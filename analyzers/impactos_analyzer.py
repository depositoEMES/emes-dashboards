import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)


class ImpactosAnalyzer:

    def __init__(self, db):
        """
        Inicializar analyzer con conexión a Firebase

        Args:
            db: Instancia de Database para Firebase
        """
        self.db = db
        self.logger = logging.getLogger(__name__)
        self._data_impactos = None
        self._vendedores_list = None
        self._moleculas_list = None
        self._last_update = None

        # Cargar datos iniciales
        self._load_initial_data()

    def _load_initial_data(self):
        """Carga inicial de datos desde Firebase"""
        try:
            self.reload_data()

        except Exception as e:
            self.logger.error(f"Error en carga inicial de impactos: {e}")
            self._data_impactos = {
                'proyectadas': {},
                'reales': {}
            }
            self._vendedores_list = ['Todos']
            self._moleculas_list = []

    def reload_data(self):
        """Recargar datos desde Firebase"""
        try:
            # Obtener datos de impactos
            impactos_data = self.db.get_by_path("impactos")

            if not impactos_data:
                raise Exception("No se encontraron datos de impactos")

            self._data_impactos = impactos_data
            self._update_lists()
            self._last_update = datetime.now()

            return True

        except Exception as e:
            self.logger.error(f"Error recargando datos de impactos: {e}")
            raise

    def _update_lists(self):
        """Actualizar listas de vendedores y moléculas"""
        try:
            vendedores_set = set()
            moleculas_set = set()

            # Extraer de proyectadas
            distribucion = self._data_impactos.get(
                'proyectadas', {}).get('distribucion', {})
            for molecula, vendedores in distribucion.items():
                moleculas_set.add(molecula)
                vendedores_set.update(vendedores.keys())

            # Extraer de reales
            reales = self._data_impactos.get('reales', {})
            for quarter_data in reales.values():
                for molecula, vendedores in quarter_data.items():
                    moleculas_set.add(molecula)
                    vendedores_set.update(vendedores.keys())

            self._vendedores_list = ['Todos'] + sorted(list(vendedores_set))
            self._moleculas_list = sorted(list(moleculas_set))

        except Exception as e:
            self.logger.error(f"Error actualizando listas: {e}")
            self._vendedores_list = ['Todos']
            self._moleculas_list = []

    @property
    def vendedores_list(self):
        """Lista de vendedores disponibles"""
        return self._vendedores_list or ['Todos']

    @property
    def moleculas_list(self):
        """Lista de moléculas disponibles"""
        return self._moleculas_list or []

    @property
    def quarter_actual(self):
        """Quarter proyectado actual"""
        return self._data_impactos.get('proyectadas', {}).get('quarter', 'N/A')

    def get_proyectadas_vendedor(self, vendedor: str = 'Todos') -> pd.DataFrame:
        """
        Obtener impactos proyectados para un vendedor

        Args:
            vendedor: Nombre del vendedor o 'Todos'

        Returns:
            DataFrame con moléculas, vendedor y cantidad proyectada
        """
        try:
            distribucion = self._data_impactos.get(
                'proyectadas', {}).get('distribucion', {})

            data = []
            for molecula, vendedores in distribucion.items():
                if vendedor == 'Todos':
                    # Agregar todos los vendedores
                    for vend, cantidad in vendedores.items():
                        data.append({
                            'molecula': molecula,
                            'vendedor': vend,
                            'cantidad_proyectada': cantidad
                        })
                else:
                    # Solo el vendedor seleccionado
                    if vendedor in vendedores:
                        data.append({
                            'molecula': molecula,
                            'vendedor': vendedor,
                            'cantidad_proyectada': vendedores[vendedor]
                        })

            return pd.DataFrame(data)

        except Exception as e:
            self.logger.error(f"Error obteniendo proyectadas: {e}")
            return pd.DataFrame()

    def get_reales_vendedor(self, vendedor: str = 'Todos', quarter: str = None) -> pd.DataFrame:
        """
        Obtener impactos reales para un vendedor en un quarter específico

        Args:
            vendedor: Nombre del vendedor o 'Todos'
            quarter: Quarter específico (ej: '2025Q1') o None para el más reciente

        Returns:
            DataFrame con moléculas, vendedor, nit y cliente
        """
        try:
            reales = self._data_impactos.get('reales', {})

            # Si no se especifica quarter, usar el más reciente
            if not quarter:
                quarters = sorted(reales.keys(), reverse=True)
                quarter = quarters[0] if quarters else None

            if not quarter or quarter not in reales:
                return pd.DataFrame()

            quarter_data = reales[quarter]

            data = []
            for molecula, vendedores in quarter_data.items():
                if vendedor == 'Todos':
                    # Agregar todos los vendedores
                    for vend, clientes in vendedores.items():
                        for nit, cliente in clientes.items():
                            data.append({
                                'molecula': molecula,
                                'vendedor': vend,
                                'nit': nit,
                                'cliente': cliente,
                                'quarter': quarter
                            })
                else:
                    # Solo el vendedor seleccionado
                    if vendedor in vendedores:
                        for nit, cliente in vendedores[vendedor].items():
                            data.append({
                                'molecula': molecula,
                                'vendedor': vendedor,
                                'nit': nit,
                                'cliente': cliente,
                                'quarter': quarter
                            })

            return pd.DataFrame(data)

        except Exception as e:
            self.logger.error(f"Error obteniendo reales: {e}")
            return pd.DataFrame()

    def get_progreso_vendedor(self, vendedor: str = 'Todos') -> Dict:
        """
        Calcular progreso actual del vendedor vs proyectado

        Args:
            vendedor: Nombre del vendedor o 'Todos'

        Returns:
            Dict con métricas de progreso
        """
        try:
            # Obtener proyectadas
            proyectadas = self.get_proyectadas_vendedor(vendedor)
            total_proyectado = proyectadas['cantidad_proyectada'].sum()

            # Obtener reales del quarter actual
            quarter_actual = self.quarter_actual
            reales = self.get_reales_vendedor(vendedor, quarter_actual)
            total_real = len(reales)  # Cada fila es un impacto

            # Calcular progreso
            porcentaje = (total_real / total_proyectado *
                          100) if total_proyectado > 0 else 0
            faltantes = max(0, total_proyectado - total_real)

            return {
                'proyectado': total_proyectado,
                'alcanzado': total_real,
                'faltante': faltantes,
                'porcentaje': porcentaje,
                'quarter': quarter_actual
            }

        except Exception as e:
            self.logger.error(f"Error calculando progreso: {e}")
            return {
                'proyectado': 0,
                'alcanzado': 0,
                'faltante': 0,
                'porcentaje': 0,
                'quarter': 'N/A'
            }

    def get_progreso_por_molecula(self, vendedor: str = 'Todos') -> pd.DataFrame:
        """
        Obtener progreso desglosado por molécula

        Args:
            vendedor: Nombre del vendedor o 'Todos'

        Returns:
            DataFrame con progreso por molécula
        """
        try:
            # Proyectadas
            proyectadas = self.get_proyectadas_vendedor(vendedor)
            proyectadas_grouped = proyectadas.groupby(
                'molecula')['cantidad_proyectada'].sum()

            # Reales
            quarter_actual = self.quarter_actual
            reales = self.get_reales_vendedor(vendedor, quarter_actual)
            reales_grouped = reales.groupby('molecula').size()

            # Combinar
            resultado = pd.DataFrame({
                'proyectado': proyectadas_grouped,
                'alcanzado': reales_grouped
            }).fillna(0)

            resultado['faltante'] = resultado['proyectado'] - \
                resultado['alcanzado']
            resultado['porcentaje'] = (
                resultado['alcanzado'] / resultado['proyectado'] * 100).fillna(0)
            resultado = resultado.reset_index()
            resultado.columns = ['molecula', 'proyectado',
                                 'alcanzado', 'faltante', 'porcentaje']

            return resultado.sort_values('porcentaje', ascending=False)

        except Exception as e:
            self.logger.error(f"Error calculando progreso por molécula: {e}")
            return pd.DataFrame()

    def get_historico_quarters(self, vendedor: str = 'Todos') -> pd.DataFrame:
        """
        Obtener histórico de impactos por quarter

        Args:
            vendedor: Nombre del vendedor o 'Todos'

        Returns:
            DataFrame con impactos por quarter
        """
        try:
            reales = self._data_impactos.get('reales', {})

            data = []
            for quarter in sorted(reales.keys()):
                df_quarter = self.get_reales_vendedor(vendedor, quarter)
                total_impactos = len(df_quarter)

                # Contar moléculas únicas
                moleculas_unicas = df_quarter['molecula'].nunique(
                ) if not df_quarter.empty else 0

                data.append({
                    'quarter': quarter,
                    'total_impactos': total_impactos,
                    'moleculas_unicas': moleculas_unicas
                })

            return pd.DataFrame(data)

        except Exception as e:
            self.logger.error(f"Error obteniendo histórico: {e}")
            return pd.DataFrame()

    def get_top_moleculas_historico(self, vendedor: str = 'Todos', top_n: int = 10) -> pd.DataFrame:
        """
        Obtener top moléculas históricas por impactos

        Args:
            vendedor: Nombre del vendedor o 'Todos'
            top_n: Número de moléculas a retornar

        Returns:
            DataFrame con top moléculas
        """
        try:
            reales = self._data_impactos.get('reales', {})

            # Combinar todos los quarters
            all_impactos = []
            for quarter in reales.keys():
                df_quarter = self.get_reales_vendedor(vendedor, quarter)
                all_impactos.append(df_quarter)

            if not all_impactos:
                return pd.DataFrame()

            df_total = pd.concat(all_impactos, ignore_index=True)

            # Contar impactos por molécula
            resultado = df_total.groupby(
                'molecula').size().reset_index(name='total_impactos')
            resultado = resultado.sort_values(
                'total_impactos', ascending=False).head(top_n)

            return resultado

        except Exception as e:
            self.logger.error(f"Error obteniendo top moléculas: {e}")
            return pd.DataFrame()

    def get_detalle_impactos_molecula(self, molecula: str, vendedor: str = 'Todos') -> pd.DataFrame:
        """
        Obtener detalle de impactos para una molécula específica

        Args:
            molecula: Código de molécula
            vendedor: Nombre del vendedor o 'Todos'

        Returns:
            DataFrame con detalle de clientes impactados
        """
        try:
            reales = self._data_impactos.get('reales', {})

            # Obtener quarter actual
            quarter_actual = self.quarter_actual

            if quarter_actual not in reales:
                return pd.DataFrame()

            df_reales = self.get_reales_vendedor(vendedor, quarter_actual)
            df_filtrado = df_reales[df_reales['molecula'] == molecula]

            return df_filtrado[['vendedor', 'nit', 'cliente']]

        except Exception as e:
            self.logger.error(f"Error obteniendo detalle de molécula: {e}")
            return pd.DataFrame()

    def get_quarters_disponibles(self) -> List[str]:
        """Obtener lista de quarters disponibles en datos reales"""
        try:
            reales = self._data_impactos.get('reales', {})
            return sorted(reales.keys(), reverse=True)
        except:
            return []

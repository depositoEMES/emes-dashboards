import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)


class VentasProveedoresAnalyzer:

    def __init__(self, db):
        """
        Inicializar analyzer con conexión a Firebase.
        """
        self.db = db
        self.logger = logging.getLogger(__name__)

        self._ventas_data = None
        self._clientes_data = None
        self._labs_data = None
        self._codigos_vendedores = None

        self._laboratorios_list = ['Todos']
        self._vendedores_list = ['Todos']
        self._meses_list = ['Todos']

        self._last_update = None
        self._load_initial_data()

    def _load_initial_data(self):
        """
        Carga inicial de datos desde Firebase.
        """
        try:
            self.reload_data()
        except Exception as e:
            self.logger.error(f"Error en carga inicial: {e}")

    def reload_data(self):
        """
        Recargar datos desde Firebase.
        """
        try:
            ventas_raw = self.db.get_by_path("ventas_proveedores")

            if not ventas_raw:
                raise Exception(
                    "No se encontraron datos de ventas_proveedores")

            clientes_raw = self.db.get_by_path("maestros/clientes_id")

            if not clientes_raw:
                raise Exception("No se encontraron datos de clientes_id")

            labs_raw = self.db.get_by_path("maestros/codigos_labs")

            if not labs_raw:
                raise Exception("No se encontraron datos de codigos_labs")

            codigos_vendedores_raw = self.db.get_by_path(
                "maestros/codigos_vendedores")

            if not codigos_vendedores_raw:
                raise Exception(
                    "No se encontraron datos de codigos_vendedores")

            self._ventas_data = ventas_raw
            self._clientes_data = clientes_raw
            self._codigos_vendedores = codigos_vendedores_raw
            self._labs_data = {k[:-3]: v for k, v in labs_raw.items()}

            self._update_lists()
            self._last_update = datetime.now()

            return True

        except Exception as e:
            self.logger.error(f"Error recargando datos: {e}")
            raise

    def _update_lists(self):
        """
        Actualizar listas de laboratorios, vendedores y meses.
        """
        try:
            vendedores_set = set()
            meses_set = set()
            labs_set = set()

            for _, cliente_info in self._clientes_data.items():
                vendedor = cliente_info.get('vendedor')

                if vendedor:
                    seller_name = \
                        self._codigos_vendedores.get(
                            str(vendedor), str(vendedor))

                    vendedores_set.add(str(seller_name))

            for fecha_str in self._ventas_data.keys():
                try:
                    if len(fecha_str) >= 6:
                        year = fecha_str[:4]
                        month = fecha_str[4:6]
                        mes_nombre = f"{year}-{month}"
                        meses_set.add(mes_nombre)
                except:
                    continue

            for lab_code, lab_name in self._labs_data.items():
                labs_set.add(f"{lab_code} - {lab_name}")

            self._laboratorios_list = \
                ['Todos'] + sorted(list(labs_set))
            self._vendedores_list = \
                ['Todos'] + sorted(list(vendedores_set))
            self._meses_list = \
                ['Todos'] + sorted(list(meses_set), reverse=True)

        except Exception as e:
            self.logger.error(f"Error actualizando listas: {e}")

            if not self._laboratorios_list or len(self._laboratorios_list) == 0:
                self._laboratorios_list = ['Todos']
            if not self._vendedores_list or len(self._vendedores_list) == 0:
                self._vendedores_list = ['Todos']
            if not self._meses_list or len(self._meses_list) == 0:
                self._meses_list = ['Todos']

    @property
    def laboratorios_list(self):
        """
        Lista de laboratorios disponibles
        """
        if not self._laboratorios_list or len(self._laboratorios_list) == 0:
            return ['Todos']

        return self._laboratorios_list

    @property
    def vendedores_list(self):
        """
        Lista de vendedores disponibles
        """
        if not self._vendedores_list or len(self._vendedores_list) == 0:
            return ['Todos']

        return self._vendedores_list

    @property
    def meses_list(self):
        """
        Lista de meses disponibles
        """
        if not self._meses_list or len(self._meses_list) == 0:
            return ['Todos']

        return self._meses_list

    def _get_lab_from_codigo(self, codigo: str) -> str:
        """
        Obtener laboratorio desde código de producto
        """
        try:
            codigo_lab = str(codigo)[:3]
            lab_name = self._labs_data.get(codigo_lab, 'Desconocido')

            return f"{codigo_lab} - {lab_name}"
        except:
            return 'Desconocido'

    def _get_cliente_info(self, cliente_id: int) -> Dict:
        """
        Obtener información de cliente
        """
        try:
            cliente_id_str = str(cliente_id)
            return self._clientes_data.get(cliente_id_str, {})
        except:
            return {}

    def get_ventas_dataframe(
            self,
            laboratorio: str = 'Todos',
            mes: str = 'Todos',
            vendedor: str = 'Todos') -> pd.DataFrame:
        """
        Obtener DataFrame procesado de ventas con filtros aplicados
        """
        try:
            if not self._ventas_data:
                return pd.DataFrame()

            data_list = []

            for fecha_str, ventas_dia in self._ventas_data.items():
                if mes != 'Todos':
                    try:
                        fecha_mes = f"{fecha_str[:4]}-{fecha_str[4:6]}"
                        if fecha_mes != mes:
                            continue
                    except:
                        continue

                if not isinstance(ventas_dia, list):
                    continue

                for venta in ventas_dia:
                    try:
                        if not isinstance(venta, list) or len(venta) < 6:
                            continue

                        codigo = str(venta[0])
                        cliente_id = int(venta[1])
                        factura = str(venta[2])  # Convertir a string
                        precio_unit = float(venta[3])
                        costo_unit = float(venta[4])
                        cantidad = int(venta[5])

                        lab = self._get_lab_from_codigo(codigo)

                        if laboratorio != 'Todos' and lab != laboratorio:
                            continue

                        cliente_info = self._get_cliente_info(cliente_id)
                        vendedor_codigo = \
                            str(
                                cliente_info.get('vendedor', 'Desconocido'))
                        vendedor_nombre = \
                            self._codigos_vendedores.get(
                                vendedor_codigo,
                                'Desconocido'
                            )

                        if vendedor != 'Todos' and vendedor_nombre != vendedor:
                            continue

                        valor_venta = precio_unit * cantidad
                        valor_costo = costo_unit * cantidad
                        utilidad = valor_venta - valor_costo
                        margen = (utilidad / valor_venta *
                                  100) if valor_venta > 0 else 0

                        data_list.append({
                            'fecha': fecha_str,
                            'mes': f"{fecha_str[:4]}-{fecha_str[4:6]}",
                            'laboratorio': lab,
                            'codigo_producto': codigo,
                            'cliente_id': str(cliente_id),
                            'cliente_nombre': cliente_info.get('nombre', 'Desconocido'),
                            'cliente_razon': cliente_info.get('razon', 'Desconocido'),
                            'vendedor': vendedor_codigo,
                            'zona': cliente_info.get('zona', 'Desconocida'),
                            'ciudad': cliente_info.get('ciudad', 'Desconocida'),
                            'factura': factura,
                            'cantidad': cantidad,
                            'precio_unitario': precio_unit,
                            'costo_unitario': costo_unit,
                            'valor_venta': valor_venta,
                            'valor_costo': valor_costo,
                            'utilidad': utilidad,
                            'margen': margen
                        })

                    except Exception as e:
                        continue

            df = pd.DataFrame(data_list)

            if not df.empty:
                df['fecha_dt'] = pd.to_datetime(
                    df['fecha'], format='%Y%m%d', errors='coerce')

            return df

        except Exception as e:
            self.logger.error(f"Error creando DataFrame: {e}")
            return pd.DataFrame()

    def get_resumen_general(
            self,
            laboratorio: str = 'Todos',
            mes: str = 'Todos',
            vendedor: str = 'Todos') -> Dict:
        """
        Obtener resumen general de ventas
        """
        try:
            df = self.get_ventas_dataframe(laboratorio, mes, vendedor)

            if df.empty:
                return {
                    'total_ventas': 0,
                    'total_unidades': 0,
                    'total_utilidad': 0,
                    'margen_promedio': 0,
                    'num_facturas': 0,
                    'num_clientes': 0,
                    'num_productos': 0,
                    'num_laboratorios': 0
                }

            return {
                'total_ventas': float(df['valor_venta'].sum()),
                'total_unidades': int(df['cantidad'].sum()),
                'total_utilidad': float(df['utilidad'].sum()),
                'margen_promedio': float((df['utilidad'].sum() / df['valor_venta'].sum() * 100) if df['valor_venta'].sum() > 0 else 0),
                'num_facturas': int(df['factura'].nunique()),
                'num_clientes': int(df['cliente_id'].nunique()),
                'num_productos': int(df['codigo_producto'].nunique()),
                'num_laboratorios': int(df['laboratorio'].nunique())
            }

        except Exception as e:
            self.logger.error(f"Error calculando resumen: {e}")
            return {
                'total_ventas': 0,
                'total_unidades': 0,
                'total_utilidad': 0,
                'margen_promedio': 0,
                'num_facturas': 0,
                'num_clientes': 0,
                'num_productos': 0,
                'num_laboratorios': 0
            }

    def get_ventas_por_laboratorio(
            self,
            mes: str = 'Todos',
            vendedor: str = 'Todos',
            top_n: int = None) -> pd.DataFrame:
        """
        Obtener ventas agrupadas por laboratorio
        """
        try:
            df = self.get_ventas_dataframe('Todos', mes, vendedor)

            if df.empty:
                return pd.DataFrame()

            resultado = df.groupby('laboratorio').agg({
                'valor_venta': 'sum',
                'cantidad': 'sum',
                'cliente_id': 'nunique',
                'factura': 'nunique',
                'utilidad': 'sum'
            }).reset_index()

            resultado.columns = ['laboratorio', 'valor_ventas', 'unidades',
                                 'num_clientes', 'num_facturas', 'utilidad']

            resultado['margen'] = (
                resultado['utilidad'] / resultado['valor_ventas'] * 100).fillna(0)
            resultado = resultado.sort_values('valor_ventas', ascending=False)
            resultado = resultado[resultado['laboratorio'] != 'Desconocido']

            if top_n:
                resultado = resultado.head(top_n)

            return resultado

        except Exception as e:
            self.logger.error(f"Error calculando ventas por laboratorio: {e}")
            return pd.DataFrame()

    def get_evolucion_mensual(
            self,
            laboratorio: str = 'Todos',
            vendedor: str = 'Todos') -> pd.DataFrame:
        """
        Obtener evolución mensual de ventas
        """
        try:
            df = self.get_ventas_dataframe(laboratorio, 'Todos', vendedor)

            if df.empty:
                return pd.DataFrame()

            resultado = df.groupby('mes').agg({
                'valor_venta': 'sum',
                'cantidad': 'sum',
                'cliente_id': 'nunique',
                'utilidad': 'sum'
            }).reset_index()

            resultado.columns = ['mes', 'valor_ventas',
                                 'unidades', 'num_clientes', 'utilidad']
            resultado = resultado.sort_values('mes')

            return resultado

        except Exception as e:
            self.logger.error(f"Error calculando evolución mensual: {e}")

            return \
                pd.DataFrame()

    def get_evolucion_impactos_mensual(
            self,
            laboratorio: str = 'Todos',
            vendedor: str = 'Todos') -> pd.DataFrame:
        """
        Obtener evolución mensual de impactos (clientes únicos)
        """
        try:
            df = self.get_ventas_dataframe(laboratorio, 'Todos', vendedor)

            if df.empty:
                return pd.DataFrame()

            resultado = df.groupby('mes').agg({
                'cliente_id': 'nunique'
            }).reset_index()

            resultado.columns = ['mes', 'impactos']
            resultado = resultado.sort_values('mes')

            return resultado

        except Exception as e:
            self.logger.error(f"Error calculando evolución de impactos: {e}")

            return \
                pd.DataFrame()

    def get_top_clientes(
            self,
            laboratorio: str = 'Todos',
            mes: str = 'Todos',
            vendedor: str = 'Todos',
            top_n: int = 10) -> pd.DataFrame:
        """
        Obtener top clientes por ventas
        """
        try:
            df = self.get_ventas_dataframe(laboratorio, mes, vendedor)

            if df.empty:
                return pd.DataFrame()

            resultado = df.groupby(['cliente_id', 'cliente_razon', 'zona']).agg({
                'valor_venta': 'sum',
                'cantidad': 'sum',
                'factura': 'nunique'
            }).reset_index()

            resultado.columns = ['cliente_id', 'cliente', 'zona',
                                 'valor_ventas', 'unidades', 'num_facturas']

            resultado = resultado.sort_values(
                'valor_ventas', ascending=False).head(top_n)

            return resultado

        except Exception as e:
            self.logger.error(f"Error calculando top clientes: {e}")

            return \
                pd.DataFrame()

    def get_ventas_por_molecula(
            self,
            laboratorio: str = 'Todos',
            mes: str = 'Todos',
            vendedor: str = 'Todos',
            periodo: str = 'mensual') -> pd.DataFrame:
        """
        Obtener ventas, unidades e impactos por molécula/producto
        periodo: 'mensual', 'trimestral' o 'anual'
        """
        try:
            df = self.get_ventas_dataframe(laboratorio, mes, vendedor)

            if df.empty:
                return pd.DataFrame()

            if periodo == 'trimestral':
                df['periodo'] = df['fecha_dt'].dt.to_period('Q').astype(str)
            elif periodo == 'anual':
                df['periodo'] = df['fecha_dt'].dt.year.astype(str)
            else:
                df['periodo'] = df['mes']

            resultado = df.groupby(['codigo_producto', 'periodo', 'laboratorio']).agg({
                'valor_venta': 'sum',
                'cantidad': 'sum',
                'cliente_id': 'nunique'
            }).reset_index()

            resultado.columns = [
                'molecula', 'periodo', 'laboratorio', 'valor_ventas', 'unidades', 'impactos']
            resultado = resultado.sort_values(
                ['periodo', 'valor_ventas'], ascending=[True, False])

            return resultado

        except Exception as e:
            self.logger.error(f"Error calculando ventas por molécula: {e}")
            return pd.DataFrame()

    def get_comparativo_laboratorios(
            self,
            mes: str = 'Todos',
            vendedor: str = 'Todos') -> pd.DataFrame:
        """
        Obtener comparativo de valor, unidades e impactos por laboratorio
        """
        try:
            df = \
                self.get_ventas_dataframe('Todos', mes, vendedor)

            if df.empty:
                return pd.DataFrame()

            resultado = df.groupby('laboratorio').agg({
                'valor_venta': 'sum',
                'cantidad': 'sum',
                'cliente_id': 'nunique',
                'utilidad': 'sum',
                'margen': 'mean'
            }).reset_index()

            resultado.columns = \
                [
                    'laboratorio',
                    'valor_ventas',
                    'unidades',
                    'impactos',
                    'utilidad',
                    'margen'
                ]

            resultado = resultado[resultado['laboratorio'] != 'Desconocido']
            resultado = resultado.sort_values('valor_ventas', ascending=False)

            return resultado

        except Exception as e:
            self.logger.error(f"Error calculando comparativo: {e}")
            return pd.DataFrame()

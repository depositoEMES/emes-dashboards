import time
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any


class UnifiedVentasAnalyzer:

    def __init__(self):
        """
        Initialize the UnifiedVentasAnalyzer with empty dataframes.
        """
        self.df_ventas_totales = pd.DataFrame()
        self.df_ventas = pd.DataFrame()
        self.df_transferencias = pd.DataFrame()

        # Listas de filtros
        self.vendedores_list = ['Todos']
        self.transferencistas_list = ['Todos']
        self.meses_list = ['Todos']

        # Cache para datos complementarios
        self._df_convenios = pd.DataFrame()
        self._df_cuotas = pd.DataFrame()
        self._df_recibos = pd.DataFrame()
        self._df_num_clientes = pd.DataFrame()
        self._df_clientes = pd.DataFrame()

        # Cache para datos maestros
        self._maestro_tipos = {}
        self._maestros_forma_pago = {}
        self._maestro_vendedores = {}
        self._clientes_id_cache = {}

        # Control de actualizaciones
        self._last_update = None
        self._last_convenios_update = None
        self._last_recibos_update = None
        self._last_num_clientes_update = None
        self._last_clientes_update = None
        self._last_maestros_update = None

    def reload_data(self):
        """
        Force reload of ALL data from Firebase.
        """
        try:
            # Clean cache
            self.df_ventas_totales = pd.DataFrame()
            self.df_ventas = pd.DataFrame()
            self.df_transferencias = pd.DataFrame()
            self._df_convenios = pd.DataFrame()
            self._df_recibos = pd.DataFrame()
            self._df_num_clientes = pd.DataFrame()
            self._df_clientes = pd.DataFrame()
            self._df_cuotas = pd.DataFrame()

            # Limpiar cache de maestros
            self._maestro_tipos = {}
            self._maestros_forma_pago = {}
            self._maestro_vendedores = {}
            self._clientes_id_cache = {}

            self.vendedores_list = ['Todos']
            self.transferencistas_list = ['Todos']
            self.meses_list = ['Todos']

            # Reload main data
            start_time = time.time()
            result = self.load_data_from_firebase(force_reload=True)
            load_time = time.time() - start_time

            # Mark update
            self._last_update = datetime.now()
            self._last_convenios_update = None
            self._last_recibos_update = None
            self._last_num_clientes_update = None
            self._last_clientes_update = None
            self._last_maestros_update = None

            return result

        except Exception as e:
            print(f"❌ [UnifiedVentasAnalyzer] Error recargando datos: {e}")
            return pd.DataFrame()

    def _get_db(self):
        """
        Get database instance with retry logic.
        """
        from server import get_db

        max_retries = 3

        for attempt in range(max_retries):
            try:
                db = get_db()
                if db:
                    return db
            except Exception as e:
                print(
                    f"⚠️ Intento {attempt + 1}/{max_retries}: Error conectando a DB: {e}")

            # Wait until next attempt
            if attempt < max_retries - 1:
                time.sleep(1)

        print(
            "❌ No se pudo establecer conexión a la base de datos después de varios intentos")
        return None

    def load_maestros_data(self, force_reload: bool = False) -> bool:
        """
        Cargar datos maestros de tipos de documento y códigos de vendedores.
        """
        try:
            # Si ya tenemos datos y no es recarga forzada, usar cache
            if not force_reload and \
                self._maestro_tipos and \
                    self._maestro_vendedores and \
                    self._maestros_forma_pago:
                return True

            db = self._get_db()

            if not db:
                print(
                    "❌ [UnifiedVentasAnalyzer] No se pudo obtener conexión para maestros")
                return False

            # Cargar tipo_documentos
            tipos_data = db.get_by_path("maestros/tipo_documentos")

            if tipos_data:
                self._maestro_tipos = tipos_data
            else:
                print("⚠️ No se encontraron datos en maestros/tipo_documentos")

            # Cargar codigos_vendedores
            vendedores_data = db.get_by_path("maestros/codigos_vendedores")

            if vendedores_data:
                self._maestro_vendedores = vendedores_data
            else:
                print("⚠️ No se encontraron datos en maestros/codigos_vendedores")

            # Cargar forma_pago
            forma_pago_data = db.get_by_path("maestros/forma_pago_clientes")

            if forma_pago_data:
                self._maestros_forma_pago = forma_pago_data
            else:
                print("⚠️ No se encontraron datos en maestros/forma_pago_clientes")

            self._last_maestros_update = datetime.now()

            return True

        except Exception as e:
            print(f"❌ Error cargando datos maestros: {e}")
            return False

    def __get_forma_pago_by_id(self, forma_pago_code: str) -> str:
        """
        Get "forma pago" based on id.

        Args:
            forma_pago_code (str): Client's ID.

        Returns:
            str: Forma pago.
        """
        return \
            self._maestros_forma_pago.get(
                forma_pago_code,
                forma_pago_code
            )

    def process_clientes_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Process clientes_id data.
        """
        if not data:
            return pd.DataFrame()

        clientes_list = []

        for cliente_id, cliente_info in data.items():
            cliente_row = {
                'id1': cliente_id,
                'lat': float(cliente_info.get('lat', 0) or 0),
                'long': float(cliente_info.get('long', 0) or 0),
                'cliente_nombre': cliente_info.get('cliente_nombre', ''),
                'ciudad': cliente_info.get('ciudad', ''),
                'departamento': cliente_info.get('departamento', ''),
                'direccion': cliente_info.get('direccion', ''),
                'estado': cliente_info.get('estado', 'Anulado'),
                'nit': cliente_info.get('nit', ''),
                'zona': cliente_info.get('zona', ''),
                'subzona': cliente_info.get('subzona', ''),
                'forma_pago': self.__get_forma_pago_by_id(cliente_info.get('forma_pago', '')),
                'cupo_credito': float(cliente_info.get('cupo_credito', 0) or 0)
            }
            clientes_list.append(cliente_row)

        return pd.DataFrame(clientes_list) if clientes_list else pd.DataFrame()

    def load_data_from_firebase(self, force_reload: bool = False) -> pd.DataFrame:
        """
        Load sales data from fac_ventas instead of ventas_totales.
        """
        try:
            # Si ya tenemos datos y no es recarga forzada, usar cache
            if not force_reload and not self.df_ventas_totales.empty:
                return self.df_ventas_totales

            db = self._get_db()

            if not db:
                print(
                    "❌ [UnifiedVentasAnalyzer] No se pudo obtener conexión a la base de datos")
                return pd.DataFrame()

            if not self.load_maestros_data(force_reload):
                print("⚠️ Continuando sin algunos datos maestros")

            # Load clientes_id data into cache
            self.load_clientes_data_from_firebase(force_reload)

            # Get invoices data
            data = db.get("fac_ventas")

            if data:
                result = self.process_unified_data(data)
                return result
            else:
                print(
                    "⚠️ [UnifiedVentasAnalyzer] No data found in Firebase - fac_ventas")
                return pd.DataFrame()

        except Exception as e:
            print(
                f"❌ [UnifiedVentasAnalyzer] Error loading sales data from Firebase: {e}")
            return pd.DataFrame()

    def load_clientes_data_from_firebase(self, force_reload: bool = False) -> pd.DataFrame:
        """
        Load clientes_id data from Firebase database with caching.
        """
        try:
            # Usar cache si está disponible y no es recarga forzada
            if not force_reload and hasattr(self, '_df_clientes') and \
                    not self._df_clientes.empty and self._clientes_id_cache:
                return self._df_clientes

            db = self._get_db()

            if not db:
                print(
                    "❌ [VentasAnalyzer] No se pudo obtener conexión para clientes")
                return pd.DataFrame()

            data = db.get_by_path("maestros/clientes_id")

            if data:
                self._clientes_id_cache = {}

                for cliente_id, cliente_info in data.items():
                    id1 = cliente_info.get('id1', cliente_id)
                    self._clientes_id_cache[id1] = cliente_info

                # Procesar para DataFrame también
                result = self.process_clientes_data(data)

                # Guardar en cache
                self._df_clientes = result
                self._last_clientes_update = datetime.now()

                return result
            else:
                print("⚠️ [VentasAnalyzer] No clientes_id data found in Firebase")
                self._df_clientes = pd.DataFrame()
                self._clientes_id_cache = {}
                return pd.DataFrame()

        except Exception as e:
            print(
                f"❌ [VentasAnalyzer] Error loading clientes_id data from Firebase: {e}")
            self._df_clientes = pd.DataFrame()
            self._clientes_id_cache = {}
            return pd.DataFrame()

    def get_dias_sin_venta_por_cliente(
            self,
            mode: str,
            vendedor: str = 'Todos'):
        """
        Get days without transfers for each client.
        Solo incluye clientes con estado diferente a 'Anulado'.
        """
        if mode == "vendedor":
            df = \
                self.filter_ventas_data(
                    vendedor=vendedor,
                    mes='Todos'
                )
        else:
            df = \
                self.filter_transferencias_data(
                    transferencista=vendedor,
                    mes='Todos'
                )

        ventas_reales = df[df['tipo'].str.contains(
            'Remision', case=False, na=False)]

        if ventas_reales.empty:
            return pd.DataFrame()

        # Obtener datos de clientes para filtrar por estado
        df_clientes = self._df_clientes

        if df_clientes.empty:
            df_clientes = self.load_clientes_data_from_firebase()

        # Si aún no hay datos de clientes, proceder sin filtro
        if df_clientes.empty:
            print(
                "⚠️ No se pudieron cargar datos de clientes, procesando sin filtro de estado")
            clientes_activos = ventas_reales['id1'].unique()
        else:
            # Filtrar clientes que NO estén anulados
            clientes_no_anulados = df_clientes[
                (df_clientes['estado'] != 'Anulado') &
                (df_clientes['estado'].notna())
            ]

            if clientes_no_anulados.empty:
                print("⚠️ No se encontraron clientes con estado válido")
                return pd.DataFrame()

            # Obtener lista de IDs de clientes activos
            clientes_activos = clientes_no_anulados['id1'].unique()

        # FILTRAR ventas solo de clientes activos (no anulados)
        ventas_reales_filtradas = ventas_reales[
            ventas_reales['id1'].isin(clientes_activos)
        ]

        if ventas_reales_filtradas.empty:
            print("⚠️ No se encontraron ventas para clientes activos")
            return pd.DataFrame()

        # Get last sale date for each client (solo clientes activos)
        ultima_venta = ventas_reales_filtradas.groupby('cliente_completo').agg({
            'fecha': 'max',
            'valor_neto': 'sum',
            'documento_id': 'count',
            'id1': 'first'  # Agregar id1 para referencia
        }).reset_index()

        # Remove rows with invalid dates
        ultima_venta = ultima_venta.dropna(subset=['fecha'])

        if ultima_venta.empty:
            return pd.DataFrame()

        # Calculate days without sales
        today = datetime.now()
        ultima_venta['dias_sin_venta'] = (
            today - ultima_venta['fecha']).dt.days

        # Filter out recent sales (less than 7 days) to focus on inactive clients
        resultado = ultima_venta[ultima_venta['dias_sin_venta'] >= 7].copy()

        if resultado.empty:
            return pd.DataFrame()

        # Add categories for better visualization
        def categorize_days(days):
            if days < 30:
                return "1-29 días"
            elif days < 60:
                return "30-59 días"
            elif days < 90:
                return "60-89 días"
            elif days < 180:
                return "90-179 días"
            else:
                return "180+ días"

        resultado['categoria'] = resultado['dias_sin_venta'].apply(
            categorize_days)

        # Sort by days without sales descending
        return resultado.sort_values('dias_sin_venta', ascending=False)

    def process_unified_data(self, data):
        """
        Process raw unified sales data from fac_ventas and enrich with master data.
        """
        if not data:
            return pd.DataFrame()

        ventas_list = []

        # Procesar cada documento (donde key = número de factura/nota)
        for doc_id, doc_info in data.items():
            # Obtener el id1 para buscar datos del cliente
            id1 = doc_info.get('id1', '')
            cliente_data = self._clientes_id_cache.get(id1, {})

            # Decodificar tipo de documento
            tipo_codigo = doc_info.get('tipo', '')
            tipo_nombre = self._maestro_tipos.get(tipo_codigo, "N/A")

            # Decodificar vendedor
            vendedor_codigo = doc_info.get('vendedor', '')
            vendedor_nombre = self._maestro_vendedores.get(
                vendedor_codigo, "N/A")

            # Decodificar transferencista
            transf_codigo = doc_info.get('transferencista', '')
            transf_nombre = self._maestro_vendedores.get(transf_codigo, "N/A")

            doc_row = \
                {
                    'documento_id': doc_id,
                    'vendedor': vendedor_nombre,
                    'transferencista': transf_nombre,
                    'cliente': cliente_data.get('nombre', ''),
                    'url': cliente_data.get('razon', ''),
                    'nit': cliente_data.get('nit', ''),
                    'fecha': doc_info.get('fecha', ''),
                    'tipo': tipo_nombre,
                    'valor_bruto': float(doc_info.get('valor_bruto', 0) or 0),
                    'descuento': float(doc_info.get('descuento', 0) or 0),
                    'iva': float(doc_info.get('iva', 0) or 0),
                    'forma_pago': cliente_data.get('forma_pago', 'No Definida'),
                    'zona': cliente_data.get('zona', ''),
                    'subzona': cliente_data.get('subzona', ''),
                    'cupo_credito': float(cliente_data.get('cupo_credito', 0) or 0),
                    'id1': id1
                }

            ventas_list.append(doc_row)

        if not ventas_list:
            return pd.DataFrame()

        # Crear DataFrame principal
        self.df_ventas_totales = pd.DataFrame(ventas_list)

        # Procesar fechas y campos comunes
        self._process_common_fields(self.df_ventas_totales)

        # Separar en dos DataFrames específicos
        self._separate_data()

        return self.df_ventas_totales

    def _process_common_fields(self, df):
        """
        Process common fields like dates and calculations.
        """
        # Process dates
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')

        # Extract month-year for filtering
        df['año_mes'] = df['fecha'].dt.to_period('M')
        df['mes_nombre'] = df['fecha'].dt.strftime('%Y-%m')

        # Calculate net value (valor_bruto - descuento)
        df['valor_neto'] = df['valor_bruto'] - df['descuento']

        # Create combined client name
        df['cliente_completo'] = df.apply(
            lambda row: f"{row['cliente']} – {row['url']}" if row['url'] and row['url'].strip(
            ) else row['cliente'],
            axis=1
        )

        # Create months list (común para ambos)
        meses_unicos = df['mes_nombre'].dropna().unique()
        self.meses_list = ['Todos'] + sorted(meses_unicos, reverse=True)

    def _separate_data(self):
        """
        Separate unified data into vendor and transfer agent specific DataFrames.
        """
        # DataFrame para ventas (por vendedor)
        # Filtrar registros donde vendedor no está vacío
        ventas_mask = (
            self.df_ventas_totales['vendedor'].notna() &
            (self.df_ventas_totales['vendedor'] != '') &
            (self.df_ventas_totales['vendedor'] != 'null') &
            (~self.df_ventas_totales['vendedor'].str.contains(
                'Vendedor \\d+', na=False))  # Excluir no decodificados
        )
        self.df_ventas = self.df_ventas_totales[ventas_mask].copy()

        # Filtrar registros donde transferencista no está vacío
        transferencias_mask = (
            self.df_ventas_totales['transferencista'].notna() &
            (self.df_ventas_totales['transferencista'] != '') &
            (self.df_ventas_totales['transferencista'] != 'null') &
            (~self.df_ventas_totales['transferencista'].str.contains(
                'Transferencista \\d+', na=False))  # Excluir no decodificados
        )

        self.df_transferencias = \
            self.df_ventas_totales[transferencias_mask].copy()

        # Create vendedores list
        if not self.df_ventas.empty:
            vendedores_unicos = self.df_ventas['vendedor'].dropna().unique()
            self.vendedores_list = ['Todos'] + sorted(vendedores_unicos)

        # Create transferencistas list
        if not self.df_transferencias.empty:
            transferencistas_unicos = self.df_transferencias['transferencista'].dropna(
            ).unique()
            self.transferencistas_list = [
                'Todos'] + sorted(transferencistas_unicos)

    def filter_ventas_data(self, vendedor='Todos', mes='Todos'):
        """
        Filter ventas data by salesperson and month.
        """
        df = self.df_ventas.copy()

        if vendedor != 'Todos':
            df = df[df['vendedor'] == vendedor]

        if mes != 'Todos':
            df = df[df['mes_nombre'] == mes]

        return df

    def get_resumen_ventas(self, vendedor='Todos', mes='Todos'):
        """Get sales summary statistics."""
        df = self.filter_ventas_data(vendedor, mes)

        # Filter only sales (exclude credit notes, returns, etc.)
        ventas_reales = df[df['tipo'].str.contains(
            'Remision', case=False, na=False)]
        devoluciones = df[df['tipo'].str.contains(
            'Devolución|Devolucion', case=False, na=False)]
        notas_credito = df[df['tipo'].str.contains(
            'Nota.*crédito|Nota.*credito', case=False, na=False)]

        total_ventas = ventas_reales['valor_neto'].sum()
        total_devoluciones = abs(devoluciones['valor_neto'].sum())
        total_notas_credito = abs(notas_credito['valor_neto'].sum())
        ventas_netas = total_ventas - total_devoluciones

        return {
            'total_ventas': total_ventas,
            'total_devoluciones': total_devoluciones,
            'total_notas_credito': total_notas_credito,
            'ventas_netas': ventas_netas,
            'num_facturas': len(ventas_reales),
            'num_clientes': ventas_reales['cliente_completo'].nunique() if not ventas_reales.empty else 0,
            'num_devoluciones': len(devoluciones),
            'ticket_promedio': total_ventas / len(ventas_reales) if len(ventas_reales) > 0 else 0,
            'total_descuentos': abs(ventas_reales['descuento'].sum()),
            'porcentaje_descuento': (abs(ventas_reales['descuento'].sum()) / ventas_reales['valor_bruto'].sum() * 100) if ventas_reales['valor_bruto'].sum() > 0 else 0
        }

    def get_ventas_por_mes(self, vendedor='Todos'):
        """
        Get sales evolution by month with net sales (sales minus returns).
        """
        df = self.filter_ventas_data(vendedor, 'Todos')

        # Separar ventas reales y devoluciones
        ventas_reales = df[df['tipo'].str.contains(
            'Remision', case=False, na=False)]
        devoluciones = df[df['tipo'].str.contains(
            'Devolución|Devolucion', case=False, na=False)]

        if ventas_reales.empty and devoluciones.empty:
            return pd.DataFrame()

        # Agrupar ventas por mes
        resultado_ventas = ventas_reales.groupby('mes_nombre').agg({
            'valor_neto': 'sum',
            'documento_id': 'count'
        }).reset_index() if not ventas_reales.empty else pd.DataFrame()

        # Agrupar devoluciones por mes
        resultado_devoluciones = devoluciones.groupby('mes_nombre').agg({
            'valor_neto': 'sum'
        }).reset_index() if not devoluciones.empty else pd.DataFrame()

        # Si solo hay ventas
        if resultado_devoluciones.empty:
            return resultado_ventas.sort_values('mes_nombre')

        # Si solo hay devoluciones
        if resultado_ventas.empty:
            resultado_devoluciones['documento_id'] = 0
            resultado_devoluciones['valor_neto'] = - \
                abs(resultado_devoluciones['valor_neto'])
            return resultado_devoluciones.sort_values('mes_nombre')

        # Combinar ventas y devoluciones
        resultado = resultado_ventas.merge(
            resultado_devoluciones,
            on='mes_nombre',
            how='outer',
            suffixes=('', '_dev')
        ).fillna(0)

        # Calcular ventas netas (ventas - devoluciones)
        resultado['valor_neto'] = resultado['valor_neto'] - \
            abs(resultado['valor_neto_dev'])

        # Limpiar columnas
        resultado = resultado[['mes_nombre', 'valor_neto', 'documento_id']]

        return resultado.sort_values('mes_nombre')

    def filter_transferencias_data(self, transferencista='Todos', mes='Todos'):
        """Filter transferencias data by transfer agent and month."""
        df = self.df_transferencias.copy()

        if transferencista != 'Todos':
            df = df[df['transferencista'] == transferencista]

        if mes != 'Todos':
            df = df[df['mes_nombre'] == mes]

        return df

    def get_resumen_transferencias(
            self,
            transferencista: str = 'Todos',
            mes: str = 'Todos') -> Dict[str, Any]:
        """
        Get transfer summary statistics.
        """
        df = self.filter_transferencias_data(transferencista, mes)

        # Filter only sales (exclude credit notes, returns, etc.)
        ventas_reales = df[df['tipo'].str.contains(
            'Remision', case=False, na=False)]
        devoluciones = df[df['tipo'].str.contains(
            'Devolución|Devolucion', case=False, na=False)]
        notas_credito = df[df['tipo'].str.contains(
            'Nota.*crédito|Nota.*credito', case=False, na=False)]

        total_transferencias = ventas_reales['valor_neto'].sum()
        total_devoluciones = abs(devoluciones['valor_neto'].sum())
        total_notas_credito = abs(notas_credito['valor_neto'].sum())
        transferencias_netas = total_transferencias - total_devoluciones

        return {
            'total_transferencias': total_transferencias,
            'total_devoluciones': total_devoluciones,
            'total_notas_credito': total_notas_credito,
            'transferencias_netas': transferencias_netas,
            'num_facturas': len(ventas_reales),
            'num_clientes': ventas_reales['cliente'].nunique() if not ventas_reales.empty else 0,
            'num_devoluciones': len(devoluciones),
            'ticket_promedio': total_transferencias / len(ventas_reales) if len(ventas_reales) > 0 else 0,
            'total_descuentos': abs(ventas_reales['descuento'].sum()),
            'porcentaje_descuento': (abs(ventas_reales['descuento'].sum()) / ventas_reales['valor_bruto'].sum() * 100) if ventas_reales['valor_bruto'].sum() > 0 else 0
        }

    def get_transferencias_por_mes(self, transferencista: str = 'Todos') -> pd.DataFrame:
        """
        Get transfers evolution by month.
        """
        df = self.filter_transferencias_data(transferencista, 'Todos')

        ventas_reales = df[df['tipo'].str.contains(
            'Remision', case=False, na=False)]

        if ventas_reales.empty:
            return pd.DataFrame()

        resultado = ventas_reales.groupby('mes_nombre').agg({
            'valor_neto': 'sum',
            'documento_id': 'count'
        }).reset_index()

        return resultado.sort_values('mes_nombre')

    def get_ventas_por_dia_semana(self, person='Todos', mes='Todos', person_type='vendedor'):
        """
        Get sales distribution by day of week.

        Args:
            person: Name of person (vendedor or transferencista)
            mes: Month filter
            person_type: 'vendedor' or 'transferencista'
        """
        if person_type == 'vendedor':
            df = self.filter_ventas_data(person, mes)
        else:
            df = self.filter_transferencias_data(person, mes)

        ventas_reales = df[df['tipo'].str.contains(
            'Remision', case=False, na=False)]

        if ventas_reales.empty:
            return pd.DataFrame()

        # Add day of week
        ventas_reales = ventas_reales.copy()
        ventas_reales['dia_semana'] = ventas_reales['fecha'].dt.day_name()

        # Define order for days of week in Spanish
        dias_orden = ['Monday', 'Tuesday', 'Wednesday',
                      'Thursday', 'Friday', 'Saturday', 'Sunday']
        dias_espanol = ['Lunes', 'Martes', 'Miércoles',
                        'Jueves', 'Viernes', 'Sábado', 'Domingo']

        # Map English to Spanish
        dia_map = dict(zip(dias_orden, dias_espanol))
        ventas_reales['dia_semana_es'] = ventas_reales['dia_semana'].map(
            dia_map)

        resultado = ventas_reales.groupby('dia_semana_es').agg({
            'valor_neto': 'sum',
            'documento_id': 'count'
        }).reset_index()

        # Reorder by day of week
        resultado['dia_semana_es'] = pd.Categorical(
            resultado['dia_semana_es'],
            categories=dias_espanol,
            ordered=True
        )
        return resultado.sort_values('dia_semana_es')

    def load_convenios_from_firebase(self, force_reload: bool = False) -> pd.DataFrame:
        """
        Load convenios data from Firebase database with caching.
        """
        try:
            if not force_reload and not self._df_convenios.empty:
                return self._df_convenios

            db = self._get_db()

            if not db:
                print(
                    "❌ [UnifiedVentasAnalyzer] No se pudo obtener conexión para convenios")
                return pd.DataFrame()

            data = db.get("convenios")

            if data:
                result = self.process_convenios_data(data)
                self._df_convenios = result
                self._last_convenios_update = datetime.now()

                return result
            else:
                print(
                    "⚠️ [UnifiedVentasAnalyzer] No convenios data found in Firebase")
                self._df_convenios = pd.DataFrame()
                return pd.DataFrame()

        except Exception as e:
            print(
                f"❌ [UnifiedVentasAnalyzer] Error loading convenios data from Firebase: {e}")
            self._df_convenios = pd.DataFrame()
            return pd.DataFrame()

    def process_convenios_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Process convenios data with correct field names.
        """
        if not data:
            return pd.DataFrame()

        convenios_list = []

        for nit, convenio_info in data.items():
            convenio_row = {
                'nit': nit,
                'client_name': convenio_info.get('client_name', ''),
                'razon': convenio_info.get('razon', ''),
                'seller_name': convenio_info.get('seller_name', ''),
                'estado': convenio_info.get('estado', ''),
                'rebate_pct': float(convenio_info.get('rebate_pct', 0) or 0) * 100,
                'target_value': float(convenio_info.get('target_value', 0) or 0),
                'observations': convenio_info.get('observations', '')
            }
            convenios_list.append(convenio_row)

        df_convenios = pd.DataFrame(
            convenios_list) if convenios_list else pd.DataFrame()

        # Filter only confirmed agreements
        if not df_convenios.empty:
            df_convenios = df_convenios[df_convenios['estado'] == 'Confirmado']

        return df_convenios

    def clear_all_cache(self) -> None:
        """
        Clean cache to force reload.
        """
        self.df_ventas_totales = pd.DataFrame()
        self.df_ventas = pd.DataFrame()
        self.df_transferencias = pd.DataFrame()
        self._df_convenios = pd.DataFrame()
        self._df_cuotas = pd.DataFrame()
        self._df_recibos = pd.DataFrame()
        self._df_num_clientes = pd.DataFrame()
        self._df_clientes = pd.DataFrame()

        self.vendedores_list = ['Todos']
        self.transferencistas_list = ['Todos']
        self.meses_list = ['Todos']

        self._last_update = None
        self._last_convenios_update = None
        self._last_recibos_update = None
        self._last_num_clientes_update = None
        self._last_clientes_update = None

    def get_cache_status(self) -> Dict[str, Any]:
        """
        Get current cache status for debugging including new caches.
        """
        return \
            {
                'ventas_totales': {
                    'records': len(self.df_ventas_totales),
                    'last_update': self._last_update.isoformat() if self._last_update else None
                },
                'ventas': {
                    'records': len(self.df_ventas),
                    'vendedores': len(self.vendedores_list) - 1
                },
                'transferencias': {
                    'records': len(self.df_transferencias),
                    'transferencistas': len(self.transferencistas_list) - 1
                },
                'convenios': {
                    'records': len(self._df_convenios),
                    'last_update': self._last_convenios_update.isoformat() if self._last_convenios_update else None
                },
                'maestros': {
                    'tipos_documentos': len(self._maestro_tipos),
                    'codigos_vendedores': len(self._maestro_vendedores),
                    'clientes_cache': len(self._clientes_id_cache),
                    'last_update': self._last_maestros_update.isoformat() if self._last_maestros_update else None
                }
            }

    def get_seller_name(self, id1: str) -> str:
        """
        Get seller name based on id.

        Args:
            id1 (str): Client's ID.

        Returns:
            str: Seller name.
        """
        vendedor_code = \
            self._clientes_id_cache.get(id1, {}).get("vendedor")

        vendedor = \
            self._maestro_vendedores.get(vendedor_code, "")

        return vendedor

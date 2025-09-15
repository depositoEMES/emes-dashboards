import time
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
from collections import Counter

import pandas as pd
from pandas.core.frame import DataFrame

from utils import (
    format_currency_int,
    calcular_dias_habiles_colombia
)


class VentasAnalyzer:

    def __init__(self) -> None:
        """
        Constructor.
        """
        from . import get_unified_analyzer
        self._unified_analyzer = get_unified_analyzer()

        # Cache manager for RFM+ model
        self._rfm_cache = {}
        self._rfm_cache_timestamp = None
        self._rfm_cache_ttl = 300

    @property
    def df_ventas(self) -> DataFrame:
        """
        Compatibility: returns the DataFrame of sales by salesperson.
        """
        return self._unified_analyzer.df_ventas

    @property
    def vendedores_list(self) -> List[str]:
        """
        Compatibility: returns the list of vendors.
        """
        return self._unified_analyzer.vendedores_list

    @property
    def meses_list(self):
        """
        Compatibility: Returns the list of months.
        """
        return self._unified_analyzer.meses_list

    def reload_data(self):
        """
        Force reload of ALL data from Firebase.
        """
        return self._unified_analyzer.reload_data()

    def load_data_from_firebase(self, force_reload=False):
        """
        Load sales data from Firebase database with caching and retry logic.
        """
        return self._unified_analyzer.load_data_from_firebase(force_reload)

    def clear_all_cache(self):
        """
        Clean cache to force reload.
        """
        return self._unified_analyzer.clear_all_cache()

    def get_cache_status(self):
        """
        Get current cache status for debugging.
        """
        status = self._unified_analyzer.get_cache_status()

        return \
            {
                'ventas': status['ventas'],
                'convenios': status['convenios'],
                'recibos': status.get('recibos', {'records': 0, 'last_update': None}),
                'num_clientes': status.get('num_clientes', {'records': 0, 'last_update': None}),
                'clientes': status.get('clientes', {'records': 0, 'last_update': None})
            }

    def filter_data(self, vendedor='Todos', mes='Todos'):
        """
        Filter data by salesperson and month.
        """
        return self._unified_analyzer.filter_ventas_data(vendedor, mes)

    def get_resumen_ventas(self, vendedor='Todos', mes='Todos'):
        """
        Get sales summary statistics.
        """
        return self._unified_analyzer.get_resumen_ventas(vendedor, mes)

    def get_ventas_por_mes(self, vendedor='Todos'):
        """
        Get sales evolution by month.
        """
        return self._unified_analyzer.get_ventas_por_mes(vendedor)

    def get_ventas_por_dia_semana(self, vendedor='Todos', mes='Todos'):
        """
        Get sales distribution by day of week for seasonality analysis.
        """
        return self._unified_analyzer.get_ventas_por_dia_semana(
            vendedor, mes, person_type='vendedor'
        )

    def get_ventas_por_zona(self, vendedor='Todos', mes='Todos'):
        """
        Get sales distribution by zone.
        """
        df = self.filter_data(vendedor, mes)

        ventas_reales = \
            df[df['tipo'].str.contains('Remision', case=False, na=False)]

        if ventas_reales.empty:
            return pd.DataFrame()

        resultado = ventas_reales.groupby('zona').agg({
            'valor_neto': 'sum',
            'cliente': 'nunique'
        }).reset_index()

        return resultado[resultado['valor_neto'] > 0]

    def get_top_clientes(self, vendedor='Todos', mes='Todos', top_n=10):
        """
        Get top customers by sales.
        """
        df = self.filter_data(vendedor, mes)
        ventas_reales = \
            df[df['tipo'].str.contains('Remision', case=False, na=False)]

        if ventas_reales.empty:
            return pd.DataFrame()

        resultado = ventas_reales.groupby('cliente_completo').agg({
            'valor_neto': 'sum',
            'documento_id': 'count'
        }).reset_index()

        return resultado.nlargest(top_n, 'valor_neto')

    def get_forma_pago_distribution(self, vendedor='Todos', mes='Todos'):
        """
        Get payment method distribution.
        """
        df = self.filter_data(vendedor, mes)
        ventas_reales = df[df['tipo'].str.contains(
            'Remision', case=False, na=False)]

        if ventas_reales.empty:
            return pd.DataFrame()

        resultado = ventas_reales.groupby('forma_pago').agg({
            'valor_neto': 'sum',
            'documento_id': 'count'
        }).reset_index()

        resultado["forma_pago"] = \
            resultado["forma_pago"].map(
                self._unified_analyzer._maestros_forma_pago)

        return resultado[resultado['valor_neto'] > 0]

    def get_treemap_data(self, vendedor='Todos', mes='Todos'):
        """
        Get data for treemap visualization.
        """
        df = self.filter_data(vendedor, mes)

        ventas_reales = \
            df[df['tipo'].str.contains('Remision', case=False, na=False)]

        if ventas_reales.empty:
            return pd.DataFrame()

        resultado = ventas_reales.groupby('cliente_completo').agg({
            'valor_neto': 'sum'
        }).reset_index()

        resultado = resultado[
            (resultado['valor_neto'] > 0) &
            (resultado['cliente_completo'].notna()) &
            (resultado['cliente_completo'] != '')
        ]

        return resultado

    def get_clientes_list(self, vendedor='Todos'):
        """
        Get list of clients for dropdown.
        """
        df = self.filter_data(vendedor, 'Todos')

        ventas_reales = \
            df[df['tipo'].str.contains('Remision', case=False, na=False)]

        if ventas_reales.empty:
            return ['Seleccione un cliente']

        clientes = ventas_reales['cliente_completo'].unique()

        return ['Seleccione un cliente'] + sorted(clientes)

    def get_evolucion_cliente(self, cliente, vendedor='Todos'):
        """
        Get client's sales evolution by day.
        """
        df = self.filter_data(vendedor, 'Todos')

        ventas_reales = \
            df[df['tipo'].str.contains('Remision', case=False, na=False)]

        if ventas_reales.empty or cliente == 'Seleccione un cliente':
            return pd.DataFrame()

        cliente_data = ventas_reales[ventas_reales['cliente_completo'] == cliente]

        if cliente_data.empty:
            return pd.DataFrame()

        # Group by date instead of month
        cliente_data['fecha_str'] = cliente_data['fecha'].dt.strftime(
            '%Y-%m-%d')

        resultado = cliente_data.groupby('fecha_str').agg({
            'valor_neto': 'sum',
            'documento_id': 'count'
        }).reset_index()

        return resultado.sort_values('fecha_str')

    def get_ventas_acumuladas_mes(self, mes='Todos', vendedor='Todos'):
        """
        Get accumulated sales up to selected month for all clients.
        """
        df = self.filter_data(vendedor, 'Todos')

        ventas_reales = \
            df[df['tipo'].str.contains('Remision', case=False, na=False)]

        if ventas_reales.empty:
            return pd.DataFrame()

        # If specific month selected, filter up to that month
        if mes != 'Todos':
            try:
                mes_limite = pd.to_datetime(mes + '-01')
                ventas_reales = ventas_reales[
                    ventas_reales['fecha'] <= mes_limite +
                    pd.offsets.MonthEnd(0)
                ]
            except:
                pass

        resultado = ventas_reales.groupby('cliente_completo').agg({
            'valor_neto': 'sum',
            'documento_id': 'count'
        }).reset_index()

        # Filter positive values only
        resultado = resultado[
            (resultado['valor_neto'] > 0) &
            (resultado['cliente_completo'].notna()) &
            (resultado['cliente_completo'] != '')
        ]

        return resultado

    def get_clientes_impactados_por_periodo(self, vendedor='Todos'):
        """
        Get number of unique clients impacted per month with percentage calculation.
        """
        df = self.filter_data(vendedor, 'Todos')

        ventas_reales = \
            df[df['tipo'].str.contains('Remision', case=False, na=False)]

        if ventas_reales.empty:
            return pd.DataFrame(), 0, 0

        # Load total clients data
        df_total_clientes = self.load_num_clientes_from_firebase()

        # Count unique clients per month (impacted clients)
        resultado = ventas_reales.groupby('mes_nombre').agg({
            'cliente_completo': 'nunique',
            'valor_neto': 'sum',
            'documento_id': 'count'
        }).reset_index()

        resultado.rename(
            columns={'cliente_completo': 'clientes_impactados'}, inplace=True)
        resultado = resultado.sort_values('mes_nombre')

        # Calculate percentages
        if not df_total_clientes.empty:
            df_total_clientes_filtrado = df_total_clientes[
                df_total_clientes['vendedor'] != 'MONICA YANET DUQUE'
            ]

            if vendedor == 'Todos':
                total_clientes_disponibles = df_total_clientes_filtrado['total_clientes'].sum(
                )
            else:
                vendor_data = df_total_clientes_filtrado[df_total_clientes_filtrado['vendedor'] == vendedor]
                total_clientes_disponibles = vendor_data['total_clientes'].sum(
                ) if not vendor_data.empty else 0
        else:
            total_clientes_disponibles = 0

        # Calculate average percentage of impacted clients
        if total_clientes_disponibles > 0 and not resultado.empty:
            promedio_impactados = resultado['clientes_impactados'].mean()
            porcentaje_promedio = (
                promedio_impactados / total_clientes_disponibles * 100)
        else:
            porcentaje_promedio = 0

        return resultado, porcentaje_promedio, total_clientes_disponibles

    def get_dias_sin_venta_por_cliente(self, vendedor='Todos'):
        """
        Get days without transfers for each client.
        Solo incluye clientes con estado diferente a 'Anulado'.
        """
        data = \
            self._unified_analyzer.get_dias_sin_venta_por_cliente(
                mode="vendedor",
                vendedor=vendedor
            )

        return data

    def get_ventas_por_rango_fechas(
            self,
            vendedor='Todos',
            fecha_inicio=None,
            fecha_fin=None):
        """
        Get sales data for date range with monthly breakdown per client.
        """
        try:
            # Filter by vendor
            df = self.filter_data(vendedor, 'Todos')

            # Filter only sales (exclude returns, credit notes, etc.)
            ventas_reales = df[df['tipo'].str.contains(
                'Remision', case=False, na=False)]

            if ventas_reales.empty:
                return pd.DataFrame()

            # Apply date range filter - INCLUIR MES COMPLETO
            if fecha_inicio and fecha_fin:
                # Asegurar que incluye el mes completo
                fecha_inicio_mes = fecha_inicio.replace(
                    day=1)  # Primer día del mes
                # Último día del mes final
                if fecha_fin.month == 12:
                    fecha_fin_mes = fecha_fin.replace(
                        year=fecha_fin.year + 1, month=1, day=1) - pd.Timedelta(days=1)
                else:
                    fecha_fin_mes = fecha_fin.replace(
                        month=fecha_fin.month + 1, day=1) - pd.Timedelta(days=1)

                ventas_reales = ventas_reales[
                    (ventas_reales['fecha'] >= fecha_inicio_mes) &
                    (ventas_reales['fecha'] <= fecha_fin_mes)
                ]

            if ventas_reales.empty:
                return pd.DataFrame()

            # Create month-year column for grouping
            ventas_reales['mes_año'] = ventas_reales['fecha'].dt.strftime(
                '%Y-%m')

            # Group by client and month
            resultado_mensual = ventas_reales.groupby(['cliente_completo', 'mes_año']).agg({
                'valor_neto': 'sum',
                'documento_id': 'count'
            }).reset_index()

            # Group by client for totals
            resultado_total = ventas_reales.groupby('cliente_completo').agg({
                'valor_neto': 'sum',
                'documento_id': 'count'
            }).reset_index()

            # Filter positive values only
            resultado_total = resultado_total[
                (resultado_total['valor_neto'] > 0) &
                (resultado_total['cliente_completo'].notna()) &
                (resultado_total['cliente_completo'] != '')
            ]

            resultado_mensual = resultado_mensual[
                (resultado_mensual['valor_neto'] > 0) &
                (resultado_mensual['cliente_completo'].notna()) &
                (resultado_mensual['cliente_completo'] != '')
            ]

            return {
                'total': resultado_total,
                'mensual': resultado_mensual
            }

        except Exception as e:
            print(f"❌ Error en get_ventas_por_rango_fechas: {e}")
            return pd.DataFrame()

    def load_convenios_from_firebase(self, force_reload=False):
        """
        Load convenios data from Firebase database with caching.
        """

        return self._unified_analyzer.load_convenios_from_firebase(force_reload)

    def get_analisis_convenios(self, vendedor='Todos', mes='Todos'):
        """
        Analyze compliance with agreements using correct field names.
        """
        # Load convenios
        df_convenios = self.load_convenios_from_firebase()

        if df_convenios.empty:
            return pd.DataFrame()

        # Get sales data
        df_ventas = self.filter_data(vendedor, mes)
        ventas_reales = df_ventas[df_ventas['tipo'].str.contains(
            'Remision', case=False, na=False)]

        if ventas_reales.empty:
            return pd.DataFrame()

        # Group sales by NIT
        ventas_por_nit = ventas_reales.groupby('nit').agg({
            'valor_bruto': 'sum',
            'descuento': lambda x: abs(x).sum(),
            'cliente_completo': 'first',
            'documento_id': 'count',
            'vendedor': 'first'
        }).reset_index()

        # Calculate net value (valor_bruto - descuento) for target comparison
        ventas_por_nit['valor_neto'] = ventas_por_nit['valor_bruto'] - \
            ventas_por_nit['descuento']

        # Calculate actual discount percentage (still using valor_bruto as denominator)
        ventas_por_nit['descuento_real_pct'] = (
            ventas_por_nit['descuento'] / ventas_por_nit['valor_bruto'] * 100
        ).round(2)

        # Merge with convenios using correct field names
        resultado = pd.merge(
            ventas_por_nit,
            df_convenios[['nit', 'client_name', 'razon', 'seller_name',
                          'rebate_pct', 'target_value', 'observations']],
            on='nit',
            how='inner'
        )

        if resultado.empty:
            return pd.DataFrame()

        # Calculate compliance
        resultado['cumplimiento_descuento'] = (
            resultado['descuento_real_pct'] <= resultado['rebate_pct']
        )
        resultado['diferencia_descuento'] = (
            resultado['descuento_real_pct'] - resultado['rebate_pct']
        ).round(2)

        # Calculate target compliance using valor_neto
        resultado['cumplimiento_meta'] = (
            resultado['valor_neto'] >= resultado['target_value']
        )
        resultado['diferencia_meta'] = (
            resultado['valor_neto'] - resultado['target_value']
        )

        # Calculate progress percentage towards target using valor_neto
        resultado['progreso_meta_pct'] = (
            resultado['valor_neto'] / resultado['target_value'] * 100
        ).round(1)

        # Calculate expected sales based on days elapsed in the year
        today = datetime.now()
        days_elapsed = today.timetuple().tm_yday  # Day of year (1-365/366)
        days_in_year = 366 if today.year % 4 == 0 else 365  # Check for leap year

        resultado['dias_transcurridos'] = days_elapsed
        resultado['ventas_esperadas'] = (
            resultado['target_value'] / days_in_year * days_elapsed).round(0)
        resultado['progreso_esperado_pct'] = \
            round(days_elapsed / days_in_year * 100, 2)

        return resultado

    def get_ventas_por_rango_meses(self, vendedor='Todos', mes_inicio=1, mes_fin=12, min_monto=None, max_monto=None):
        """
        Get sales data filtered by month range (1-12) and optionally by amount range
        """
        try:
            # Filter by vendor
            df = self.filter_data(vendedor, 'Todos')

            # Filter only sales
            ventas_reales = df[df['tipo'].str.contains(
                'Remision', case=False, na=False)]

            if ventas_reales.empty:
                return {'total': pd.DataFrame(), 'mensual': pd.DataFrame()}

            # Apply month range filter
            ventas_reales = ventas_reales[
                (ventas_reales['fecha'].dt.month >= mes_inicio) &
                (ventas_reales['fecha'].dt.month <= mes_fin)
            ]

            if ventas_reales.empty:
                return {'total': pd.DataFrame(), 'mensual': pd.DataFrame()}

            # Create month-year column for grouping
            ventas_reales['mes_año'] = ventas_reales['fecha'].dt.strftime(
                '%Y-%m')

            # Group by client for totals FIRST
            resultado_total = ventas_reales.groupby('cliente_completo').agg({
                'valor_neto': 'sum',
                'documento_id': 'count'
            }).reset_index()

            # Apply amount filter if specified
            if min_monto is not None and max_monto is not None:
                resultado_total = resultado_total[
                    (resultado_total['valor_neto'] >= min_monto) &
                    (resultado_total['valor_neto'] <= max_monto)
                ]

            # Filter the original data to match the clients that passed the amount filter
            if not resultado_total.empty:
                clientes_filtrados = resultado_total['cliente_completo'].tolist(
                )
                ventas_reales = ventas_reales[ventas_reales['cliente_completo'].isin(
                    clientes_filtrados)]

            # Group by client and month for monthly breakdown
            resultado_mensual = ventas_reales.groupby(['cliente_completo', 'mes_año']).agg({
                'valor_neto': 'sum',
                'documento_id': 'count'
            }).reset_index()

            # Filter positive values only
            resultado_total = resultado_total[
                (resultado_total['valor_neto'] > 0) &
                (resultado_total['cliente_completo'].notna()) &
                (resultado_total['cliente_completo'] != '')
            ]

            resultado_mensual = resultado_mensual[
                (resultado_mensual['valor_neto'] > 0) &
                (resultado_mensual['cliente_completo'].notna()) &
                (resultado_mensual['cliente_completo'] != '')
            ]

            return {
                'total': resultado_total,
                'mensual': resultado_mensual
            }

        except Exception as e:
            print(f"❌ Error en get_ventas_por_rango_meses: {e}")
            return {'total': pd.DataFrame(), 'mensual': pd.DataFrame()}

    def load_recibos_from_firebase(self, force_reload=False):
        """
        Delegación al analyzer unificado.
        """
        try:
            if not force_reload and not self._unified_analyzer._df_recibos.empty:
                return self._unified_analyzer._df_recibos

            start_time = time.time()

            db = self._unified_analyzer._get_db()

            if not db:
                print("❌ [VentasAnalyzer] No se pudo obtener conexión para recibos")
                return pd.DataFrame()

            data = db.get("recibos_caja")

            if data:
                result = self.process_recibos_data(data)

                # Guardar en cache
                self._unified_analyzer._df_recibos = result
                self._last_recibos_update = datetime.now()

                load_time = time.time() - start_time

                return result
            else:
                print(
                    "⚠️ [VentasAnalyzer] No recibos_caja data found in Firebase")

                self._unified_analyzer._df_recibos = pd.DataFrame()

                return pd.DataFrame()

        except Exception as e:
            print(
                f"❌ [VentasAnalyzer] Error loading recibos_caja data from Firebase: {e}")

            self._unified_analyzer._df_recibos = pd.DataFrame()

            return pd.DataFrame()

    def process_recibos_data(self, data):
        """
        Process recibos_caja data with date field.
        """
        if not data:
            return pd.DataFrame()

        recibos_list = []

        for recibo_id, recibo_info in data.items():
            id1 = recibo_info.get('id1', '')

            if not id1:
                continue

            vendedor = \
                self._unified_analyzer.get_seller_name(id1)

            if not vendedor:
                continue

            recibo_row = \
                {
                    'recibo_id': recibo_id,
                    'id1': id1,
                    'valor_recibo': float(recibo_info.get('valor_recibo', 0) or 0),
                    'vendedor': vendedor,
                    'fecha': recibo_info.get('fecha', '')
                }

            recibos_list.append(recibo_row)

        df_recibos = pd.DataFrame(
            recibos_list) if recibos_list else pd.DataFrame()

        if not df_recibos.empty:
            # Process dates
            df_recibos['fecha'] = pd.to_datetime(
                df_recibos['fecha'], errors='coerce')
            df_recibos['mes_nombre'] = df_recibos['fecha'].dt.strftime('%Y-%m')
            df_recibos['fecha_str'] = df_recibos['fecha'].dt.strftime(
                '%Y-%m-%d')

        return df_recibos

    def _count_active_clients_by_vendor(self) -> Dict[str, int]:
        """
        Count the number of active clients per vendor name.

        Returns:
            Dict[str, int]: Dict with clients by vendor.
        """
        valid_types = {"Cliente", "Cliente proveedor"}

        # Count clients by vendor code
        counts = Counter(
            c["vendedor"]
            for c in self._unified_analyzer._clientes_id_cache.values()
            if c.get("estado_maestro") == "Activo" and c.get("tipo") in valid_types
        )

        # Map vendor codes to vendor names
        return \
            {
                self._unified_analyzer._maestro_vendedores.get(code, f"N/A"): count
                for code, count in counts.items()
            }

    def load_num_clientes_from_firebase(self, force_reload=False):
        """
        Get number of clients by vendor.

        Args:
            force_reload (bool): Si True, fuerza la recarga incluso si ya hay datos
        """
        try:
            # Usar cache si está disponible y no es recarga forzada
            if not force_reload and not self._unified_analyzer._df_num_clientes.empty:
                return self._unified_analyzer._df_num_clientes

            start_time = time.time()

            db = self._unified_analyzer._get_db()

            if not db:
                print(
                    "❌ [VentasAnalyzer] No se pudo obtener conexión para num_clientes")
                return pd.DataFrame()

            # Get number of clients by vendor
            data = self._count_active_clients_by_vendor()

            if data:
                result = self.process_num_clientes_data(data)

                # Guardar en cache
                self._unified_analyzer._df_num_clientes = result
                self._last_num_clientes_update = datetime.now()

                return result
            else:
                print(
                    "⚠️ [VentasAnalyzer] No vendor data found in Firebase")

                self._unified_analyzer._df_num_clientes = pd.DataFrame()

                return pd.DataFrame()

        except Exception as e:
            print(
                f"❌ [VentasAnalyzer] Error loading vendor data from Firebase: {e}")

            self._unified_analyzer._df_num_clientes = pd.DataFrame()

            return pd.DataFrame()

    def get_recibos_data(self, force_reload=False):
        """
        Convenient access to auto-loaded receipt data.
        """
        if self._unified_analyzer._df_recibos.empty or force_reload:
            return self.load_recibos_from_firebase(force_reload)

        return self._unified_analyzer._df_recibos

    def get_num_clientes_data(self, force_reload=False):
        """
        Convenient access to num_clients data with autoload.
        """
        if self._unified_analyzer._df_num_clientes.empty or force_reload:
            return self.load_num_clientes_from_firebase(force_reload)

        return self._unified_analyzer._df_num_clientes

    def process_num_clientes_data(self, data):
        """
        Process num_clientes_por_vendedor data.
        """
        if not data:
            return pd.DataFrame()

        clientes_list = []

        for vendedor, num_clientes in data.items():
            clientes_row = \
                {
                    'vendedor': vendedor,
                    'total_clientes': int(num_clientes or 0)
                }
            clientes_list.append(clientes_row)

        return \
            pd.DataFrame(clientes_list) if clientes_list else pd.DataFrame()

    def get_recaudo_por_dia(self, vendedor='Todos', mes='Todos'):
        """
        Get daily collection amounts using real date field.
        """
        df_recibos = self.load_recibos_from_firebase()

        if df_recibos.empty:
            return pd.DataFrame(), 0

        # Filter by vendedor if needed
        if vendedor != 'Todos':
            df_recibos = df_recibos[df_recibos['vendedor'] == vendedor]

        # Filter by month if specified
        if mes != 'Todos':
            df_recibos = df_recibos[df_recibos['mes_nombre'] == mes]

        total_recaudo = df_recibos['valor_recibo'].sum()

        if vendedor == 'Todos':
            # Group by date for overall daily view
            resultado = df_recibos.groupby('fecha_str').agg({
                'valor_recibo': 'sum',
                'recibo_id': 'count'
            }).reset_index()
            resultado = resultado.sort_values('fecha_str')
        else:
            # Group by date for specific vendor
            resultado = df_recibos.groupby('fecha_str').agg({
                'valor_recibo': 'sum',
                'recibo_id': 'count'
            }).reset_index()
            resultado = resultado.sort_values('fecha_str')

        return resultado, total_recaudo

    def get_recaudo_por_mes(self, vendedor='Todos'):
        """
        Get monthly collection amounts using real date field.
        """
        df_recibos = self.load_recibos_from_firebase()
        if df_recibos.empty:
            return pd.DataFrame(), 0

        # Filter by vendedor if needed
        if vendedor != 'Todos':
            df_recibos = df_recibos[df_recibos['vendedor'] == vendedor]

        total_recaudo = df_recibos['valor_recibo'].sum()

        # Group by month
        resultado = df_recibos.groupby('mes_nombre').agg({
            'valor_recibo': 'sum',
            'recibo_id': 'count'
        }).reset_index()
        resultado = resultado.sort_values('mes_nombre')

        return resultado, total_recaudo

    def get_recaudo_por_vendedor(self, mes=None):
        """
        Get collection data by vendor, optionally filtered by month.

        Args:
            mes (_type_, optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        """
        try:
            df_recibos = self.load_recibos_from_firebase()

            if df_recibos.empty:
                return pd.DataFrame(), 0

            # Aplicar filtro de mes si está especificado
            if mes and mes != 'Todos':
                # Assumiendo que df_recibos tiene una columna 'mes_nombre'
                df_filtered = df_recibos[df_recibos['mes_nombre'] == mes]
            else:
                df_filtered = df_recibos

            if df_filtered.empty:
                return pd.DataFrame(), 0

            # Agrupar por vendedor
            result = df_filtered.groupby('vendedor').agg({
                'valor_recibo': 'sum',
                'recibo_id': 'count'
            }).reset_index()

            result = result.sort_values('valor_recibo', ascending=False)
            total_recaudo = result['valor_recibo'].sum()

            return result, total_recaudo
        except Exception as e:
            print(f"Error en get_recaudo_por_vendedor: {e}")
            return pd.DataFrame(), 0

    def get_resumen_recaudo(self, vendedor='Todos', mes='Todos'):
        """
        Get collection summary for the selected period.
        """
        df_recibos = self.load_recibos_from_firebase()
        if df_recibos.empty:
            return 0

        # Filter by vendedor if needed
        if vendedor != 'Todos':
            df_recibos = df_recibos[df_recibos['vendedor'] == vendedor]

        # Filter by month if specified
        if mes != 'Todos':
            df_recibos = df_recibos[df_recibos['mes_nombre'] == mes]

        return df_recibos['valor_recibo'].sum()

    def get_variaciones_mensuales_clientes(self, vendedor='Todos', mes_inicio=1, mes_fin=12, filtro_tipo='todos'):
        """
        Obtener variaciones porcentuales mensuales de ventas por URL para heatmap
        """
        try:
            df = self.filter_data(vendedor, 'Todos')
            ventas_reales = df[df['tipo'].str.contains(
                'Remision', case=False, na=False)]

            if ventas_reales.empty:
                return pd.DataFrame()

            # Filtrar por rango de meses
            ventas_reales = ventas_reales[
                (ventas_reales['fecha'].dt.month >= mes_inicio) &
                (ventas_reales['fecha'].dt.month <= mes_fin)
            ]

            if ventas_reales.empty:
                return pd.DataFrame()

            # Crear mes_año para agrupación
            ventas_reales['mes_año'] = ventas_reales['fecha'].dt.strftime(
                '%Y-%m')

            # Agrupar por URL y mes
            resultado = ventas_reales.groupby(['url', 'mes_año']).agg({
                'valor_neto': 'sum'
            }).reset_index()

            # Crear tabla pivote con ventas por URL y mes
            pivot_table = resultado.pivot(
                index='url',
                columns='mes_año',
                values='valor_neto'
            ).fillna(0)

            if pivot_table.empty or pivot_table.shape[1] < 2:
                return pd.DataFrame()

            # Ordenar columnas cronológicamente
            meses_ordenados = sorted(pivot_table.columns)
            pivot_table = pivot_table[meses_ordenados]

            # Calcular variaciones porcentuales mes a mes
            variaciones = pd.DataFrame(index=pivot_table.index)

            for i in range(1, len(meses_ordenados)):
                mes_anterior = meses_ordenados[i-1]
                mes_actual = meses_ordenados[i]

                # Calcular variación porcentual correctamente
                ventas_anterior = pivot_table[mes_anterior]
                ventas_actual = pivot_table[mes_actual]

                # Solo calcular variación si hay ventas en el mes anterior
                variacion = pd.Series(index=pivot_table.index, dtype=float)

                for url in pivot_table.index:
                    anterior = ventas_anterior[url]
                    actual = ventas_actual[url]

                    if anterior > 0:  # Solo si hay ventas en mes anterior
                        variacion[url] = ((actual - anterior) / anterior) * 100
                    # Nueva venta (antes no había)
                    elif actual > 0 and anterior == 0:
                        variacion[url] = 100.0  # 100% de crecimiento desde 0
                    else:
                        variacion[url] = 0.0  # Sin cambios o ambos en 0

                # Crear nombre de columna más legible
                try:
                    fecha_ant = pd.to_datetime(mes_anterior + '-01')
                    fecha_act = pd.to_datetime(mes_actual + '-01')

                    meses_esp = {
                        1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr',
                        5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago',
                        9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
                    }

                    nombre_col = f"{meses_esp[fecha_ant.month]} → {meses_esp[fecha_act.month]}"
                except:
                    nombre_col = f"{mes_anterior} → {mes_actual}"

                variaciones[nombre_col] = variacion

            if variaciones.empty:
                return pd.DataFrame()

            # Filtrar URLs que tengan al menos una variación significativa
            mask_activos = (variaciones.abs() > 0.1).any(axis=1)
            variaciones = variaciones[mask_activos]

            if variaciones.empty:
                return pd.DataFrame()

            # CORRECCIÓN: Calcular suma de variaciones porcentuales para ranking
            variaciones['suma_variaciones'] = variaciones.sum(axis=1)

            # Aplicar filtros CORRECTAMENTE por suma de variaciones
            if filtro_tipo == 'top10':
                variaciones = variaciones.nlargest(10, 'suma_variaciones')
            elif filtro_tipo == 'bottom10':
                variaciones = variaciones.nsmallest(10, 'suma_variaciones')
            #     variaciones = variaciones #.nlargest(, 'suma_variaciones')

            # Remover columna auxiliar antes de retornar
            variaciones = variaciones.drop('suma_variaciones', axis=1)

            return variaciones

        except Exception as e:
            print(f"❌ Error en get_variaciones_mensuales_clientes: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def calculate_enhanced_rfm_scores(self, vendedor='Todos', use_cache=True):
        """
        Calcular RFM+ Score con CACHE para evitar recálculos
        Mantiene TODAS las categorías y cálculos originales
        """
        try:
            # Generar clave de cache
            cache_key = f"rfm_{vendedor}"
            current_time = datetime.now()

            # Verificar si hay datos en cache válidos
            if (use_cache and
                cache_key in self._rfm_cache and
                self._rfm_cache_timestamp and
                    (current_time - self._rfm_cache_timestamp).seconds < self._rfm_cache_ttl):
                # Retornar copia para evitar modificaciones
                return self._rfm_cache[cache_key].copy()

            # Si no hay cache o expiró, usar el método original optimizado
            rfm_data = self._calculate_enhanced_rfm_optimized(vendedor)

            # Guardar en cache
            if use_cache and not rfm_data.empty:
                self._rfm_cache[cache_key] = rfm_data.copy()
                self._rfm_cache_timestamp = current_time

            return rfm_data

        except Exception as e:
            print(f"❌ Error en RFM con cache: {e}")
            return pd.DataFrame()

    def _calculate_client_trends(self, ventas_data, cliente, fecha_corte):
        """
        Calcular métricas de tendencia para un cliente específico.
        CORREGIDO: Maneja correctamente la conversión datetime a period.
        """
        try:
            import pandas as pd

            # Filtrar datos del cliente
            client_data = ventas_data[ventas_data['cliente_completo'] == cliente].copy(
            )

            if len(client_data) < 2:
                return {
                    'cliente_completo': cliente,
                    'cagr_6m': 0,
                    'variacion_3m': 0,
                    'variacion_reciente': 0,
                    'tendencia_general': 'estable',
                    'meses_activos': 1,
                    'consistencia': 0
                }

            # Preparar datos mensuales
            client_data['mes_periodo'] = client_data['fecha'].dt.to_period('M')
            monthly_sales = client_data.groupby(
                'mes_periodo')['valor_neto'].sum().sort_index()

            # 🔧 CORRECCIÓN: Convertir fecha_corte a pandas Timestamp y luego a period
            if hasattr(fecha_corte, 'to_period'):
                # Ya es un pandas Timestamp
                ultimo_periodo_completo = fecha_corte.to_period('M')
            else:
                # Es un datetime, convertir a pandas Timestamp primero
                ultimo_periodo_completo = pd.Timestamp(
                    fecha_corte).to_period('M')

            # Filtrar hasta el último período completo
            monthly_sales = monthly_sales[monthly_sales.index <=
                                          ultimo_periodo_completo]

            if len(monthly_sales) < 2:
                return {
                    'cliente_completo': cliente,
                    'cagr_6m': 0,
                    'variacion_3m': 0,
                    'variacion_reciente': 0,
                    'tendencia_general': 'estable',
                    'meses_activos': 1,
                    'consistencia': 0
                }

            # 1. CAGR de últimos 6 meses (o todos los meses disponibles si son menos)
            meses_disponibles = len(monthly_sales)
            meses_cagr = min(6, meses_disponibles)  # REVISAR
            recent_months = monthly_sales.tail(meses_cagr)

            if len(recent_months) >= 2:
                primer_valor = recent_months.iloc[0]
                ultimo_valor = recent_months.iloc[-1]
                periodos = len(recent_months) - 1

                if primer_valor > 0 and periodos > 0:
                    cagr_6m = ((ultimo_valor / primer_valor)
                               ** (1/periodos) - 1) * 100
                else:
                    cagr_6m = 0
            else:
                cagr_6m = 0

            # 2. Variación de últimos 3 meses vs 3 meses anteriores
            if len(monthly_sales) >= 6:
                ultimos_3m = monthly_sales.tail(3).sum()
                anteriores_3m = monthly_sales.tail(6).head(3).sum()

                if anteriores_3m > 0:
                    variacion_3m = (
                        (ultimos_3m - anteriores_3m) / anteriores_3m) * 100
                else:
                    variacion_3m = 100 if ultimos_3m > 0 else 0
            else:
                variacion_3m = 0

            # 3. Variación del último mes vs promedio anterior
            if len(monthly_sales) >= 3:
                ultimo_mes = monthly_sales.iloc[-1]
                promedio_anterior = monthly_sales.iloc[:-1].mean()

                if promedio_anterior > 0:
                    variacion_reciente = (
                        (ultimo_mes - promedio_anterior) / promedio_anterior) * 100
                else:
                    variacion_reciente = 100 if ultimo_mes > 0 else 0
            else:
                variacion_reciente = 0

            # 4. Tendencia general (combinando indicadores)
            if cagr_6m > 10 and variacion_3m > 5:
                tendencia_general = 'crecimiento_fuerte'
            elif cagr_6m > 0 and variacion_3m >= 0:
                tendencia_general = 'crecimiento'
            elif cagr_6m < -10 and variacion_3m < -5:
                tendencia_general = 'decrecimiento_fuerte'
            elif cagr_6m < 0 and variacion_3m < 0:
                tendencia_general = 'decrecimiento'
            else:
                tendencia_general = 'estable'

            # 5. Consistencia (desviación estándar relativa)
            if len(monthly_sales) >= 3:
                cv = (monthly_sales.std() / monthly_sales.mean()) * \
                    100 if monthly_sales.mean() > 0 else 100
                # Menor variabilidad = mayor consistencia
                consistencia = max(0, 100 - cv)
            else:
                consistencia = 50  # Valor neutral para pocos datos

            return {
                'cliente_completo': cliente,
                'cagr_6m': round(cagr_6m, 2),
                'variacion_3m': round(variacion_3m, 2),
                'variacion_reciente': round(variacion_reciente, 2),
                'tendencia_general': tendencia_general,
                'meses_activos': meses_disponibles,
                'consistencia': round(consistencia, 1)
            }

        except Exception as e:
            print(f"❌ Error calculando tendencias para {cliente}: {e}")
            import traceback
            traceback.print_exc()
            return {
                'cliente_completo': cliente,
                'cagr_6m': 0,
                'variacion_3m': 0,
                'variacion_reciente': 0,
                'tendencia_general': 'estable',
                'meses_activos': 1,
                'consistencia': 0
            }

    def _calculate_trend_score(self, row):
        """
        Calcular score de tendencia (1-5) basado en CAGR y variaciones.
        """
        try:
            cagr = row['cagr_6m']
            var_3m = row['variacion_3m']
            var_reciente = row['variacion_reciente']
            consistencia = row['consistencia']

            # Score base según CAGR
            if cagr >= 20:
                base_score = 5
            elif cagr >= 10:
                base_score = 4
            elif cagr >= 0:
                base_score = 3
            elif cagr >= -10:
                base_score = 2
            else:
                base_score = 1

            # Ajustar según variación reciente (±0.5 puntos)
            if var_reciente > 15:
                base_score += 0.5
            elif var_reciente < -15:
                base_score -= 0.5

            # Ajustar según consistencia (±0.3 puntos)
            if consistencia > 80:
                base_score += 0.3
            elif consistencia < 30:
                base_score -= 0.3

            # Limitar entre 1 y 5
            final_score = max(1, min(5, base_score))

            return int(round(final_score))

        except:
            return 3  # Score neutral en caso de error

    def _categorize_enhanced_rfm(self, row):
        """
        Categorizar cliente según RFM+ score (incluye análisis de tendencia).
        """
        R, F, M, T = row['R'], row['F'], row['M'], row['T']
        tendencia = row['tendencia_general']
        cagr = row['cagr_6m']

        # 🏆 CAMPEONES VERDADEROS: Alto RFM + Tendencia positiva
        if R >= 4 and F >= 4 and M >= 4 and T >= 4:
            return "🏆 Campeones Ascendentes"

        # ⚠️ CAMPEONES EN RIESGO: Alto RFM pero tendencia negativa
        elif R >= 4 and F >= 4 and M >= 4 and T <= 2:
            return "⚠️ Campeones en Declive"

        # 🚀 CLIENTES ESTRELLA: Buenos indicadores + crecimiento fuerte
        elif F >= 3 and M >= 3 and T >= 4 and cagr > 15:
            return "🚀 Clientes Estrella"

        # 💎 CLIENTES LEALES ESTABLES: Buenos en F,M + tendencia estable
        elif F >= 4 and M >= 4 and T >= 3:
            return "💎 Leales Estables"

        # 📉 CLIENTES EN CAÍDA: Buenos históricamente pero decreciendo
        elif F >= 3 and M >= 4 and T <= 2 and cagr < -10:
            return "📉 En Caída Libre"

        # ⭐ POTENCIALES CON MOMENTUM: Recientes + crecimiento
        elif R >= 4 and T >= 4:
            return "⭐ Potenciales con Momentum"

        # 🌱 NUEVOS EN DESARROLLO: Nuevos + indicios positivos
        elif R >= 4 and F <= 2 and T >= 3:
            return "🌱 Nuevos en Desarrollo"

        # 🔥 OPORTUNIDADES CALIENTES: Crecimiento fuerte reciente
        elif T >= 4 and M >= 3:
            return "🔥 Oportunidades Calientes"

        # ⚠️ NECESITAN ATENCIÓN URGENTE: Buenos en M pero inactivos y decreciendo
        elif M >= 4 and R <= 2 and T <= 2:
            return "⚠️ Atención Urgente"

        # 🆘 RESCATE INMEDIATO: Alto valor + muy inactivos + decrecimiento
        elif M >= 4 and R <= 2 and F >= 3 and T <= 2:
            return "🆘 Rescate Inmediato"

        # 😴 HIBERNANDO ESTABLES: Baja actividad pero sin grandes cambios
        elif R <= 2 and F <= 2 and T == 3:
            return "😴 Hibernando Estables"

        # 💸 PERDIDOS: Muy baja actividad + tendencia negativa
        elif R <= 2 and F <= 2 and T <= 2:
            return "💸 Perdidos"

        # 🔄 IRREGULARES: Patrones inconsistentes
        else:
            return "🔄 Comportamiento Irregular"

    def _get_client_recommendation(self, client_info):
        """
        Generar recomendación específica para un cliente basada en su perfil RFM+.
        """
        categoria = client_info['categoria_rfm']
        cagr = client_info['cagr_6m']
        recency = client_info['recency_days']

        recommendations = {
            "🏆 Campeones Ascendentes": "Cliente estrella en crecimiento. Ofrecer descuentos de forma recurrente y acceso a nuevas líneas.",
            "⚠️ Campeones en Declive": "CÓDIGO ROJO: Era nuestro mejor cliente pero está comprando menos.",
            "🚀 Clientes Estrella": "Cliente despegando rápido. Ofrecer nuevas líneas, contratos anuales, condiciones especiales.",
            "💎 Leales Estables": "Cliente confiable y constante. Mantener relación, ofertas de temporada, productos complementarios.",
            "📉 En Caída Libre": "EMERGENCIA: Cliente se está yendo. Reunión urgente, ofertas agresivas, plan de choque.",
            "⭐ Potenciales con Momentum": "Cliente nuevo con buen arranque. Acelerar con descuentos progresivos y mayor frecuencia.",
            "🌱 Nuevos en Desarrollo": "Cliente recién llegado con potencial. Educación de productos, seguimiento cercano, ofertas de bienvenida.",
            "🔥 Oportunidades Calientes": "Cliente en racha compradora. Aprovechar ahora con ofertas grandes, nuevas líneas, expansión.",
            "⚠️ Atención Urgente": "Cliente valioso pero inactivo. Llamada personal, revisar necesidades, ofertas de reactivación.",
            "🆘 Rescate Inmediato": "Última carta con cliente importante. Intervención directiva, condiciones irresistibles, todo vale.",
            "😴 Hibernando Estables": "Cliente quieto pero no perdido. Recordatorios suaves, promociones estacionales, mantener contacto.",
            "💸 Perdidos": "Cliente prácticamente ido. Último intento automático, ofertas de regreso, si no responde archivar.",
            "🔄 Comportamiento Irregular": "Cliente impredecible. Estudiar cuándo compra más, adaptar ofertas a su patrón específico."
        }

        base_rec = recommendations.get(categoria, "Seguimiento estándar.")

        # Añadir notas específicas según métricas
        if recency > 180:
            base_rec += f" NOTA: {recency} días sin comprar - Muy urgente."
        elif recency > 90:
            base_rec += f" NOTA: {recency} días sin comprar - Prioritario."

        if cagr < -20:
            base_rec += f" ALERTA: Decrecimiento severo ({cagr:.1f}% CAGR)."
        elif cagr > 30:
            base_rec += f" OPORTUNIDAD: Crecimiento excepcional ({cagr:.1f}% CAGR)."

        return base_rec

    def calculate_rfm_scores(self, vendedor='Todos'):
        """
        Wrapper para mantener compatibilidad. Llama al método enhanced.
        """
        return self.calculate_enhanced_rfm_scores(vendedor)

    def get_rfm_plus_insights(rfm_data):
        """
        Generar insights mejorados basados en análisis RFM+ (incluye tendencias).
        """
        if rfm_data.empty:
            return {"error": "No hay datos para analizar"}

        # Análisis de distribución por categorías
        category_distribution = rfm_data['categoria_rfm'].value_counts()
        total_customers = len(rfm_data)
        total_revenue = rfm_data['monetary'].sum()

        insights = {
            "distribution": {},
            "trend_analysis": {},
            "risk_analysis": {},
            "opportunities": [],
            "recommendations": [],
            "kpis": {},
            "alerts": []
        }

        # KPIs principales incluyendo tendencias
        insights["kpis"] = {
            "total_customers": total_customers,
            "total_revenue": total_revenue,
            "avg_order_value": rfm_data['valor_promedio_transaccion'].mean(),
            "avg_frequency": rfm_data['frequency'].mean(),
            "avg_recency": rfm_data['recency_days'].mean(),
            "avg_cagr": rfm_data['cagr_6m'].mean(),
            "customers_growing": len(rfm_data[rfm_data['cagr_6m'] > 0]),
            "customers_declining": len(rfm_data[rfm_data['cagr_6m'] < -10])
        }

        # Distribución por categorías
        for category, count in category_distribution.items():
            percentage = (count / total_customers) * 100
            category_revenue = rfm_data[rfm_data['categoria_rfm']
                                        == category]['monetary'].sum()
            revenue_percentage = (category_revenue / total_revenue) * 100

            insights["distribution"][category] = {
                "count": count,
                "percentage": round(percentage, 1),
                "revenue": category_revenue,
                "revenue_percentage": round(revenue_percentage, 1)
            }

        # Análisis de tendencias
        growing_customers = rfm_data[rfm_data['cagr_6m'] > 10]
        declining_customers = rfm_data[rfm_data['cagr_6m'] < -10]

        insights["trend_analysis"] = {
            "growing_count": len(growing_customers),
            "growing_revenue": growing_customers['monetary'].sum() if not growing_customers.empty else 0,
            "declining_count": len(declining_customers),
            "declining_revenue": declining_customers['monetary'].sum() if not declining_customers.empty else 0
        }

        # Análisis de riesgo (clientes valiosos en declive)
        high_value_at_risk = rfm_data[
            (rfm_data['monetary'] > rfm_data['monetary'].quantile(0.8)) &
            (rfm_data['cagr_6m'] < -10)
        ]

        insights["risk_analysis"] = {
            "high_value_at_risk_count": len(high_value_at_risk),
            "revenue_at_risk": high_value_at_risk['monetary'].sum() if not high_value_at_risk.empty else 0
        }

        # Generar alertas automáticas
        if len(declining_customers) > total_customers * 0.3:
            insights["alerts"].append({
                "level": "high",
                "message": f"⚠️ ALERTA: {len(declining_customers)} clientes ({(len(declining_customers)/total_customers)*100:.1f}%) en decrecimiento severo"
            })

        if insights["risk_analysis"]["revenue_at_risk"] > total_revenue * 0.2:
            insights["alerts"].append({
                "level": "critical",
                "message": f"🚨 CRÍTICO: {format_currency_int(insights['risk_analysis']['revenue_at_risk'])} en riesgo por clientes valiosos en declive"
            })

        if insights["kpis"]["avg_recency"] > 90:
            insights["alerts"].append({
                "level": "high",
                "message": f"📅 ATENCIÓN: Recencia promedio de {insights['kpis']['avg_recency']:.0f} días es muy alta"
            })

        # Oportunidades (clientes con momentum)
        opportunities_data = rfm_data[
            (rfm_data['cagr_6m'] > 20) |
            (rfm_data['categoria_rfm'].str.contains(
                'Estrella|Momentum|Calientes', na=False))
        ].sort_values('cagr_6m', ascending=False).head(5)

        for _, customer in opportunities_data.iterrows():
            insights["opportunities"].append({
                "customer": customer['cliente_completo'],
                "category": customer['categoria_rfm'],
                "cagr": customer['cagr_6m'],
                "revenue": customer['monetary'],
                "action": "Acelerar crecimiento con ofertas premium"
            })

        # Recomendaciones automáticas
        if category_distribution.get("🏆 Campeones Ascendentes", 0) > 0:
            count = category_distribution.get("🏆 Campeones Ascendentes", 0)
            insights["recommendations"].append({
                "priority": "Crítica",
                "category": "🏆 Campeones Ascendentes",
                "action": f"Crear programa de clientes elite para {count} campeones que están creciendo",
                "impact": f"📈 Estos {count} clientes son oro puro - están comprando más y creciendo. Asegurar que nunca se vayan con beneficios exclusivos y atención personalizada.",
                "next_steps": "Contactar en 48h para ofrecer descuentos por volumen y productos premium"
            })

        # ⚠️ Campeones en Declive
        if category_distribution.get("⚠️ Campeones en Declive", 0) > 0:
            count = category_distribution.get("⚠️ Campeones en Declive", 0)
            revenue_at_risk = rfm_data[rfm_data['categoria_rfm']
                                       == "⚠️ Campeones en Declive"]['monetary'].sum()
            insights["recommendations"].append({
                "priority": "URGENTE",
                "category": "⚠️ Campeones en Declive",
                "action": f"ALERTA ROJA: {count} clientes top están comprando menos",
                "impact": f"🚨 Riesgo de perder {format_currency_int(revenue_at_risk)} en ventas. Estos eran nuestros mejores clientes pero algo está pasando.",
                "next_steps": "Llamar HOY al gerente comercial. Reunión urgente para entender qué está fallando"
            })

        # 📉 En Caída Libre
        # Si es más del 5%
        if category_distribution.get("📉 En Caída Libre", 0) > total_customers * 0.05:
            count = category_distribution.get("📉 En Caída Libre", 0)
            insights["recommendations"].append({
                "priority": "CRÍTICA",
                "category": "📉 En Caída Libre",
                "action": f"Emergencia comercial: {count} clientes están en caída libre",
                "impact": f"💸 Estos clientes se nos están escapando rápidamente. Cada día que pasa perdemos más dinero.",
                "next_steps": "Plan de choque: ofertas especiales, visita personal del gerente, descuentos agresivos"
            })

        # 🚀 Clientes Estrella
        if category_distribution.get("🚀 Clientes Estrella", 0) > 0:
            count = category_distribution.get("🚀 Clientes Estrella", 0)
            insights["recommendations"].append({
                "priority": "Alta",
                "category": "🚀 Clientes Estrella",
                "action": f"Acelerar crecimiento de {count} clientes que están despegando",
                "impact": f"🌟 Estos {count} clientes están creciendo rápido. Es el momento perfecto para venderles más productos.",
                "next_steps": "Ofrecer paquetes más grandes, nuevas líneas de productos, descuentos por anticipado"
            })

        # 🔥 Oportunidades Calientes
        if category_distribution.get("🔥 Oportunidades Calientes", 0) > 0:
            count = category_distribution.get("🔥 Oportunidades Calientes", 0)
            insights["recommendations"].append({
                "priority": "Inmediata",
                "category": "🔥 Oportunidades Calientes",
                "action": f"Aprovechar el momento: {count} clientes están comprando más que nunca",
                "impact": f"🔥 Estos {count} clientes están en su mejor momento. Es AHORA cuando debemos actuar.",
                "next_steps": "Contactar esta semana con ofertas especiales. No esperar - el momento es perfecto"
            })

        # 🌱 Nuevos en Desarrollo
        # Si son más del 15%
        if category_distribution.get("🌱 Nuevos en Desarrollo", 0) > total_customers * 0.15:
            count = category_distribution.get("🌱 Nuevos en Desarrollo", 0)
            insights["recommendations"].append({
                "priority": "Media",
                "category": "🌱 Nuevos en Desarrollo",
                "action": f"Cultivar {count} clientes nuevos que muestran potencial",
                "impact": f"🌱 Estos {count} clientes están empezando bien. Si los cuidamos ahora, serán grandes compradores.",
                "next_steps": "Llamadas semanales, ofertas de bienvenida, mostrarles toda la gama de productos"
            })

        # ⚠️ Atención Urgente
        if category_distribution.get("⚠️ Atención Urgente", 0) > 0:
            count = category_distribution.get("⚠️ Atención Urgente", 0)
            insights["recommendations"].append({
                "priority": "Alta",
                "category": "⚠️ Atención Urgente",
                "action": f"Rescatar {count} clientes buenos que se están enfriando",
                "impact": f"⚠️ Estos {count} clientes compraban bien pero hace tiempo no aparecen. Todavía los podemos recuperar.",
                "next_steps": "Llamada personal esta semana. Preguntar qué necesitan, ofrecer promociones especiales"
            })

        # 🆘 Rescate Inmediato
        if category_distribution.get("🆘 Rescate Inmediato", 0) > 0:
            count = category_distribution.get("🆘 Rescate Inmediato", 0)
            revenue_critical = rfm_data[rfm_data['categoria_rfm']
                                        == "🆘 Rescate Inmediato"]['monetary'].sum()
            insights["recommendations"].append({
                "priority": "EMERGENCIA",
                "category": "🆘 Rescate Inmediato",
                "action": f"Última oportunidad: {count} clientes valiosos casi perdidos",
                "impact": f"🆘 {format_currency_int(revenue_critical)} en riesgo total. Estos eran clientes importantes - última chance.",
                "next_steps": "Gerente general debe intervenir. Reunión presencial, ofertas irresistibles, todo vale"
            })

        # 😴 Hibernando Estables
        # Si son más del 20%
        if category_distribution.get("😴 Hibernando Estables", 0) > total_customers * 0.2:
            count = category_distribution.get("😴 Hibernando Estables", 0)
            insights["recommendations"].append({
                "priority": "Media",
                "category": "😴 Hibernando Estables",
                "action": f"Despertar {count} clientes que están dormidos pero estables",
                "impact": f"😴 Estos {count} clientes no están comprando mucho pero tampoco se van. Oportunidad de activarlos.",
                "next_steps": "Campaña de reactivación suave: promociones estacionales, productos nuevos, recordatorios amigables"
            })

        # 💸 Perdidos
        lost_count = category_distribution.get("💸 Perdidos", 0)
        if lost_count > total_customers * 0.1:  # Si son más del 10%
            insights["recommendations"].append({
                "priority": "Baja",
                "category": "💸 Perdidos",
                "action": f"Último intento con {lost_count} clientes perdidos",
                "impact": f"💸 Estos {lost_count} clientes probablemente ya no volverán, pero vale la pena un último intento.",
                "next_steps": "Envío automático de ofertas especiales. Si no responden en 3 meses, enfocar energía en otros clientes"
            })

        # 🔄 Comportamiento Irregular
        if category_distribution.get("🔄 Comportamiento Irregular", 0) > 0:
            count = category_distribution.get("🔄 Comportamiento Irregular", 0)
            insights["recommendations"].append({
                "priority": "Media",
                "category": "🔄 Comportamiento Irregular",
                "action": f"Entender {count} clientes con patrones extraños de compra",
                "impact": f"🔄 Estos {count} clientes compran de forma impredecible. Necesitamos entender su patrón para venderles mejor.",
                "next_steps": "Analizar qué meses compran más, qué productos prefieren, adaptar ofertas a su ritmo"
            })

        # Si hay muchos clientes decreciendo
        declining_percentage = (
            insights["kpis"]["customers_declining"] / total_customers) * 100

        if declining_percentage > 25:
            insights["recommendations"].append({
                "priority": "ESTRATÉGICA",
                "category": "Análisis General",
                "action": f"Revisar estrategia: {declining_percentage:.1f}% de clientes están comprando menos",
                "impact": "🔍 Algo está pasando en el mercado o con nuestros productos. Necesitamos investigar las causas.",
                "next_steps": "Reunión urgente de equipo comercial. Revisar precios, competencia, calidad de servicio"
            })

        # Si el CAGR promedio es negativo
        if insights["kpis"]["avg_cagr"] < -5:
            insights["recommendations"].append({
                "priority": "ESTRATÉGICA",
                "category": "Análisis General",
                "action": f"Alerta general: clientes creciendo {insights['kpis']['avg_cagr']:.1f}% en promedio",
                "impact": "📉 El negocio está retrocediendo. La mayoría de clientes están comprando menos que antes.",
                "next_steps": "Análisis profundo: ¿problemas de precio? ¿competencia? ¿calidad? ¿servicio?"
            })

        # Si la recencia promedio es muy alta
        if insights["kpis"]["avg_recency"] > 90:
            insights["recommendations"].append({
                "priority": "OPERATIVA",
                "category": "Análisis General",
                "action": f"Problema de frecuencia: clientes tardan {insights['kpis']['avg_recency']:.0f} días promedio en volver",
                "impact": "⏰ Los clientes están tardando mucho en volver a comprar. Perdemos momentum.",
                "next_steps": "Implementar recordatorios automáticos, ofertas por tiempo sin comprar, seguimiento más activo"
            })

        return insights

    def load_cuotas_from_firebase(self, force_reload=False):
        """
        Cargar datos de cuotas desde Firebase con caché.
        """
        try:
            if not force_reload and hasattr(self, '_df_cuotas') and not self._df_cuotas.empty:
                return self._df_cuotas

            db = self._unified_analyzer._get_db()

            if not db:
                print("❌ [VentasAnalyzer] No se pudo obtener conexión para cuotas")
                return pd.DataFrame()

            # Cargar datos de cuotas
            data = db.get("cuotas_vendedores")

            if data:
                result = self.process_cuotas_data(data)

                # Guardar en caché
                self._df_cuotas = result
                self._last_cuotas_update = datetime.now()

                return result
            else:
                print(
                    "⚠️ [VentasAnalyzer] No se encontraron datos de cuotas en Firebase")
                self._df_cuotas = pd.DataFrame()
                return pd.DataFrame()

        except Exception as e:
            print(
                f"❌ [VentasAnalyzer] Error cargando cuotas desde Firebase: {e}")
            self._df_cuotas = pd.DataFrame()
            return pd.DataFrame()

    def process_cuotas_data(self, data):
        """
        Procesar datos de cuotas desde Firebase.
        """
        if not data:
            return pd.DataFrame()

        cuotas_list = []

        # Iterar sobre los meses
        for mes, vendedores_data in data.items():
            if isinstance(vendedores_data, dict):
                for vendedor, cuota in vendedores_data.items():
                    try:
                        cuotas_list.append({
                            'mes': mes,
                            'vendedor': vendedor,
                            'cuota': float(cuota) if cuota else 0
                        })
                    except (ValueError, TypeError):
                        continue

        df_cuotas = pd.DataFrame(
            cuotas_list) if cuotas_list else pd.DataFrame()

        if not df_cuotas.empty:
            # Convertir mes a formato datetime para facilitar comparaciones
            try:
                df_cuotas['fecha_mes'] = pd.to_datetime(
                    df_cuotas['mes'] + '-01', format='%Y%m-%d')
                df_cuotas['mes_nombre'] = df_cuotas['fecha_mes'].dt.strftime(
                    '%Y-%m')
            except:
                df_cuotas['mes_nombre'] = df_cuotas['mes']

        return df_cuotas

    def get_cumplimiento_cuotas(self, vendedor='Todos', mes='Todos'):
        """
        Obtener análisis de cumplimiento de cuotas con progreso esperado.
        CORREGIDO: Usa días hábiles, maneja ex-vendedores, y lógica de mes finalizado.
        """
        try:
            # Cargar cuotas
            df_cuotas = self.load_cuotas_from_firebase()

            if df_cuotas.empty:
                print("No hay datos de cuotas disponibles")
                return pd.DataFrame()

            # Obtener datos de ventas
            if vendedor == 'Todos':
                df_ventas_todos = pd.DataFrame()
                vendedores_con_cuotas = df_cuotas['vendedor'].unique().tolist()

                for v in vendedores_con_cuotas:
                    try:
                        ventas_vendedor = self.get_ventas_por_mes(v)
                        if not ventas_vendedor.empty:
                            ventas_vendedor['vendedor'] = v
                            df_ventas_todos = pd.concat(
                                [df_ventas_todos, ventas_vendedor], ignore_index=True)
                    except Exception as e:
                        print(f"Error obteniendo datos para vendedor {v}: {e}")
                        continue

                df_ventas = df_ventas_todos
            else:
                df_ventas = self.get_ventas_por_mes(vendedor)
                if not df_ventas.empty:
                    df_ventas['vendedor'] = vendedor

            if df_ventas.empty:
                print("No hay datos de ventas disponibles")
                return pd.DataFrame()

            # Determinar mes a analizar
            if mes == 'Todos':
                ultimo_mes = df_ventas['mes_nombre'].max()
            else:
                ultimo_mes = mes

            # Filtrar cuotas
            if vendedor != 'Todos':
                df_cuotas_filtrado = df_cuotas[df_cuotas['vendedor'] == vendedor]
            else:
                df_cuotas_filtrado = df_cuotas

            cuota_mes = df_cuotas_filtrado[df_cuotas_filtrado['mes_nombre'] == ultimo_mes]

            if cuota_mes.empty:
                return pd.DataFrame()

            # Calcular días hábiles
            try:
                fecha_mes = pd.to_datetime(ultimo_mes + '-01')
                año = fecha_mes.year
                mes_num = fecha_mes.month

                # Usar días hábiles en lugar de días calendario
                dias_habiles_mes, dias_habiles_transcurridos = calcular_dias_habiles_colombia(
                    año, mes_num)

                hoy = datetime.now()
                mes_finalizado = año < hoy.year or (
                    año == hoy.year and mes_num < hoy.month)

                if mes_finalizado:
                    dias_habiles_transcurridos = dias_habiles_mes
                else:
                    dias_habiles_transcurridos = \
                        max(0, dias_habiles_transcurridos - 1)

                # Progreso esperado basado en días hábiles
                progreso_esperado = (
                    dias_habiles_transcurridos / dias_habiles_mes * 100) if dias_habiles_mes > 0 else 100

            except Exception as e:
                print(f"Error calculando progreso esperado: {e}")
                progreso_esperado = 100
                dias_habiles_mes = 30
                dias_habiles_transcurridos = 30
                mes_finalizado = True

            # Construir resultado
            resultado = []

            if vendedor == 'Todos':
                for _, cuota_row in cuota_mes.iterrows():
                    vendedor_name = cuota_row['vendedor']
                    cuota_valor = cuota_row['cuota']

                    ventas_vendedor_mes = df_ventas[
                        (df_ventas['vendedor'] == vendedor_name) &
                        (df_ventas['mes_nombre'] == ultimo_mes)
                    ]

                    ventas_reales = ventas_vendedor_mes['valor_neto'].sum(
                    ) if not ventas_vendedor_mes.empty else 0

                    # CORREGIDO: Excluir vendedores con ventas en cero (ex-vendedores o nuevos sin actividad)
                    if ventas_reales == 0:
                        continue

                    cumplimiento_pct = (
                        ventas_reales / cuota_valor * 100) if cuota_valor > 0 else 0
                    meta_esperada = (cuota_valor * progreso_esperado / 100)
                    diferencia_cuota = ventas_reales - cuota_valor  # CORREGIDO: vs cuota total

                    # CORREGIDO: Estados según si el mes está finalizado
                    if mes_finalizado:
                        if cumplimiento_pct >= 100:
                            estado = "Cumplido"
                            color = "#22c55e"
                        else:
                            estado = "No Cumplió"
                            color = "#ef4444"
                    else:
                        if cumplimiento_pct >= 100:
                            estado = "Cumpliendo"
                            color = "#22c55e"
                        elif cumplimiento_pct >= progreso_esperado:
                            estado = "Adelantado"
                            color = "#3b82f6"
                        elif cumplimiento_pct >= (progreso_esperado - 10):
                            estado = "En Progreso"
                            color = "#f59e0b"
                        else:
                            estado = "Atrasado"
                            color = "#ef4444"

                    resultado.append({
                        'vendedor': vendedor_name,
                        'mes': ultimo_mes,
                        'cuota': cuota_valor,
                        'ventas_reales': ventas_reales,
                        'cumplimiento_pct': cumplimiento_pct,
                        'meta_esperada': meta_esperada,
                        'progreso_esperado_pct': progreso_esperado,
                        'diferencia_cuota': diferencia_cuota,
                        'dias_transcurridos': dias_habiles_transcurridos,
                        'dias_mes': dias_habiles_mes,
                        'estado': estado,
                        'color': color,
                        'mes_finalizado': mes_finalizado
                    })
            else:
                # Vendedor específico
                cuota_valor = cuota_mes['cuota'].iloc[0]
                ventas_mes = df_ventas[df_ventas['mes_nombre'] == ultimo_mes]
                ventas_reales = ventas_mes['valor_neto'].sum(
                ) if not ventas_mes.empty else 0

                cumplimiento_pct = (
                    ventas_reales / cuota_valor * 100) if cuota_valor > 0 else 0
                meta_esperada = (cuota_valor * progreso_esperado / 100)
                diferencia_cuota = ventas_reales - cuota_valor

                if mes_finalizado:
                    if cumplimiento_pct >= 100:
                        estado = "Cumplido"
                        color = "#22c55e"
                    else:
                        estado = "No Cumplió"
                        color = "#ef4444"
                else:
                    if cumplimiento_pct >= 100:
                        estado = "Cumpliendo"
                        color = "#22c55e"
                    elif cumplimiento_pct >= progreso_esperado:
                        estado = "Adelantado"
                        color = "#3b82f6"
                    elif cumplimiento_pct >= (progreso_esperado - 10):
                        estado = "En Progreso"
                        color = "#f59e0b"
                    else:
                        estado = "Atrasado"
                        color = "#ef4444"

                resultado.append({
                    'vendedor': vendedor,
                    'mes': ultimo_mes,
                    'cuota': cuota_valor,
                    'ventas_reales': ventas_reales,
                    'cumplimiento_pct': cumplimiento_pct,
                    'meta_esperada': meta_esperada,
                    'progreso_esperado_pct': progreso_esperado,
                    'diferencia_cuota': diferencia_cuota,
                    'dias_transcurridos': dias_habiles_transcurridos,
                    'dias_mes': dias_habiles_mes,
                    'estado': estado,
                    'color': color,
                    'mes_finalizado': mes_finalizado
                })

            return pd.DataFrame(resultado)

        except Exception as e:
            print(f"Error calculando cumplimiento de cuotas: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def get_cuotas_data(self, force_reload=False):
        """
        Acceso conveniente a datos de cuotas con auto-carga.
        """
        if not hasattr(self, '_df_cuotas') or self._df_cuotas.empty or force_reload:
            return self.load_cuotas_from_firebase(force_reload)

        return self._df_cuotas

    def get_resumen_mensual(self, vendedor='Todos'):
        """
        Get monthly sales summary with unique customers
        Using Get_Ventas_Por_mes for consistency with other graphics
        """
        try:
            # Obtener datos de ventas mensuales usando el método existente
            df_ventas_mes = self.get_ventas_por_mes(vendedor)

            if df_ventas_mes.empty:
                return pd.DataFrame()

            monthly_data = []

            for _, row in df_ventas_mes.iterrows():
                mes = row['mes_nombre']

                # Obtener datos detallados del mes para contar clientes
                df_mes_detalle = self.filter_data(vendedor, mes)

                if not df_mes_detalle.empty:
                    ventas_reales = \
                        df_mes_detalle[df_mes_detalle['tipo'].str.contains(
                            'Remision',
                            case=False,
                            na=False)
                        ]
                    devoluciones = \
                        df_mes_detalle[df_mes_detalle['tipo'].str.contains(
                            'Devolución|Devolucion',
                            case=False,
                            na=False)
                        ]

                    total_ventas = ventas_reales['valor_neto'].sum()
                    total_devoluciones = abs(devoluciones['valor_neto'].sum())
                    total_ventas_netas = total_ventas - total_devoluciones

                    # Contar clientes únicos
                    clientes_unicos = \
                        ventas_reales['cliente_completo'].nunique(
                        ) if not ventas_reales.empty else 0

                    num_transacciones = \
                        len(ventas_reales) if not ventas_reales.empty else 0

                    # Calcular promedios
                    ticket_promedio = total_ventas_netas / \
                        num_transacciones if num_transacciones > 0 else 0
                    venta_por_cliente = total_ventas_netas / \
                        clientes_unicos if clientes_unicos > 0 else 0
                else:
                    clientes_unicos = 0
                    num_transacciones = 0
                    ticket_promedio = 0
                    venta_por_cliente = 0

                # Crear fecha para ordenamiento
                try:
                    fecha = pd.to_datetime(mes + '-01')
                    mes_label = fecha.strftime('%b %Y')
                except:
                    fecha = pd.to_datetime(mes, format='%Y-%m')
                    mes_label = fecha.strftime('%b %Y')

                monthly_data.append({
                    'mes': mes_label,
                    'fecha': fecha,
                    'ventas_netas': row['valor_neto'],
                    'clientes_unicos': clientes_unicos,
                    'num_transacciones': num_transacciones,
                    'ticket_promedio': ticket_promedio,
                    'venta_por_cliente': venta_por_cliente
                })

            # Crear DataFrame y ordenar
            df = pd.DataFrame(monthly_data)
            df = df.sort_values('fecha')

            return df

        except Exception as e:
            print(f"Error en get_resumen_mensual: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def _calculate_enhanced_rfm_optimized(self, vendedor):
        """
        OPTIMIZED VERSION OF THE ORIGINAL RFM CALCULATION.
        """
        try:
            # CAMBIO 1: Calcular hasta el mes actual (no mes previo)
            hoy = datetime.now()

            fecha_corte = pd.Timestamp(hoy)

            # Obtener datos de ventas
            df = self.filter_data(vendedor, 'Todos')
            ventas_reales = df[df['tipo'].str.contains(
                'Remision', case=False, na=False)]
            ventas_reales = ventas_reales[ventas_reales['fecha']
                                          <= fecha_corte]

            if ventas_reales.empty:
                print(f"⚠️ No hay datos de ventas hasta {fecha_corte}")
                return pd.DataFrame()

            # OPTIMIZACIÓN: Cálculo vectorizado de métricas base
            rfm_data = ventas_reales.groupby('cliente_completo').agg({
                'fecha': ['max', 'min', 'count'],
                'documento_id': 'count',
                'valor_neto': ['sum', 'mean']
            }).reset_index()

            rfm_data.columns = ['cliente_completo', 'fecha_max', 'fecha_min', 'periodos_activos',
                                'frequency', 'monetary_total', 'monetary_promedio']

            rfm_data['recency_days'] = (
                fecha_corte - rfm_data['fecha_max']).dt.days

            # OPTIMIZACIÓN: Calcular tendencias en batch (no uno por uno)
            trend_data = self._calculate_client_trends_batch(
                ventas_reales, fecha_corte)

            # Merge con tendencias
            rfm_enhanced = pd.merge(
                rfm_data, trend_data, on='cliente_completo', how='left')

            # Rellenar valores faltantes con defaults
            rfm_enhanced['cagr_6m'] = rfm_enhanced['cagr_6m'].fillna(0)
            rfm_enhanced['variacion_3m'] = rfm_enhanced['variacion_3m'].fillna(
                0)
            rfm_enhanced['variacion_reciente'] = rfm_enhanced['variacion_reciente'].fillna(
                0)
            rfm_enhanced['tendencia_general'] = rfm_enhanced['tendencia_general'].fillna(
                'estable')
            rfm_enhanced['meses_activos'] = rfm_enhanced['meses_activos'].fillna(
                1)
            rfm_enhanced['consistencia'] = rfm_enhanced['consistencia'].fillna(
                0)

            # Filtrar valores válidos
            rfm_enhanced = rfm_enhanced[
                (rfm_enhanced['recency_days'] >= 0) &
                (rfm_enhanced['frequency'] > 0) &
                (rfm_enhanced['monetary_total'] > 0)
            ]

            if rfm_enhanced.empty:
                return pd.DataFrame()

            # Calcular scores RFM tradicionales
            try:
                # RECENCY: Menos días = mejor score
                rfm_enhanced['R'] = pd.qcut(rfm_enhanced['recency_days'],
                                            q=5, labels=[5, 4, 3, 2, 1], duplicates='drop')

                # FREQUENCY: Más transacciones = mejor score
                rfm_enhanced['F'] = pd.qcut(rfm_enhanced['frequency'].rank(method='first'),
                                            q=5, labels=[1, 2, 3, 4, 5], duplicates='drop')

                # MONETARY: Más valor = mejor score
                rfm_enhanced['M'] = pd.qcut(rfm_enhanced['monetary_total'].rank(method='first'),
                                            q=5, labels=[1, 2, 3, 4, 5], duplicates='drop')

            except:
                # Fallback con cut si qcut falla
                rfm_enhanced['R'] = pd.cut(rfm_enhanced['recency_days'],
                                           bins=5, labels=[5, 4, 3, 2, 1], duplicates='drop')
                rfm_enhanced['F'] = pd.cut(rfm_enhanced['frequency'],
                                           bins=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
                rfm_enhanced['M'] = pd.cut(rfm_enhanced['monetary_total'],
                                           bins=5, labels=[1, 2, 3, 4, 5], duplicates='drop')

            # TREND Score basado en CAGR y variaciones (mantener lógica original)
            rfm_enhanced['T'] = rfm_enhanced.apply(
                self._calculate_trend_score, axis=1)

            # Convertir a enteros
            for col in ['R', 'F', 'M', 'T']:
                rfm_enhanced[col] = pd.to_numeric(
                    rfm_enhanced[col], errors='coerce').fillna(3).astype(int)

            # Crear RFM+ Score combinado
            rfm_enhanced['rfm_score'] = (
                rfm_enhanced['R'].astype(str) +
                rfm_enhanced['F'].astype(str) +
                rfm_enhanced['M'].astype(str) +
                rfm_enhanced['T'].astype(str)
            )

            # Calcular RFM+ Score numérico ponderado
            rfm_enhanced['rfm_numeric'] = (
                rfm_enhanced['R'] * 0.30 +
                rfm_enhanced['F'] * 0.25 +
                rfm_enhanced['M'] * 0.25 +
                rfm_enhanced['T'] * 0.20
            )

            # Categorizar clientes usando TODAS las categorías originales
            rfm_enhanced['categoria_rfm'] = rfm_enhanced.apply(
                self._categorize_enhanced_rfm, axis=1)

            # Información adicional
            rfm_enhanced['valor_promedio_transaccion'] = (
                rfm_enhanced['monetary_total'] / rfm_enhanced['frequency']
            )

            # Renombrar para compatibilidad
            rfm_enhanced.rename(columns={
                'monetary_total': 'monetary',
                'fecha_max': 'fecha'
            }, inplace=True)

            return rfm_enhanced

        except Exception as e:
            print(f"❌ Error calculando RFM optimizado: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def _calculate_client_trends_batch(self, ventas_data, fecha_corte):
        """
        Calcular tendencias para TODOS los clientes de forma eficiente
        """
        try:
            # Preparar datos mensuales para todos los clientes de una vez
            ventas_data = ventas_data.copy()
            ventas_data['mes_periodo'] = ventas_data['fecha'].dt.to_period('M')

            # Agrupar por cliente y mes
            monthly_sales = ventas_data.groupby(['cliente_completo', 'mes_periodo'])[
                'valor_neto'].sum().reset_index()

            # Lista para resultados
            trend_results = []

            # Procesar cada cliente
            for cliente in monthly_sales['cliente_completo'].unique():
                client_data = monthly_sales[monthly_sales['cliente_completo'] == cliente]
                client_data = client_data.set_index(
                    'mes_periodo')['valor_neto'].sort_index()

                # Usar el método original _calculate_client_trends pero sin el filtrado inicial
                trend_metrics = self._calculate_client_trends_from_series(
                    cliente, client_data, fecha_corte
                )
                trend_results.append(trend_metrics)

            return pd.DataFrame(trend_results)

        except Exception as e:
            print(f"❌ Error en cálculo batch de tendencias: {e}")
            return pd.DataFrame()

    def _calculate_client_trends_from_series(self, cliente, monthly_sales, fecha_corte):
        """
        Calculate trend metrics from a monthly series
        Cag from January to the last closed month.
        """
        try:
            if len(monthly_sales) < 2:
                return {
                    'cliente_completo': cliente,
                    'cagr_6m': 0,
                    'variacion_3m': 0,
                    'variacion_reciente': 0,
                    'tendencia_general': 'estable',
                    'meses_activos': 1,
                    'consistencia': 0
                }

            # Convertir fecha_corte a period
            if hasattr(fecha_corte, 'to_period'):
                ultimo_periodo_completo = fecha_corte.to_period('M')
            else:
                ultimo_periodo_completo = pd.Timestamp(
                    fecha_corte).to_period('M')

            # Filtrar hasta el último período completo
            monthly_sales = monthly_sales[monthly_sales.index <=
                                          ultimo_periodo_completo]

            if len(monthly_sales) < 2:
                return {
                    'cliente_completo': cliente,
                    'cagr_6m': 0,
                    'variacion_3m': 0,
                    'variacion_reciente': 0,
                    'tendencia_general': 'estable',
                    'meses_activos': 1,
                    'consistencia': 0
                }

            # CAMBIO 2: CAGR desde enero del año actual hasta último mes cerrado
            current_year = fecha_corte.year
            enero_period = pd.Period(f'{current_year}-01', freq='M')

            # Filtrar datos desde enero del año actual
            year_data = monthly_sales[monthly_sales.index >= enero_period]

            if len(year_data) >= 2:
                primer_valor = year_data.iloc[0]
                ultimo_valor = year_data.iloc[-1]
                periodos = len(year_data) - 1

                if primer_valor > 0 and periodos > 0:
                    cagr_6m = ((ultimo_valor / primer_valor)
                               ** (1/periodos) - 1) * 100
                else:
                    cagr_6m = 0
            else:
                # Si no hay suficientes datos del año actual, usar los últimos meses disponibles
                meses_disponibles = len(monthly_sales)
                meses_cagr = min(6, meses_disponibles)
                recent_months = monthly_sales.tail(meses_cagr)

                if len(recent_months) >= 2:
                    primer_valor = recent_months.iloc[0]
                    ultimo_valor = recent_months.iloc[-1]
                    periodos = len(recent_months) - 1

                    if primer_valor > 0 and periodos > 0:
                        cagr_6m = ((ultimo_valor / primer_valor)
                                   ** (1/periodos) - 1) * 100
                    else:
                        cagr_6m = 0
                else:
                    cagr_6m = 0

            # CAMBIO 3: Variación de últimos 3 meses vs 3 meses anteriores (solo meses cerrados)
            if len(monthly_sales) >= 6:
                # Usar solo meses cerrados para el cálculo
                meses_cerrados = monthly_sales[monthly_sales.index <
                                               ultimo_periodo_completo]

                if len(meses_cerrados) >= 6:
                    ultimos_3m = meses_cerrados.tail(3).sum()
                    anteriores_3m = meses_cerrados.tail(6).head(3).sum()

                    if anteriores_3m > 0:
                        variacion_3m = (
                            (ultimos_3m - anteriores_3m) / anteriores_3m) * 100
                    else:
                        variacion_3m = 100 if ultimos_3m > 0 else 0
                else:
                    variacion_3m = 0
            else:
                variacion_3m = 0

            # 3. Variación del último mes vs promedio anterior
            if len(monthly_sales) >= 3:
                ultimo_mes = monthly_sales.iloc[-1]
                promedio_anterior = monthly_sales.iloc[:-1].mean()

                if promedio_anterior > 0:
                    variacion_reciente = (
                        (ultimo_mes - promedio_anterior) / promedio_anterior) * 100
                else:
                    variacion_reciente = 100 if ultimo_mes > 0 else 0
            else:
                variacion_reciente = 0

            # 4. Tendencia general
            if cagr_6m > 10 and variacion_3m > 5:
                tendencia_general = 'crecimiento_fuerte'
            elif cagr_6m > 0 and variacion_3m >= 0:
                tendencia_general = 'crecimiento'
            elif cagr_6m < -10 and variacion_3m < -5:
                tendencia_general = 'decrecimiento_fuerte'
            elif cagr_6m < 0 and variacion_3m < 0:
                tendencia_general = 'decrecimiento'
            else:
                tendencia_general = 'estable'

            # 5. Consistencia
            if len(monthly_sales) >= 3:
                cv = (monthly_sales.std() / monthly_sales.mean()) * \
                    100 if monthly_sales.mean() > 0 else 100
                consistencia = max(0, 100 - cv)
            else:
                consistencia = 50

            return {
                'cliente_completo': cliente,
                'cagr_6m': round(cagr_6m, 2),
                'variacion_3m': round(variacion_3m, 2),
                'variacion_reciente': round(variacion_reciente, 2),
                'tendencia_general': tendencia_general,
                'meses_activos': len(monthly_sales),
                'consistencia': round(consistencia, 1)
            }

        except Exception as e:
            print(f"❌ Error calculando tendencias para {cliente}: {e}")
            return {
                'cliente_completo': cliente,
                'cagr_6m': 0,
                'variacion_3m': 0,
                'variacion_reciente': 0,
                'tendencia_general': 'estable',
                'meses_activos': 1,
                'consistencia': 0
            }

    def get_client_rfm_details(self, cliente, vendedor='Todos'):
        """
        Obtener detalles RFM+ para un cliente específico USANDO CACHE
        """
        try:
            # Primero intentar obtener del cache
            cache_key = f"rfm_{vendedor}"
            current_time = datetime.now()

            if (cache_key in self._rfm_cache and
                self._rfm_cache_timestamp and
                    (current_time - self._rfm_cache_timestamp).seconds < self._rfm_cache_ttl):

                rfm_data = self._rfm_cache[cache_key]
                client_data = rfm_data[rfm_data['cliente_completo'] == cliente]

                if not client_data.empty:
                    client_info = client_data.iloc[0]
                    return self._format_client_rfm_details(client_info)

            # Si no está en cache, calcular TODO y cachear
            rfm_data = \
                self.calculate_enhanced_rfm_scores(
                    vendedor,
                    use_cache=True
                )

            if rfm_data.empty:
                return None

            # Buscar cliente específico
            client_data = rfm_data[rfm_data['cliente_completo'] == cliente]

            if client_data.empty:
                return None

            client_info = client_data.iloc[0]
            return self._format_client_rfm_details(client_info)

        except Exception as e:
            print(f"❌ Error obteniendo detalles RFM para {cliente}: {e}")
            return None

    def _format_client_rfm_details(self, client_info):
        """
        Formatear detalles del cliente desde el DataFrame RFM
        """
        return {
            'cliente': client_info['cliente_completo'],
            'categoria': client_info['categoria_rfm'],
            'rfm_score': client_info['rfm_score'],
            'rfm_numeric': round(client_info['rfm_numeric'], 2),
            'scores': {
                'recency': int(client_info['R']),
                'frequency': int(client_info['F']),
                'monetary': int(client_info['M']),
                'trend': int(client_info['T'])
            },
            'metricas': {
                'dias_ultima_compra': int(client_info['recency_days']),
                'total_compras': int(client_info['frequency']),
                'valor_total': client_info['monetary'],
                'valor_promedio': client_info['valor_promedio_transaccion'],
                'meses_activos': int(client_info['meses_activos'])
            },
            'tendencias': {
                'cagr_6m': client_info['cagr_6m'],
                'variacion_3m': client_info['variacion_3m'],
                'variacion_reciente': client_info['variacion_reciente'],
                'tendencia_general': client_info['tendencia_general'],
                'consistencia': client_info['consistencia']
            },
            'recomendacion': self._get_client_recommendation(client_info)
        }

    def clear_rfm_cache(self):
        """
        Método para limpiar el cache manualmente si es necesario
        """
        self._rfm_cache = {}
        self._rfm_cache_timestamp = None
        print("🗑️ Cache RFM limpiado")

    def load_fletes_from_firebase(self, force_reload=False):
        """
        Load freight and conveyor data from Firebase.
        """
        try:
            if not force_reload and hasattr(self, '_df_fletes') and not self._df_fletes.empty:
                return self._df_fletes

            db = self._unified_analyzer._get_db()

            if not db:
                print("❌ No se pudo obtener conexión para fletes")
                return pd.DataFrame()

            data = db.get("fletes_transportadoras")

            if data:
                fletes_list = []

                for flete_id, flete_info in data.items():
                    fletes_list.append({
                        'ciudad': flete_info.get('ciudad', ''),
                        'depto': flete_info.get('depto', ''),
                        'transportadora': flete_info.get('transportadora', ''),
                        'valor_flete_unidad': flete_info.get('valor_flete_unidad', 0),
                        'valor_pedido_minimo': flete_info.get('valor_pedido_minimo', 0),
                        'zona': flete_info.get('zona', '')
                    })

                df_fletes = pd.DataFrame(fletes_list)

                # Agrupar por ciudad
                df_grouped = df_fletes.groupby(['ciudad', 'depto', 'zona']).agg({
                    'transportadora': lambda x: list(x),
                    'valor_flete_unidad': 'min',  # Mostrar el valor mínimo
                    'valor_pedido_minimo': 'min'   # Mostrar el pedido mínimo
                }).reset_index()

                self._df_fletes = df_grouped
                return df_grouped
            else:
                print("⚠️ No se encontraron datos de fletes")
                self._df_fletes = pd.DataFrame()
                return pd.DataFrame()

        except Exception as e:
            print(f"❌ Error cargando fletes: {e}")
            return pd.DataFrame()

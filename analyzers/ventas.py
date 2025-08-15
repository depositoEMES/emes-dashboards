import time
from datetime import datetime
from typing import List

import pandas as pd
from pandas.core.frame import DataFrame

class VentasAnalyzer:
    
    def __init__(self) -> None:
        """
        Constructor.
        """
        from . import get_unified_analyzer
        self._unified_analyzer = get_unified_analyzer()
    
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
        """Compatibilidad: retorna la lista de meses."""
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
        ventas_reales = df[df['tipo'].str.contains('Remision', case=False, na=False)]

        if ventas_reales.empty:
            return pd.DataFrame()

        resultado = ventas_reales.groupby('forma_pago').agg({
            'valor_neto': 'sum',
            'documento_id': 'count'
        }).reset_index()

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
        cliente_data['fecha_str'] = cliente_data['fecha'].dt.strftime('%Y-%m-%d')

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
                    ventas_reales['fecha'] <= mes_limite + pd.offsets.MonthEnd(0)
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

        resultado.rename(columns={'cliente_completo': 'clientes_impactados'}, inplace=True)
        resultado = resultado.sort_values('mes_nombre')

        # Calculate percentages
        if not df_total_clientes.empty:
            df_total_clientes_filtrado = df_total_clientes[
                df_total_clientes['vendedor'] != 'MONICA YANET DUQUE'
            ]
            
            if vendedor == 'Todos':
                total_clientes_disponibles = df_total_clientes_filtrado['total_clientes'].sum()
            else:
                vendor_data = df_total_clientes_filtrado[df_total_clientes_filtrado['vendedor'] == vendedor]
                total_clientes_disponibles = vendor_data['total_clientes'].sum() if not vendor_data.empty else 0
        else:
            total_clientes_disponibles = 0

        # Calculate average percentage of impacted clients
        if total_clientes_disponibles > 0 and not resultado.empty:
            promedio_impactados = resultado['clientes_impactados'].mean()
            porcentaje_promedio = (promedio_impactados / total_clientes_disponibles * 100)
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
    
    def get_ventas_por_rango_fechas(self, vendedor='Todos', fecha_inicio=None, fecha_fin=None):
        """
        Get sales data for date range with monthly breakdown per client.
        """        
        try:
            # Filter by vendor
            df = self.filter_data(vendedor, 'Todos')
            
            # Filter only sales (exclude returns, credit notes, etc.)
            ventas_reales = df[df['tipo'].str.contains('Remision', case=False, na=False)]
            
            if ventas_reales.empty:
                return pd.DataFrame()
            
            # Apply date range filter - INCLUIR MES COMPLETO
            if fecha_inicio and fecha_fin:
                # Asegurar que incluye el mes completo
                fecha_inicio_mes = fecha_inicio.replace(day=1)  # Primer día del mes
                # Último día del mes final
                if fecha_fin.month == 12:
                    fecha_fin_mes = fecha_fin.replace(year=fecha_fin.year + 1, month=1, day=1) - pd.Timedelta(days=1)
                else:
                    fecha_fin_mes = fecha_fin.replace(month=fecha_fin.month + 1, day=1) - pd.Timedelta(days=1)
                
                ventas_reales = ventas_reales[
                    (ventas_reales['fecha'] >= fecha_inicio_mes) & 
                    (ventas_reales['fecha'] <= fecha_fin_mes)
                ]
            
            if ventas_reales.empty:
                return pd.DataFrame()
            
            # Create month-year column for grouping
            ventas_reales['mes_año'] = ventas_reales['fecha'].dt.strftime('%Y-%m')
            
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
        ventas_reales = df_ventas[df_ventas['tipo'].str.contains('Remision', case=False, na=False)]

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
        ventas_por_nit['valor_neto'] = ventas_por_nit['valor_bruto'] - ventas_por_nit['descuento']

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
            ventas_reales['mes_año'] = ventas_reales['fecha'].dt.strftime('%Y-%m')
            
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
                clientes_filtrados = resultado_total['cliente_completo'].tolist()
                ventas_reales = ventas_reales[ventas_reales['cliente_completo'].isin(clientes_filtrados)]
            
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
            recibo_row = {
                'recibo_id': recibo_id,
                'id1': recibo_info.get('id1', ''),
                'valor_recibo': float(recibo_info.get('valor_recibo', 0) or 0),
                'vendedor': recibo_info.get('vendedor', ''),
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
    
    def load_num_clientes_from_firebase(self, force_reload=False):
        """
        Load num_clientes_por_vendedor data from Firebase database with caching.

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

            data = db.get("num_clientes_por_vendedor")

            if data:
                result = self.process_num_clientes_data(data)

                # Guardar en cache
                self._unified_analyzer._df_num_clientes = result
                self._last_num_clientes_update = datetime.now()

                load_time = time.time() - start_time

                return result
            else:
                print(
                    "⚠️ [VentasAnalyzer] No num_clientes_por_vendedor data found in Firebase")

                self._unified_analyzer._df_num_clientes = pd.DataFrame()

                return pd.DataFrame()

        except Exception as e:
            print(
                f"❌ [VentasAnalyzer] Error loading num_clientes_por_vendedor data from Firebase: {e}")

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
            ventas_reales = df[df['tipo'].str.contains('Remision', case=False, na=False)]
            
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
            ventas_reales['mes_año'] = ventas_reales['fecha'].dt.strftime('%Y-%m')
            
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
                    elif actual > 0 and anterior == 0:  # Nueva venta (antes no había)
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
        
    def get_clientes_con_variaciones(self, vendedor='Todos', mes_inicio=1, mes_fin=12):
        """Obtener lista de clientes (URLs) que tienen variaciones en el período"""
        try:
            df = self.filter_data(vendedor, 'Todos')
            ventas_reales = df[df['tipo'].str.contains('Remision', case=False, na=False)]
            
            if ventas_reales.empty:
                return []
            
            # Filtrar por rango de meses
            ventas_reales = ventas_reales[
                (ventas_reales['fecha'].dt.month >= mes_inicio) & 
                (ventas_reales['fecha'].dt.month <= mes_fin)
            ]
            
            if ventas_reales.empty:
                return []
            
            # Crear mes_año para agrupación
            ventas_reales['mes_año'] = ventas_reales['fecha'].dt.strftime('%Y-%m')
            
            # Obtener URLs que tienen ventas en al menos 2 meses diferentes
            urls_por_mes = ventas_reales.groupby('url')['mes_año'].nunique()
            urls_con_variaciones = urls_por_mes[urls_por_mes >= 2].index.tolist()
            
            return urls_con_variaciones
            
        except Exception as e:
            print(f"❌ Error obteniendo clientes con variaciones: {e}")
            return []

    def get_variaciones_clientes_especificos(self, vendedor='Todos', mes_inicio=1, mes_fin=12, clientes_seleccionados=[]):
        """Obtener variaciones para clientes específicos seleccionados"""
        try:
            if not clientes_seleccionados:
                return pd.DataFrame()
            
            # Obtener datos base
            df = self.filter_data(vendedor, 'Todos')
            ventas_reales = df[df['tipo'].str.contains('Remision', case=False, na=False)]
            
            if ventas_reales.empty:
                return pd.DataFrame()
            
            # Filtrar por clientes seleccionados
            ventas_reales = ventas_reales[ventas_reales['url'].isin(clientes_seleccionados)]
            
            # Filtrar por rango de meses
            ventas_reales = ventas_reales[
                (ventas_reales['fecha'].dt.month >= mes_inicio) & 
                (ventas_reales['fecha'].dt.month <= mes_fin)
            ]
            
            if ventas_reales.empty:
                return pd.DataFrame()
            
            # Crear mes_año para agrupación
            ventas_reales['mes_año'] = ventas_reales['fecha'].dt.strftime('%Y-%m')
            
            # Agrupar por URL y mes
            resultado = ventas_reales.groupby(['url', 'mes_año']).agg({
                'valor_neto': 'sum'
            }).reset_index()
            
            # Crear tabla pivote
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
                
                ventas_anterior = pivot_table[mes_anterior]
                ventas_actual = pivot_table[mes_actual]
                
                variacion = pd.Series(index=pivot_table.index, dtype=float)
                
                for url in pivot_table.index:
                    anterior = ventas_anterior[url]
                    actual = ventas_actual[url]
                    
                    if anterior > 0:
                        variacion[url] = ((actual - anterior) / anterior) * 100
                    elif actual > 0 and anterior == 0:
                        variacion[url] = 100.0
                    else:
                        variacion[url] = 0.0
                
                # Crear nombre de columna
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
            
            return variaciones
            
        except Exception as e:
            print(f"❌ Error en variaciones clientes específicos: {e}")
            return pd.DataFrame()
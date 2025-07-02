import pandas as pd
from datetime import datetime


class VentasAnalyzer:

    def __init__(self):
        """
        Initialize the VentasAnalyzer with empty dataframes.
        """
        self.df_ventas = pd.DataFrame()
        self.vendedores_list = ['Todos']
        self.meses_list = ['Todos']

    def _get_db(self):
        """
        Get database instance.
        """
        from server import get_db

        return get_db()

    def load_data_from_firebase(self):
        """
        Load data from Firebase database.
        """
        try:
            db = self._get_db()
            data = db.get("ventas_vendedor")

            if data:
                return self.process_data(data)
            else:
                print("No sales data found in Firebase")
                return pd.DataFrame()
        except Exception as e:
            print(f"Error loading sales data from Firebase: {e}")
            return pd.DataFrame()

    def process_data(self, data):
        """
        Process raw sales data and create DataFrame.
        """
        if not data:
            return pd.DataFrame()

        ventas_list = []

        for vendedor_nombre, documentos in data.items():
            for doc_id, doc_info in documentos.items():
                doc_row = {
                    'vendedor': vendedor_nombre,
                    'documento_id': doc_id,
                    'cliente': doc_info.get('cliente', ''),
                    'url': doc_info.get('url', ''),
                    'nit': doc_info.get('nit', ''),
                    'fecha': doc_info.get('fecha', ''),
                    'tipo': doc_info.get('tipo', ''),
                    'valor_bruto': float(doc_info.get('valor_bruto', 0) or 0),
                    'descuento': float(doc_info.get('descuento', 0) or 0),
                    'iva': float(doc_info.get('iva', 0) or 0),
                    'forma_pago': doc_info.get('forma_pago', 'No Definida'),
                    'zona': doc_info.get('zona', ''),
                    'subzona': doc_info.get('subzona', ''),
                    'cupo_credito': float(doc_info.get('cupo_credito', 0) or 0)
                }
                ventas_list.append(doc_row)

        if not ventas_list:
            return pd.DataFrame()

        self.df_ventas = pd.DataFrame(ventas_list)

        # Process dates
        self.df_ventas['fecha'] = pd.to_datetime(
            self.df_ventas['fecha'], errors='coerce')

        # Extract month-year for filtering
        self.df_ventas['año_mes'] = self.df_ventas['fecha'].dt.to_period('M')
        self.df_ventas['mes_nombre'] = self.df_ventas['fecha'].dt.strftime(
            '%Y-%m')

        # Calculate net value (valor_bruto - descuento)
        self.df_ventas['valor_neto'] = self.df_ventas['valor_bruto'] - \
            self.df_ventas['descuento']

        # Create combined client name
        self.df_ventas['cliente_completo'] = self.df_ventas.apply(
            lambda row: f"{row['cliente']} – {row['url']}" if row['url'] and row['url'].strip() else row['cliente'], axis=1
        )

        # Create vendedores list
        vendedores_unicos = self.df_ventas['vendedor'].dropna().unique()
        self.vendedores_list = ['Todos'] + sorted(vendedores_unicos)

        # Create months list
        meses_unicos = self.df_ventas['mes_nombre'].dropna().unique()
        self.meses_list = ['Todos'] + sorted(meses_unicos, reverse=True)

        return self.df_ventas

    def filter_data(self, vendedor='Todos', mes='Todos'):
        """
        Filter data by salesperson and month.
        """
        df = self.df_ventas.copy()

        if vendedor != 'Todos':
            df = df[df['vendedor'] == vendedor]

        if mes != 'Todos':
            df = df[df['mes_nombre'] == mes]

        return df

    def get_resumen_ventas(self, vendedor='Todos', mes='Todos'):
        """
        Get sales summary statistics.
        """
        df = self.filter_data(vendedor, mes)

        # Filter only sales (exclude credit notes, returns, etc.)
        ventas_reales = df[df['tipo'].str.contains(
            'Remision|Factura', case=False, na=False)]
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
            'num_clientes': ventas_reales['cliente'].nunique() if not ventas_reales.empty else 0,
            'num_devoluciones': len(devoluciones),
            'ticket_promedio': total_ventas / len(ventas_reales) if len(ventas_reales) > 0 else 0,
            'total_descuentos': abs(ventas_reales['descuento'].sum()),
            'porcentaje_descuento': (abs(ventas_reales['descuento'].sum()) / ventas_reales['valor_bruto'].sum() * 100) if ventas_reales['valor_bruto'].sum() > 0 else 0
        }

    def get_ventas_por_mes(self, vendedor='Todos'):
        """
        Get sales evolution by month.
        """
        df = self.filter_data(vendedor, 'Todos')

        ventas_reales = df[df['tipo'].str.contains(
            'Remision|Factura', case=False, na=False)]

        if ventas_reales.empty:
            return pd.DataFrame()

        resultado = ventas_reales.groupby('mes_nombre').agg({
            'valor_neto': 'sum',
            'documento_id': 'count'
        }).reset_index()

        resultado = resultado.sort_values('mes_nombre')

        return resultado

    def get_ventas_por_dia_semana(self, vendedor='Todos', mes='Todos'):
        """
        Get sales distribution by day of week for seasonality analysis.
        """
        df = self.filter_data(vendedor, mes)
        ventas_reales = df[df['tipo'].str.contains(
            'Remision|Factura', case=False, na=False)]

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
        resultado = resultado.sort_values('dia_semana_es')

        return resultado

    def load_convenios_from_firebase(self):
        """
        Load convenios data from Firebase database.
        """
        try:
            db = self._get_db()
            data = db.get("convenios")

            if data:
                return self.process_convenios_data(data)
            else:
                print("No convenios data found in Firebase")
                return pd.DataFrame()
        except Exception as e:
            print(f"Error loading convenios data from Firebase: {e}")
            return pd.DataFrame()

    def process_convenios_data(self, data):
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

        df_convenios = \
            pd.DataFrame(convenios_list) if convenios_list else pd.DataFrame()

        # Filter only confirmed agreements
        if not df_convenios.empty:
            df_convenios = df_convenios[df_convenios['estado'] == 'Confirmado']

        return df_convenios

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
            'Remision|Factura', case=False, na=False)]

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
        resultado['progreso_esperado_pct'] = round(
            days_elapsed / days_in_year * 100, 2)

        return resultado

    def load_recibos_from_firebase(self):
        """
        Load recibos_caja data from Firebase database.
        """
        try:
            db = self._get_db()
            data = db.get("recibos_caja")

            if data:
                return self.process_recibos_data(data)
            else:
                print("No recibos_caja data found in Firebase")
                return pd.DataFrame()
        except Exception as e:
            print(f"Error loading recibos_caja data from Firebase: {e}")
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

    def load_num_clientes_from_firebase(self):
        """
        Load num_clientes_por_vendedor data from Firebase database.
        """
        try:
            db = self._get_db()
            data = db.get("num_clientes_por_vendedor")

            if data:
                return self.process_num_clientes_data(data)
            else:
                print("No num_clientes_por_vendedor data found in Firebase")
                return pd.DataFrame()
        except Exception as e:
            print(
                f"Error loading num_clientes_por_vendedor data from Firebase: {e}")
            return pd.DataFrame()

    def process_num_clientes_data(self, data):
        """
        Process num_clientes_por_vendedor data.
        """
        if not data:
            return pd.DataFrame()

        clientes_list = []
        for vendedor, num_clientes in data.items():
            clientes_row = {
                'vendedor': vendedor,
                'total_clientes': int(num_clientes or 0)
            }
            clientes_list.append(clientes_row)

        return pd.DataFrame(clientes_list) if clientes_list else pd.DataFrame()

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

    def get_recaudo_por_vendedor(self):
        """
        Get collection summary by vendor.
        """
        df_recibos = self.load_recibos_from_firebase()
        if df_recibos.empty:
            return pd.DataFrame(), 0

        total_recaudo = df_recibos['valor_recibo'].sum()

        resultado = df_recibos.groupby('vendedor').agg({
            'valor_recibo': 'sum',
            'recibo_id': 'count'
        }).reset_index()

        return resultado, total_recaudo

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

    def get_ventas_por_zona(self, vendedor='Todos', mes='Todos'):
        """
        Get sales distribution by zone.
        """
        df = self.filter_data(vendedor, mes)
        ventas_reales = df[df['tipo'].str.contains(
            'Remision|Factura', case=False, na=False)]

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
        ventas_reales = df[df['tipo'].str.contains(
            'Remision|Factura', case=False, na=False)]

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
            'Remision|Factura', case=False, na=False)]

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
        ventas_reales = df[df['tipo'].str.contains(
            'Remision|Factura', case=False, na=False)]

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
        ventas_reales = df[df['tipo'].str.contains(
            'Remision|Factura', case=False, na=False)]

        if ventas_reales.empty:
            return ['Seleccione un cliente']

        clientes = ventas_reales['cliente_completo'].unique()
        return ['Seleccione un cliente'] + sorted(clientes)

    def get_evolucion_cliente(self, cliente, vendedor='Todos'):
        """
        Get client's sales evolution by day.
        """
        df = self.filter_data(vendedor, 'Todos')

        ventas_reales = df[df['tipo'].str.contains(
            'Remision|Factura', case=False, na=False)]

        if ventas_reales.empty or cliente == 'Seleccione un cliente':
            return pd.DataFrame()

        cliente_data = \
            ventas_reales[ventas_reales['cliente_completo'] == cliente]

        if cliente_data.empty:
            return pd.DataFrame()

        # Group by date instead of month
        cliente_data['fecha_str'] = cliente_data['fecha'].dt.strftime(
            '%Y-%m-%d')

        resultado = cliente_data.groupby('fecha_str').agg({
            'valor_neto': 'sum',
            'documento_id': 'count'
        }).reset_index()

        resultado = resultado.sort_values('fecha_str')

        return resultado

    def get_ventas_acumuladas_mes(self, mes='Todos', vendedor='Todos'):
        """
        Get accumulated sales up to selected month for all clients.
        """
        df = self.filter_data(vendedor, 'Todos')
        ventas_reales = df[df['tipo'].str.contains(
            'Remision|Factura', case=False, na=False)]

        if ventas_reales.empty:
            return pd.DataFrame()

        # If specific month selected, filter up to that month
        if mes != 'Todos':
            # Convert mes to datetime for comparison
            try:
                mes_limite = pd.to_datetime(mes + '-01')
                ventas_reales = ventas_reales[ventas_reales['fecha']
                                              <= mes_limite + pd.offsets.MonthEnd(0)]
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

        ventas_reales = df[df['tipo'].str.contains(
            'Remision|Factura', case=False, na=False)]

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
            if vendedor == 'Todos':
                total_clientes_disponibles = df_total_clientes['total_clientes'].sum(
                )
            else:
                vendor_data = df_total_clientes[df_total_clientes['vendedor'] == vendedor]
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
        Get days without sales for each client - NEW METHOD for treemap.
        """
        df = self.filter_data(vendedor, 'Todos')
        ventas_reales = df[df['tipo'].str.contains(
            'Remision|Factura', case=False, na=False)]

        if ventas_reales.empty:
            return pd.DataFrame()

        # Get last sale date for each client
        ultima_venta = ventas_reales.groupby('cliente_completo').agg({
            'fecha': 'max',
            'valor_neto': 'sum',
            'documento_id': 'count'
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
        resultado = resultado.sort_values('dias_sin_venta', ascending=False)

        return resultado

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

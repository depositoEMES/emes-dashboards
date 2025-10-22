import time
import numpy as np
import pandas as pd
from datetime import datetime


class CarteraAnalyzer:

    def __init__(self):
        """
        Initialize the CarteraAnalyzer with empty dataframes and default values.
        """
        self.df_documentos = pd.DataFrame()
        self.vendedores_list = ['Todos']
        self._last_update = None

    def reload_data(self):
        """
        Force reloading of data from Firebase.
        """
        try:
            self.df_documentos = pd.DataFrame()
            self.vendedores_list = ['Todos']

            result = self.load_data_from_firebase()
            self._last_update = datetime.now()

            return result

        except Exception as e:
            print(f"❌ Error recargando datos de cartera: {e}")
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

    def load_data_from_firebase(self, force_reload=False):
        """
        Load data from Firebase database.

        Args:
            force_reload (bool): Si True, fuerza la recarga incluso si ya hay datos
        """
        try:
            # Si ya tenemos datos y no es recarga forzada, usar cache
            if not force_reload and not self.df_documentos.empty:
                return self.df_documentos

            db = self._get_db()

            if not db:
                print("❌ No se pudo obtener conexión a la base de datos")
                return pd.DataFrame()

            data = db.get("cartera_actual")

            if data:
                result = self.process_data(data)
                return result
            else:
                print("⚠️ No data found in Firebase - cartera_actual")
                return pd.DataFrame()

        except Exception as e:
            print(f"❌ Error loading data from Firebase: {e}")
            return pd.DataFrame()

    def process_data(self, data):
        """
        Process raw data and create DataFrame.

        Args:
            data (dict): Raw data from Firebase

        Returns:
            pd.DataFrame: Processed dataframe with customer and document information
        """
        if not data:
            return pd.DataFrame()

        documentos_list = []

        for cliente_id, cliente_info in data.items():
            documentos = cliente_info.get('documentos', {})
            for doc_id, doc_info in documentos.items():
                doc_row = {
                    'cliente_id': cliente_id,
                    'documento_id': doc_id,
                    'cliente_nombre': cliente_info.get('cliente', ''),
                    'razon_social': cliente_info.get('razon', ''),
                    'ciudad': cliente_info.get('ciudad', ''),
                    'nit': cliente_info.get('nit', ''),
                    'vendedor': cliente_info.get('vendedor', 'Sin Asignar'),
                    'forma_pago': cliente_info.get('forma_pago', 'No Definida'),
                    'fecha': doc_info.get('fecha', ''),
                    'notas': doc_info.get('notas', ''),
                    'vencimiento': doc_info.get('vencimiento', ''),
                    'saldo': float(doc_info.get('saldo', 0) or 0),
                    'valor': float(doc_info.get('valor', 0) or 0),
                    'vencida': float(doc_info.get('vencida', 0) or 0),
                    'sin_vencer': float(doc_info.get('sin_vencer', 0) or 0),
                    'aplicado': float(doc_info.get('aplicado', 0) or 0)
                }
                documentos_list.append(doc_row)

        if not documentos_list:
            return pd.DataFrame()

        self.df_documentos = pd.DataFrame(documentos_list)

        # Process dates
        self.df_documentos['fecha'] = pd.to_datetime(
            self.df_documentos['fecha'], errors='coerce')
        self.df_documentos['vencimiento'] = pd.to_datetime(
            self.df_documentos['vencimiento'], errors='coerce')

        # Calculate overdue days safely
        hoy = datetime.now().date()

        def calcular_dias_vencidos(fecha_venc):
            """Calculate days overdue for a given due date."""
            if pd.isna(fecha_venc):
                return np.nan
            try:
                return (hoy - fecha_venc.date()).days
            except:
                return np.nan

        self.df_documentos['dias_vencidos'] = self.df_documentos['vencimiento'].apply(
            calcular_dias_vencidos)

        # Create combined client-company name for display
        self.df_documentos['cliente_completo'] = self.df_documentos.apply(
            lambda row: f"{row['cliente_nombre']} – {row['razon_social']}"
            if row['razon_social'] and row['razon_social'].strip()
            else row['cliente_nombre'], axis=1
        )

        # List of salespeople
        vendedores_unicos = self.df_documentos['vendedor'].dropna().unique()
        self.vendedores_list = [
            'Todos'] + sorted([v for v in vendedores_unicos if v != 'Sin Asignar'])

        return self.df_documentos

    def filter_by_vendedor(self, vendedor):
        """
        Filter data by salesperson.

        Args:
            vendedor (str): Salesperson name or 'Todos' for all

        Returns:
            pd.DataFrame: Filtered dataframe
        """
        if vendedor == 'Todos':
            return self.df_documentos

        return \
            self.df_documentos[self.df_documentos['vendedor'] == vendedor]

    def get_resumen(self, vendedor='Todos'):
        """
        Get portfolio summary statistics.

        Args:
            vendedor (str): Salesperson name or 'Todos' for all

        Returns:
            dict: Summary statistics including totals, percentages, and counts
        """
        df = self.filter_by_vendedor(vendedor)

        # Customers with overdue portfolio
        clientes_vencida = df[df['vencida'] > 0]['cliente_id'].nunique()

        # Number of invoices (unique documents)
        num_facturas = df['documento_id'].nunique()

        # Quality indicator: Percentage of current portfolio (not overdue)
        total_cartera = df['saldo'].sum()
        cartera_al_dia = df['sin_vencer'].sum()
        porcentaje_al_dia = (cartera_al_dia / total_cartera *
                             100) if total_cartera != 0 else 0

        return {
            'total_cartera': total_cartera,
            'total_vencida': df['vencida'].sum(),
            'total_sin_vencer': cartera_al_dia,
            'porcentaje_al_dia': porcentaje_al_dia,
            'num_clientes': df['cliente_id'].nunique(),
            'clientes_vencida': clientes_vencida,
            'num_documentos': len(df),
            'num_facturas': num_facturas
        }

    def get_rangos_vencimiento(self, vendedor='Todos'):
        """
        Get distribution by overdue ranges.

        Args:
            vendedor (str): Salesperson name or 'Todos' for all

        Returns:
            pd.DataFrame: Distribution by overdue day ranges
        """
        df = self.filter_by_vendedor(vendedor).copy()

        def clasificar_vencimiento(dias):
            """Classify overdue days into ranges."""
            if pd.isna(dias):
                return 'Sin Fecha'
            elif dias < 0:
                return 'Por Vencer'
            elif dias <= 30:
                return '0-30 días'
            elif dias <= 60:
                return '31-60 días'
            elif dias <= 90:
                return '61-90 días'
            elif dias <= 180:
                return '91-180 días'
            else:
                return 'Más de 180 días'

        df['rango'] = df['dias_vencidos'].apply(clasificar_vencimiento)

        resultado = df.groupby('rango').agg({
            'saldo': 'sum',
            'documento_id': 'count'
        }).reset_index()

        orden = ['Por Vencer', '0-30 días', '31-60 días',
                 '61-90 días', '91-180 días', 'Más de 180 días', 'Sin Fecha']
        resultado['rango'] = pd.Categorical(
            resultado['rango'], categories=orden, ordered=True)

        return resultado.sort_values('rango')

    def get_forma_pago(self, vendedor='Todos'):
        """
        Get distribution by payment method.

        Args:
            vendedor (str): Salesperson name or 'Todos' for all

        Returns:
            pd.DataFrame: Distribution by payment method
        """
        df = self.filter_by_vendedor(vendedor)

        resultado = df.groupby('forma_pago').agg({
            'saldo': 'sum',
            'cliente_id': 'nunique'
        }).reset_index()

        return resultado[resultado['saldo'] != 0]

    def get_top_clientes(self, tipo='vencida', vendedor='Todos', top_n=10):
        """
        Get top customers by portfolio type.

        Args:
            tipo (str): Portfolio type ('vencida' or 'sin_vencer')
            vendedor (str): Salesperson name or 'Todos' for all
            top_n (int): Number of top customers to return

        Returns:
            pd.DataFrame: Top customers with combined client-company names
        """
        df = self.filter_by_vendedor(vendedor)

        resultado = df.groupby(['cliente_id', 'cliente_completo']).agg({
            'vencida': 'sum',
            'sin_vencer': 'sum',
            'saldo': 'sum'
        }).reset_index()

        column = 'vencida' if tipo == 'vencida' else 'sin_vencer'
        resultado = resultado[resultado[column] > 0]

        return resultado.nlargest(top_n, column)

    def get_treemap_data_vencida(self, vendedor='Todos'):
        """
        Get data for overdue portfolio treemap visualization.

        Args:
            vendedor (str): Salesperson name or 'Todos' for all

        Returns:
            pd.DataFrame: Data formatted for treemap with combined client-company names (overdue only)
        """
        df = self.filter_by_vendedor(vendedor)

        if df.empty:
            return pd.DataFrame()

        resultado = df.groupby(['cliente_completo']).agg({
            'vencida': 'sum'
        }).reset_index()

        # Filter only positive and valid values for overdue portfolio
        resultado = resultado[
            (resultado['vencida'] > 0) &
            (resultado['cliente_completo'].notna()) &
            (resultado['cliente_completo'] != '')
        ]

        return resultado

    def get_treemap_data(self, vendedor='Todos'):
        """
        Get data for treemap visualization.

        Args:
            vendedor (str): Salesperson name or 'Todos' for all

        Returns:
            pd.DataFrame: Data formatted for treemap with combined client-company names
        """
        df = self.filter_by_vendedor(vendedor)

        if df.empty:
            return pd.DataFrame()

        resultado = df.groupby(['cliente_completo']).agg({
            'saldo': 'sum'
        }).reset_index()

        # Filter only positive and valid values
        resultado = resultado[
            (resultado['saldo'] > 0) &
            (resultado['cliente_completo'].notna()) &
            (resultado['cliente_completo'] != '')
        ]

        return resultado

    def get_proximos_vencer(self, dias_limite=5, vendedor='Todos'):
        """
        Get customers about to expire.

        Args:
            dias_limite (int): Days limit for expiration analysis
            vendedor (str): Salesperson name or 'Todos' for all

        Returns:
            pd.DataFrame: Customers about to expire with combined names
        """
        df = self.filter_by_vendedor(vendedor).copy()

        # Filter documents expiring in X days
        proximos = df[
            (df['dias_vencidos'] < 0) &
            (abs(df['dias_vencidos']) <= dias_limite) &
            (df['sin_vencer'] > 0)
        ].copy()

        if len(proximos) == 0:
            return pd.DataFrame()

        proximos['dias_hasta_vencimiento'] = abs(proximos['dias_vencidos'])

        resultado = proximos.groupby(['cliente_id', 'cliente_completo']).agg({
            'sin_vencer': 'sum',
            'dias_hasta_vencimiento': 'min'
        }).reset_index()

        return resultado.sort_values('dias_hasta_vencimiento')

    def get_documentos_proximos_vencer(self, dias_limite=5, vendedor='Todos'):
        """
        Get documents about to expire grouped by customer.

        Args:
            dias_limite (int): Days limit for expiration analysis
            vendedor (str): Salesperson name or 'Todos' for all

        Returns:
            pd.DataFrame: Documents about to expire with combined client-company names
        """
        df = self.filter_by_vendedor(vendedor).copy()

        # Filter documents expiring in X days
        proximos = df[
            (df['dias_vencidos'] < 0) &
            (abs(df['dias_vencidos']) <= dias_limite) &
            (df['sin_vencer'] > 0)
        ].copy()

        if len(proximos) == 0:
            return pd.DataFrame()

        proximos['dias_hasta_vencimiento'] = abs(proximos['dias_vencidos'])

        # Select relevant columns
        resultado = proximos[['cliente_completo', 'documento_id',
                              'vencimiento', 'sin_vencer', 'dias_hasta_vencimiento']].copy()
        resultado = resultado.sort_values(
            ['cliente_completo', 'dias_hasta_vencimiento'])

        return resultado

    def get_documentos_agrupados_por_dias(self, dias_limite=5, vendedor='Todos'):
        """
        Get documents about to expire grouped by days and then by client for stacked bar chart.

        Args:
            dias_limite (int): Days limit for expiration analysis
            vendedor (str): Salesperson name or 'Todos' for all

        Returns:
            pd.DataFrame: Documents grouped by days until expiration and client with document lists
        """
        df = self.filter_by_vendedor(vendedor).copy()

        # Filter documents expiring in X days
        proximos = df[
            (df['dias_vencidos'] < 0) &
            (abs(df['dias_vencidos']) <= dias_limite) &
            (df['sin_vencer'] > 0)
        ].copy()

        if len(proximos) == 0:
            return pd.DataFrame()

        proximos['dias_hasta_vencimiento'] = abs(proximos['dias_vencidos'])

        # Group by days and client, sum the amounts and collect document IDs
        resultado = proximos.groupby(['dias_hasta_vencimiento', 'cliente_completo']).agg({
            'sin_vencer': 'sum',
            # Collect all document IDs as a list
            'documento_id': lambda x: list(x)
        }).reset_index()

        # Create formatted document list and count
        resultado['documentos_lista'] = \
            resultado['documento_id'].apply(
                lambda docs: ' - '.join(sorted(docs))
                if len(docs) <= 10
                else ' - '.join(sorted(docs)[:10]) + f' (+{len(docs)-10} más)'
        )
        resultado['num_documentos'] = resultado['documento_id'].apply(len)

        # CAMBIO PRINCIPAL: Ordenar por días ascendente Y por valores (sin_vencer) ascendente también
        return resultado.sort_values(['dias_hasta_vencimiento', 'sin_vencer'], ascending=[True, True])

    def get_clientes_list(self, vendedor='Todos'):
        """
        Get list of clients for dropdown selection.

        Args:
            vendedor (str): Salesperson name or 'Todos' for all

        Returns:
            list: List of client names with combined format
        """
        df = self.filter_by_vendedor(vendedor)

        if df.empty:
            return []

        clientes = df['cliente_completo'].unique()

        return \
            ['Todos'] + \
            sorted([cliente for cliente in clientes if cliente and cliente.strip()])

    def get_cliente_detalle(self, cliente_completo: str, vendedor: str = 'Todos'):
        """
        Get detailed information for a specific client with combined data.
        """
        df = self.filter_by_vendedor(vendedor)

        if df.empty or not cliente_completo:
            return \
                {
                    'forma_pago': 'No Definida',
                    'documentos': pd.DataFrame()
                }

        # Filter by client
        if cliente_completo == "Todos":
            cliente_df = df.copy()
        else:
            cliente_df = df[df['cliente_completo'] == cliente_completo].copy()

        if cliente_df.empty:
            return \
                {
                    'forma_pago': 'No Definida',
                    'documentos': pd.DataFrame()
                }

        # Get payment method
        forma_pago = cliente_df['forma_pago'].iloc[0]

        # Prepare combined dataframe
        columns_tabla = ['documento_id', 'valor', 'aplicado',
                         'saldo', 'fecha', 'vencimiento', 'dias_vencidos']

        # Add tipo column to distinguish between vencida and sin_vencer
        documentos_combined = []

        # Add documents with overdue portfolio
        vencida_docs = cliente_df[cliente_df['vencida'] > 0].copy()
        if not vencida_docs.empty:
            vencida_docs['tipo'] = 'vencida'
            vencida_docs['notas'] = vencida_docs.get(
                'notas', 'Sin notas')  # Handle missing notas
            documentos_combined.append(
                vencida_docs[columns_tabla + ['tipo', 'notas']])

        # Add documents without overdue portfolio
        sin_vencer_docs = cliente_df[cliente_df['sin_vencer'] > 0].copy()

        if not sin_vencer_docs.empty:
            sin_vencer_docs['tipo'] = 'sin_vencer'
            sin_vencer_docs['notas'] = sin_vencer_docs.get(
                'notas', 'Sin notas')  # Handle missing notas
            documentos_combined.append(
                sin_vencer_docs[columns_tabla + ['tipo', 'notas']])

        # Combine all documents
        if documentos_combined:
            documentos_df = pd.concat(documentos_combined, ignore_index=True)
            # Sort by tipo (vencida first) then by dias_vencidos
            documentos_df = documentos_df.sort_values(
                ['tipo', 'dias_vencidos'], ascending=[False, False])
        else:
            documentos_df = pd.DataFrame(
                columns=columns_tabla + ['tipo', 'notas'])

        return \
            {
                'forma_pago': forma_pago,
                'documentos': documentos_df
            }

    def get_todos_clientes_detalle(self, vendedor: str = 'Todos'):
        """
        Get detailed information for ALL clients with combined data.
        Similar to get_cliente_detalle but for all clients.

        Args:
            vendedor: Salesperson name or 'Todos' for all

        Returns:
            dict: Dictionary with combined documents from all clients
        """
        df = self.filter_by_vendedor(vendedor)

        if df.empty:
            return \
                {
                    'forma_pago': 'Múltiples',
                    'documentos': pd.DataFrame()
                }

        # Prepare combined dataframe for ALL clients
        columns_tabla = ['documento_id', 'valor', 'aplicado',
                         'saldo', 'fecha', 'vencimiento', 'dias_vencidos',
                         'cliente_completo', 'cliente_nombre']  # Incluir info del cliente

        # Add documents with overdue portfolio
        documentos_combined = []

        vencida_docs = df[df['vencida'] > 0].copy()
        if not vencida_docs.empty:
            vencida_docs['tipo'] = 'vencida'
            vencida_docs['notas'] = vencida_docs.get('notas', 'Sin notas')
            documentos_combined.append(
                vencida_docs[columns_tabla + ['tipo', 'notas']])

        # Add documents without overdue portfolio
        sin_vencer_docs = df[df['sin_vencer'] > 0].copy()
        if not sin_vencer_docs.empty:
            sin_vencer_docs['tipo'] = 'sin_vencer'
            sin_vencer_docs['notas'] = sin_vencer_docs.get(
                'notas', 'Sin notas')
            documentos_combined.append(
                sin_vencer_docs[columns_tabla + ['tipo', 'notas']])

        # Combine all documents
        if documentos_combined:
            documentos_df = pd.concat(documentos_combined, ignore_index=True)
            # Sort by client name, then by tipo (vencida first) then by dias_vencidos
            documentos_df = documentos_df.sort_values(
                ['cliente_completo', 'tipo', 'dias_vencidos'],
                ascending=[True, False, False])
        else:
            documentos_df = pd.DataFrame(
                columns=columns_tabla + ['tipo', 'notas'])

        return \
            {
                'forma_pago': 'Múltiples',  # Multiple payment methods
                'documentos': documentos_df
            }

    def calculate_portfolio_indicator(self, vendedor='Todos'):
        """
        Calculate portfolio performance indicator for vendors.
        Based on indicador_cartera_v4.py logic.

        Returns:
            dict or list: Indicator data for single vendor or all vendors
        """
        from datetime import datetime
        from collections import defaultdict

        # Constants
        NON_CURRENT_SELLERS = {
            "MONICA YANET DUQUE",
            "MONICA BIBIANA HOLGUIN",
            "MAURICIO ROJAS PERAZA",
            "JERLY INFANTE RUEDA",
            "GAVIS AGUIRRE RODRIGUEZ",
            "DIANA CAROLINA LONDOÑO",
            "JESUS IVAN GOMEZ VELASQUEZ",
            "(Cartera)LUISA MARIA COSSIO ORTIZ",
            "LUISA FERNANDA ZAPATA GALVIS",
            "NIDIA BIBIANA TABORDA BETANCUR",
            "JHONEVER ORTIZ"
        }

        WEIGHTS = {
            'overdue_rate': 0.2,
            'avg_days_overdue': 0.35,
            'collection_efficiency': 0.1,
            'portfolio_turnover': 0.2,
            'risk_concentration': 0.15
        }

        TODAY = datetime.now()

        # Get necessary data from Firebase
        db = self._get_db()

        if not db:
            return [] if vendedor == 'Todos' else {}

        try:
            # Load collections
            cartera_actual = db.get("cartera_actual")
            recibos_caja = db.get("recibos_caja")
            fac_ventas = db.get("fac_ventas")
            codigos_vendedores = db.get_by_path("/maestros/codigos_vendedores")

            if not all([cartera_actual, recibos_caja, fac_ventas]):
                return [] if vendedor == 'Todos' else {}

            # Process portfolio data by vendor
            vendor_portfolio = defaultdict(lambda: {
                'total_portfolio': 0,
                'overdue_portfolio': 0,
                'weighted_days_sum': 0,
                'invoices': [],
                'client_count': 0,
                'clients_overdue': {},
                'credit_notes_value': 0
            })

            for client_id, client_data in cartera_actual.items():
                vendor_name = client_data.get('vendedor', 'UNKNOWN')

                if vendor_name in NON_CURRENT_SELLERS:
                    continue

                # Filter by vendor if specified
                if vendedor != 'Todos' and vendor_name != vendedor:
                    continue

                documents = client_data.get('documentos', {})
                client_name = client_data.get('cliente', 'UNKNOWN')
                doc_type = client_data.get('tipo', 'UNKNOWN')

                if client_name not in vendor_portfolio[vendor_name]['clients_overdue']:
                    has_valid_documents = False

                for doc_num, doc_data in documents.items():
                    saldo = doc_data.get('saldo', 0)

                    vendor_portfolio[vendor_name]['total_portfolio'] += saldo

                    # Valid invoices (6 digits starting with 7)
                    if doc_type == "Remision de la FE":
                        due_date = doc_data.get('vencimiento', '')

                        if saldo <= 0:
                            continue

                        has_valid_documents = True
                        days_overdue = self._calculate_days_overdue(
                            due_date, TODAY)

                        vendor_portfolio[vendor_name]['invoices'].append({
                            'doc_num': doc_num,
                            'saldo': saldo,
                            'days_overdue': days_overdue,
                            'client': client_name
                        })

                        if days_overdue > 0:
                            vendor_portfolio[vendor_name]['overdue_portfolio'] += saldo
                            vendor_portfolio[vendor_name]['weighted_days_sum'] += (
                                saldo * days_overdue)

                            if client_name not in vendor_portfolio[vendor_name]['clients_overdue']:
                                vendor_portfolio[vendor_name]['clients_overdue'][client_name] = 0

                            vendor_portfolio[vendor_name]['clients_overdue'][client_name] += saldo

                    # Credit notes (4 digits)
                    elif doc_type == "Nota Credito Clientes":
                        vendor_portfolio[vendor_name]['total_portfolio'] += saldo
                        vendor_portfolio[vendor_name]['credit_notes_value'] += saldo
                        has_valid_documents = True

                if has_valid_documents:
                    vendor_portfolio[vendor_name]['client_count'] += 1

            # Calculate collections by vendor
            vendor_collections = defaultdict(float)

            for receipt_id, receipt_data in recibos_caja.items():
                vendor_name = receipt_data.get('vendedor', 'UNKNOWN')

                if vendor_name not in NON_CURRENT_SELLERS:
                    if vendedor == 'Todos' or vendor_name == vendedor:
                        amount = receipt_data.get('valor_recibo', 0)
                        vendor_collections[vendor_name] += amount

            # Calculate sales by vendor
            vendor_sales = defaultdict(float)

            for invoice_id, invoice_data in fac_ventas.items():
                vendor_code = invoice_data.get('vendedor', '')
                vendor_name = codigos_vendedores.get(
                    vendor_code, 'UNKNOWN') if codigos_vendedores else 'UNKNOWN'

                if vendor_name not in NON_CURRENT_SELLERS:
                    if vendedor == 'Todos' or vendor_name == vendedor:
                        valor_bruto = invoice_data.get('valor_bruto', 0)
                        descuento = invoice_data.get('descuento', 0)
                        iva = invoice_data.get('iva', 0)
                        net_value = valor_bruto - descuento + iva
                        vendor_sales[vendor_name] += net_value

            # Calculate indicators for each vendor
            results = []

            for vendor_name, data in vendor_portfolio.items():
                if data['total_portfolio'] == 0:
                    continue

                # Calculate metrics
                overdue_rate = (data['overdue_portfolio'] /
                                data['total_portfolio']) * 100
                overdue_rate_risk = min(1.0, overdue_rate / 100)

                # WOF (Weighted Overdue Factor)
                if data['total_portfolio'] > 0:
                    wof = data['weighted_days_sum'] / data['total_portfolio']
                    wof_risk = min(1.0, wof / 90)
                else:
                    wof = 0
                    wof_risk = 0

                avg_days_overdue = data['weighted_days_sum'] / \
                    data['overdue_portfolio'] if data['overdue_portfolio'] > 0 else 0

                # Collection efficiency
                collections = vendor_collections.get(vendor_name, 0)
                sales = vendor_sales.get(vendor_name, 0)

                if sales > 0:
                    collection_efficiency = (collections / sales) * 100
                    collection_risk = max(
                        0, 1.0 - (collection_efficiency / 100))
                else:
                    collection_efficiency = 0
                    collection_risk = 0.5

                # DSO (Days Sales Outstanding)
                if sales > 0:
                    daily_sales = sales / 365
                    dso = data['total_portfolio'] / \
                        daily_sales if daily_sales > 0 else 365
                    dso_risk = min(1.0, max(0, (dso - 30) / 90))
                else:
                    dso = 0
                    dso_risk = 0.5

                # Risk concentration
                if data['overdue_portfolio'] > 0 and data['clients_overdue']:
                    sorted_clients = sorted(
                        data['clients_overdue'].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )
                    top_n = min(3, len(sorted_clients))
                    top_clients_overdue = sum(
                        [amount for _, amount in sorted_clients[:top_n]])

                    concentration_pct = (
                        top_clients_overdue / data['overdue_portfolio']) * 100
                    concentration_risk = concentration_pct / 100
                else:
                    concentration_pct = 0
                    concentration_risk = 0

                # Calculate composite risk indicator with penalty factor
                base_composite_risk = (
                    overdue_rate_risk * WEIGHTS['overdue_rate'] +
                    wof_risk * WEIGHTS['avg_days_overdue'] +
                    collection_risk * WEIGHTS['collection_efficiency'] +
                    dso_risk * WEIGHTS['portfolio_turnover'] +
                    concentration_risk * WEIGHTS['risk_concentration']
                )

                # Apply exponential penalty for higher risks (makes it more strict)
                # This makes the scale non-linear, penalizing higher risks
                if base_composite_risk >= 0.5:
                    # Apply exponential penalty for risks above 0.5
                    # Exponential growth
                    penalty_factor = 1.5 ** ((base_composite_risk - 0.5) * 4)
                    composite_risk = min(
                        1.0, 0.5 + (base_composite_risk - 0.5) * penalty_factor)
                else:
                    composite_risk = base_composite_risk

                vendor_result = {
                    'vendor': vendor_name,
                    'risk_indicator': round(composite_risk, 4),
                    'total_portfolio': round(data['total_portfolio'], 2),
                    'overdue_portfolio': round(data['overdue_portfolio'], 2),
                    'overdue_rate': round(overdue_rate, 2),
                    'wof': round(wof, 2),
                    'avg_days_overdue': round(avg_days_overdue, 2),
                    'collection_efficiency': round(collection_efficiency, 2),
                    'dso': round(dso, 2),
                    'risk_concentration': round(concentration_pct, 2),
                    'client_count': data['client_count'],
                    'total_collections': round(collections, 2),
                    'total_sales': round(sales, 2),
                    'invoice_count': len(data['invoices']),
                    'credit_notes_value': round(data['credit_notes_value'], 2),
                    # Component risks for visualization
                    'component_risks': {
                        'overdue_rate_risk': round(overdue_rate_risk, 3),
                        'wof_risk': round(wof_risk, 3),
                        'collection_risk': round(collection_risk, 3),
                        'dso_risk': round(dso_risk, 3),
                        'concentration_risk': round(concentration_risk, 3)
                    }
                }

                results.append(vendor_result)

            # Sort by risk indicator (highest first)
            results.sort(key=lambda x: x['risk_indicator'], reverse=True)

            # Apply percentile-based categorization for stricter evaluation
            if len(results) >= 5:  # Only apply if we have enough vendors
                import numpy as np
                risk_values = [r['risk_indicator'] for r in results]

                # Calculate percentiles
                p25 = np.percentile(risk_values, 25)
                p50 = np.percentile(risk_values, 50)
                p75 = np.percentile(risk_values, 75)
                p90 = np.percentile(risk_values, 90)

                # Add percentile information and adjusted risk level
                for vendor_result in results:
                    risk = vendor_result['risk_indicator']

                    # Determine percentile category
                    if risk >= p90:
                        vendor_result['percentile'] = 90
                        vendor_result['risk_category'] = 'CRÍTICO'
                        vendor_result['adjusted_risk'] = min(
                            1.0, 0.85 + (risk - p90) / (1 - p90) * 0.15) if p90 < 1 else risk
                    elif risk >= p75:
                        vendor_result['percentile'] = 75
                        vendor_result['risk_category'] = 'ALTO'
                        vendor_result['adjusted_risk'] = 0.70 + \
                            (risk - p75) / (p90 - p75) * \
                            0.15 if p90 > p75 else risk
                    elif risk >= p50:
                        vendor_result['percentile'] = 50
                        vendor_result['risk_category'] = 'MEDIO'
                        vendor_result['adjusted_risk'] = 0.45 + \
                            (risk - p50) / (p75 - p50) * \
                            0.25 if p75 > p50 else risk
                    elif risk >= p25:
                        vendor_result['percentile'] = 25
                        vendor_result['risk_category'] = 'MODERADO'
                        vendor_result['adjusted_risk'] = 0.25 + \
                            (risk - p25) / (p50 - p25) * \
                            0.20 if p50 > p25 else risk
                    else:
                        vendor_result['percentile'] = 0
                        vendor_result['risk_category'] = 'BAJO'
                        vendor_result['adjusted_risk'] = risk / \
                            p25 * 0.25 if p25 > 0 else risk

                    # Store percentile thresholds for reference
                    vendor_result['percentile_thresholds'] = {
                        'p25': round(p25, 4),
                        'p50': round(p50, 4),
                        'p75': round(p75, 4),
                        'p90': round(p90, 4)
                    }
            else:
                # If not enough vendors, use fixed thresholds
                for vendor_result in results:
                    risk = vendor_result['risk_indicator']
                    vendor_result['adjusted_risk'] = risk
                    if risk >= 0.8:
                        vendor_result['risk_category'] = 'CRÍTICO'
                    elif risk >= 0.6:
                        vendor_result['risk_category'] = 'ALTO'
                    elif risk >= 0.4:
                        vendor_result['risk_category'] = 'MEDIO'
                    elif risk >= 0.2:
                        vendor_result['risk_category'] = 'MODERADO'
                    else:
                        vendor_result['risk_category'] = 'BAJO'
                    vendor_result['percentile'] = None
                    vendor_result['percentile_thresholds'] = {}

            # Return single vendor data if specified
            if vendedor != 'Todos':
                return results[0] if results else {}

            return results

        except Exception as e:
            print(f"Error calculating portfolio indicator: {e}")
            return [] if vendedor == 'Todos' else {}

    def _calculate_days_overdue(self, due_date_str, today):
        """
        Helper method to calculate days overdue
        """
        from datetime import datetime

        try:
            due_date = datetime.strptime(due_date_str, '%Y/%m/%d')
            days_diff = (today - due_date).days
            return max(0, days_diff)
        except:
            return 0

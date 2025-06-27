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

    def _get_db(self):
        """
        Get database instance.
        """
        from server import get_db

        return get_db()

    def load_data_from_firebase(self):
        """
        Load data from Firebase database.

        Returns:
            pd.DataFrame: Processed dataframe with portfolio data
        """
        try:
            db = self._get_db()
            data = db.get("cartera_actual")

            if data:
                return self.process_data(data)
            else:
                print("No data found in Firebase")
                return pd.DataFrame()
        except Exception as e:
            print(f"Error loading data from Firebase: {e}")
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
        return self.df_documentos[self.df_documentos['vendedor'] == vendedor]

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

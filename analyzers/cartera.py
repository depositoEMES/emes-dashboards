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
            sorted([cliente for cliente in clientes if cliente and cliente.strip()])

    # def get_cliente_detalle(self, cliente_completo, vendedor='Todos'):
    #     """
    #     Get detailed information for a specific client.

    #     Args:
    #         cliente_completo (str): Complete client name
    #         vendedor (str): Salesperson name or 'Todos' for all

    #     Returns:
    #         dict: Dictionary with client details including documents and payment method
    #     """
    #     df = self.filter_by_vendedor(vendedor)

    #     if df.empty or not cliente_completo:
    #         return {
    #             'forma_pago': 'No Definida',
    #             'sin_vencer': pd.DataFrame(),
    #             'vencida': pd.DataFrame()
    #         }

    #     # Filter by client
    #     cliente_df = df[df['cliente_completo'] == cliente_completo].copy()

    #     if cliente_df.empty:
    #         return {
    #             'forma_pago': 'No Definida',
    #             'sin_vencer': pd.DataFrame(),
    #             'vencida': pd.DataFrame()
    #         }

    #     # Get payment method (should be the same for all documents of this client)
    #     forma_pago = cliente_df['forma_pago'].iloc[0]

    #     # Separate documents into current and overdue
    #     sin_vencer_docs = cliente_df[cliente_df['sin_vencer'] > 0].copy()
    #     vencida_docs = cliente_df[cliente_df['vencida'] > 0].copy()

    #     # Select relevant columns for the table
    #     columns_tabla = ['documento_id', 'valor', 'aplicado',
    #                      'saldo', 'fecha', 'vencimiento', 'notas', 'dias_vencidos']

    #     # Prepare sin vencer dataframe
    #     if not sin_vencer_docs.empty:
    #         sin_vencer_tabla = sin_vencer_docs[columns_tabla].copy()
    #         sin_vencer_tabla = sin_vencer_tabla.sort_values('vencimiento')
    #     else:
    #         sin_vencer_tabla = pd.DataFrame(columns=columns_tabla)

    #     # Prepare vencida dataframe
    #     if not vencida_docs.empty:
    #         vencida_tabla = vencida_docs[columns_tabla].copy()
    #         vencida_tabla = vencida_tabla.sort_values(
    #             'dias_vencidos', ascending=False)
    #     else:
    #         vencida_tabla = pd.DataFrame(columns=columns_tabla)

    #     return \
    #         {
    #             'forma_pago': forma_pago,
    #             'sin_vencer': sin_vencer_tabla,
    #             'vencida': vencida_tabla
    #         }

    def get_cliente_detalle(self, cliente_completo, vendedor='Todos'):
        """
        Get detailed information for a specific client with combined data.
        """
        df = self.filter_by_vendedor(vendedor)

        if df.empty or not cliente_completo:
            return {
                'forma_pago': 'No Definida',
                'documentos': pd.DataFrame()
            }

        # Filter by client
        cliente_df = df[df['cliente_completo'] == cliente_completo].copy()

        if cliente_df.empty:
            return {
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

        return {
            'forma_pago': forma_pago,
            'documentos': documentos_df
        }

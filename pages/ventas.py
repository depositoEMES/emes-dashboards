import math
import numpy as np

import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from analyzers import VentasAnalyzer
from utils import format_currency_int, get_theme_styles


# Initialize analyzer
analyzer = VentasAnalyzer()
df = analyzer.load_data_from_firebase()

# Try to load convenios data (optional, won't break if not available)
try:
    df_convenios = analyzer.load_convenios_from_firebase()
except Exception as e:
    print(f"Could not load convenios: {e}")
    df_convenios = pd.DataFrame()

# Try to load recibos data (optional, won't break if not available)
try:
    df_recibos = analyzer.load_recibos_from_firebase()
except Exception as e:
    print(f"Could not load recibos: {e}")
    df_recibos = pd.DataFrame()

# Try to load num_clientes data (optional, won't break if not available)
try:
    df_num_clientes = analyzer.load_num_clientes_from_firebase()
except Exception as e:
    print(f"Could not load num_clientes: {e}")
    df_num_clientes = pd.DataFrame()


def get_dropdown_style(theme):
    """
    Get dropdown styles based on theme.
    """
    if theme == 'dark':
        return {
            'backgroundColor': '#2d2d2d',
            'color': '#ffffff',
            'border': '1px solid #505050'
        }
    else:
        return {
            'backgroundColor': 'white',
            'color': '#2c3e50',
            'border': '1px solid #ddd'
        }


def get_selected_vendor(session_data, dropdown_value):
    """
    Obtener vendedor basado en permisos y selección.
    """
    from utils import can_see_all_vendors, get_user_vendor_filter

    try:
        if not session_data:
            return 'Todos'

        if can_see_all_vendors(session_data):
            # Para administradores, usar el dropdown
            return dropdown_value if dropdown_value else 'Todos'
        else:
            # Para usuarios normales, usar filtro automático
            return get_user_vendor_filter(session_data)
    except Exception as e:
        print(f"Error en get_selected_vendor: {e}")
        return 'Todos'


layout = html.Div([
    # Store for theme
    dcc.Store(id='ventas-theme-store', data='light'),

    # Header
    html.Div([
        html.Div([
            html.H1(id='ventas-titulo-dashboard',
                    children="Dashboard de Ventas")
        ], style={'width': '40%', 'display': 'inline-block'}),

        # Dropdown para vendedores (siempre presente, visibility controlada)
        html.Div([
            html.Label("Vendedor:", style={
                       'fontWeight': 'bold', 'marginBottom': '5px', 'fontFamily': 'Inter'}, id='ventas-dropdown-vendedor-label'),
            dcc.Dropdown(
                id='ventas-dropdown-vendedor',
                options=[{'label': v, 'value': v}
                         for v in analyzer.vendedores_list],
                value='Todos',
                style={'fontFamily': 'Inter'},
                className='custom-dropdown'
            )
        ], style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '2%'}, id='ventas-dropdown-vendedor-container'),

        html.Div([
            html.Label("Mes:", style={
                       'fontWeight': 'bold', 'marginBottom': '5px', 'fontFamily': 'Inter'}),
            dcc.Dropdown(
                id='ventas-dropdown-mes',
                options=[{'label': m, 'value': m}
                         for m in analyzer.meses_list],
                value='Todos',
                style={'fontFamily': 'Inter'},
                className='custom-dropdown'
            )
        ], style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '2%'}),

        html.Div([
            html.Button('🌙', id='ventas-theme-toggle', n_clicks=0)
        ], style={'width': '6%', 'display': 'inline-block', 'verticalAlign': 'top', 'textAlign': 'right'})
    ], style={'marginBottom': '30px', 'padding': '20px'}, id='ventas-header-container'),

    # Cards de resumen - 8 cards en 2 filas
    html.Div([
        # Primera fila de cards
        html.Div([
            html.Div([
                html.H3("Ventas Totales", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}),
                html.H2(id='ventas-ventas-totales', children="$0", style={'color': '#2ecc71',
                        'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='ventas-card-1'),

            html.Div([
                html.H3("Ventas Netas", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}),
                html.H2(id='ventas-ventas-netas', children="$0", style={'color': '#2ecc71',
                        'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='ventas-card-2'),

            html.Div([
                html.H3("Devoluciones", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}),
                html.H2(id='ventas-total-devoluciones', children="$0", style={
                        'color': '#e74c3c', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='ventas-card-3'),

            html.Div([
                html.H3("Descuentos", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}),
                html.H2(id='ventas-total-descuentos', children="$0", style={
                        'color': '#f39c12', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='ventas-card-4'),

        ], style={'marginBottom': '15px'}),

        # Segunda fila de cards
        html.Div([
            html.Div([
                html.H3("Valor Promedio", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}),
                html.H2(id='ventas-valor-promedio', children="$0", style={
                        'color': '#9b59b6', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='ventas-card-5'),

            html.Div([
                html.H3("# Facturas", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}),
                html.H2(id='ventas-num-facturas', children="0", style={'color': '#3498db',
                        'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='ventas-card-6'),

            html.Div([
                html.H3("# Devoluciones", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}),
                html.H2(id='ventas-num-devoluciones', children="0", style={
                        'color': '#c0392b', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='ventas-card-7'),

            html.Div([
                html.H3("Clientes", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}),
                html.H2(id='ventas-num-clientes', children="0", style={'color': '#e67e22',
                        'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='ventas-card-8'),
        ])
    ], style={'marginBottom': '30px'}),

    # Fila 1: Evolución Mensual y Análisis de Estacionalidad
    html.Div([
        html.Div([
            html.H3("Evolución de Ventas por Mes", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
            dcc.Graph(id='ventas-grafico-ventas-mes')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'}),

        html.Div([
            html.H3("Estacionalidad por Día de la Semana", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
            dcc.Graph(id='ventas-grafico-estacionalidad')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'})
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'}, id='ventas-row1-container'),

    # Fila 1.2: Comparativa de Vendedores (Solo para Administradores)
    html.Div([
        html.H3("Comparativa de Ventas por Vendedor", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
        html.P("(Evolución mensual comparativa - Solo visible para administradores)", style={
               'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '12px', 'margin': '0 0 20px 0'}),
        html.Div([
            html.Label("Tipo de Gráfico:", style={
                       'fontWeight': 'bold', 'marginRight': '10px', 'fontFamily': 'Inter'}),
            dcc.Dropdown(
                id='ventas-dropdown-tipo-grafico',
                options=[
                    {'label': 'Líneas (Tendencias)', 'value': 'lineas'},
                    {'label': 'Barras Agrupadas (Comparación)',
                     'value': 'barras'}
                ],
                value='lineas',
                style={'width': '250px', 'fontFamily': 'Inter',
                       'display': 'inline-block'},
                clearable=False
            )
        ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginBottom': '20px'}),
        dcc.Graph(id='ventas-grafico-comparativa-vendedores')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'}, id='ventas-row1-2-container'),

    # Fila 1.3: Ventas por vendedor (subplots)
    html.Div([
        html.H3("Evolución Individual por Vendedor", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
        html.P("(Gráficos de área individuales - Solo visible para administradores)", style={
            'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '12px', 'margin': '0 0 20px 0'}),
        dcc.Graph(id='ventas-graficos-area-individuales')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'},
        id='ventas-row1-3-container'),

    # Fila 1.5: Evolución de Ventas por Cliente Específico
    html.Div([
        html.H3("Evolución Diaria de Ventas por Cliente", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
        html.Div([
            html.Label("Seleccionar Cliente:", style={
                       'fontWeight': 'bold', 'marginBottom': '10px', 'fontFamily': 'Inter'}),
            dcc.Dropdown(
                id='ventas-dropdown-cliente',
                options=[{'label': 'Seleccione un cliente',
                          'value': 'Seleccione un cliente'}],
                value='Seleccione un cliente',
                style={'fontFamily': 'Inter', 'marginBottom': '20px'},
                className='custom-dropdown'
            )
        ]),
        dcc.Graph(id='ventas-grafico-evolucion-cliente')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'}, id='ventas-row1-5-container'),

    # Fila 2: Distribución por Zona y Forma de Pago
    html.Div([
        html.Div([
            html.H3("Ventas por Zona", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
            dcc.Graph(id='ventas-grafico-zona')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'}),

        html.Div([
            html.H3("Distribución por Forma de Pago", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
            dcc.Graph(id='ventas-grafico-forma-pago')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'})
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'}, id='ventas-row2-container'),

    # Fila 2.5: Ventas Acumuladas por Cliente (Treemap solo)
    html.Div([
        html.H3("Ventas Acumuladas por Cliente", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
        html.P("(Acumulado hasta el mes seleccionado)", style={
               'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '12px', 'margin': '0 0 20px 0'}),
        dcc.Graph(id='ventas-treemap-acumuladas')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'}, id='ventas-row2-5-container'),

    # Fila 3: Treemap de Ventas por Cliente del Período (Treemap solo)
    html.Div([
        html.H3("Mapa de Ventas por Cliente (Período Seleccionado)", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
        dcc.Graph(id='ventas-treemap-ventas')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'}, id='ventas-row3-container'),

    # Fila 3.5: Top Clientes y Clientes Impactados
    html.Div([
        html.H3("Clientes por Días Sin Venta", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
        html.P("(Clientes que no han comprado en 7+ días - Tamaño por total de ventas históricas)", style={
               'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '12px', 'margin': '0 0 20px 0'}),
        dcc.Graph(id='ventas-treemap-dias-sin-venta')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'}, id='ventas-row-nueva-treemap'),

    # Fila 4: Top Clientes y Clientes Impactados
    html.Div([
        html.Div([
            html.H3("Top 10 - Clientes", style={'textAlign': 'center',
                    'marginBottom': '20px', 'fontFamily': 'Inter'}),
            dcc.Graph(id='ventas-top-clientes')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'}),

        html.Div([
            html.H3("Clientes Impactados por Mes", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
            html.P("(Número de clientes únicos que compraron vs total disponible)", style={
                   'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '12px', 'margin': '0 0 20px 0'}),
            dcc.Graph(id='ventas-grafico-clientes-impactados')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'})
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'}, id='ventas-row4-container'),

    # Fila 5: Análisis de Convenios
    html.Div([
        html.H3("Análisis de Cumplimiento de Convenios", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
        html.P("(Comparación entre metas vs. ventas reales y descuentos acordados vs. descuentos aplicados)", style={
               'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '12px', 'margin': '0 0 20px 0'}),
        html.Div(id='ventas-tabla-convenios')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'}, id='ventas-row5-container'),

    # Fila 6: Análisis de Recaudo
    html.Div([
        html.Div([
            html.H3("Análisis de Recaudo", style={
                    'textAlign': 'center', 'marginBottom': '10px', 'fontFamily': 'Inter'}),
            html.H2(id='ventas-total-recaudo-titulo', style={'textAlign': 'center',
                    'color': '#27ae60', 'marginBottom': '20px', 'fontFamily': 'Inter'}),

            # DROPDOWN VISTA RECAUDO - Now always present in layout
            html.Div([
                html.Label("Vista Temporal:", style={
                           'fontWeight': 'bold', 'marginRight': '10px', 'fontFamily': 'Inter'}),
                dcc.Dropdown(
                    id='ventas-dropdown-vista-recaudo',
                    options=[
                        {'label': 'Recaudo Diario', 'value': 'diario'},
                        {'label': 'Recaudo Mensual', 'value': 'mensual'}
                    ],
                    value='diario',
                    style={'width': '200px', 'fontFamily': 'Inter',
                           'display': 'inline-block'},
                    clearable=False
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginBottom': '20px'}, id='ventas-vista-recaudo-container'),

            # GRAFICOS DE RECAUDO - Now always present in layout
            html.Div([
                # Gráfico por vendedor (solo se muestra cuando vendedor = 'Todos')
                html.Div([
                    html.H4("Resumen por Vendedor", style={
                            'textAlign': 'center', 'marginBottom': '15px', 'fontFamily': 'Inter'}),
                    dcc.Graph(id='ventas-grafico-recaudo-vendedor')
                ], style={'width': '100%', 'marginBottom': '20px'}, id='ventas-container-vendedor'),

                # Gráfico temporal (siempre se muestra)
                html.Div([
                    html.H4(id='ventas-titulo-recaudo-temporal', style={
                            'textAlign': 'center', 'marginBottom': '15px', 'fontFamily': 'Inter'}),
                    dcc.Graph(id='ventas-grafico-recaudo-temporal')
                ], style={'width': '100%'}, id='ventas-container-temporal')
            ], id='ventas-container-graficos-recaudo')
        ])
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'}, id='ventas-row6-container'),

    # Botón actualizar
    html.Div([
        html.Button('Actualizar Datos', id='ventas-btn-actualizar', n_clicks=0,
                    style={'backgroundColor': '#3498db', 'color': 'white', 'border': 'none',
                           'padding': '10px 20px', 'borderRadius': '5px', 'cursor': 'pointer',
                           'fontFamily': 'Inter'})
    ], style={'textAlign': 'center', 'margin': '20px 0'})

], style={'fontFamily': 'Inter', 'backgroundColor': '#f5f5f5', 'padding': '20px'}, id='ventas-main-container')


@callback(
    Output('ventas-grafico-comparativa-vendedores', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-tipo-grafico', 'value'),
     Input('ventas-theme-store', 'data')]
)
def update_comparativa_vendedores(session_data, tipo_grafico, theme):
    """
    Update comparative sales chart with enhanced visual appeal.
    """
    from utils import can_see_all_vendors

    try:
        # Solo mostrar si es administrador
        if not session_data or not can_see_all_vendors(session_data):
            fig = go.Figure()
            fig.add_annotation(
                text="Gráfico disponible solo para administradores",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color='#7f8c8d')
            )
            fig.update_layout(height=400)
            return fig

        theme_styles = get_theme_styles(theme)

        # Obtener datos para todos los vendedores
        # Excluir 'Todos'
        vendedores_disponibles = analyzer.vendedores_list[1:]
        datos_vendedores = {}

        # Obtener TODOS los vendedores que tengan ventas > 0
        for vendedor in vendedores_disponibles:
            try:
                data_vendedor = analyzer.get_ventas_por_mes(vendedor)
                if not data_vendedor.empty and data_vendedor['valor_neto'].sum() > 0:
                    datos_vendedores[vendedor] = data_vendedor
            except:
                continue

        if not datos_vendedores:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos disponibles para comparativa",
                xref="paper", yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=400, paper_bgcolor=theme_styles['plot_bg'])
            return fig

        # Obtener todos los meses únicos
        all_months = set()

        for data in datos_vendedores.values():
            all_months.update(data['mes_nombre'].tolist())

        all_months = sorted(list(all_months))

        # Calcular promedios mensuales
        promedios_mensuales = {}

        for mes in all_months:
            valores_mes = []

            for data in datos_vendedores.values():
                valores_por_mes = dict(
                    zip(data['mes_nombre'], data['valor_neto']))
                if mes in valores_por_mes:
                    valores_mes.append(valores_por_mes[mes])

            if valores_mes:
                promedios_mensuales[mes] = np.mean(valores_mes)

        promedio_valores = \
            [
                promedios_mensuales.get(mes, 0)
                for mes in all_months
            ]

        # Calcular volumen total de ventas por vendedor para color
        volumenes_vendedores = {}

        for vendedor, data in datos_vendedores.items():
            volumenes_vendedores[vendedor] = data['valor_neto'].sum()

        # Obtener min y max para normalización de colores
        min_volumen = min(volumenes_vendedores.values())
        max_volumen = max(volumenes_vendedores.values())

        # Normalizar volúmenes para grosor de línea (todas iguales ahora)
        line_width_standard = 3  # Grosor estándar para todas las líneas

        def get_color_by_volume(volumen):
            """
            Retorna color basado en volumen: rojo (bajo) a verde (alto).
            """
            if max_volumen == min_volumen:
                return '#FFA726'  # Naranja neutro si todos son iguales
            normalized = (volumen - min_volumen) / (max_volumen - min_volumen)
            # Gradiente más suave de rojo a verde
            if normalized >= 0.9:
                return '#1B5E20'  # Verde muy oscuro - Top performers
            elif normalized >= 0.8:
                return '#2E7D32'  # Verde oscuro
            elif normalized >= 0.7:
                return '#388E3C'  # Verde medio-oscuro
            elif normalized >= 0.6:
                return '#4CAF50'  # Verde medio
            elif normalized >= 0.5:
                return '#66BB6A'  # Verde claro
            elif normalized >= 0.4:
                return '#9CCC65'  # Verde amarillento
            elif normalized >= 0.3:
                return '#FFEB3B'  # Amarillo
            elif normalized >= 0.2:
                return '#FF9800'  # Naranja
            elif normalized >= 0.1:
                return '#FF5722'  # Naranja rojizo
            else:
                return '#D32F2F'  # Rojo - Bajo volumen

        # Crear gráfico
        fig = go.Figure()

        if tipo_grafico == 'lineas':
            for _, (vendedor, data) in enumerate(datos_vendedores.items()):
                volumen_total = volumenes_vendedores[vendedor]
                color = get_color_by_volume(volumen_total)

                # Determinar categoría de performance por volumen
                normalized_vol = \
                    (volumen_total - min_volumen) / (max_volumen -
                                                     min_volumen) if max_volumen != min_volumen else 0.5
                if normalized_vol >= 0.8:
                    performance = "🟢 TOP"
                elif normalized_vol >= 0.4:
                    performance = "🟢 Alto"
                elif normalized_vol >= 0.2:
                    performance = "🟡 Medio-Alto"
                elif normalized_vol >= 0.15:
                    performance = "🟠 Medio"
                else:
                    performance = "🔴 Bajo"

                # Línea principal con grosor estándar
                fig.add_trace(go.Scatter(
                    x=data['mes_nombre'],
                    y=data['valor_neto'],
                    mode='lines+markers',
                    name=f"{vendedor[:50]}{'...' if len(vendedor) > 50 else ''} ({performance})",
                    line=dict(
                        color=color,
                        width=line_width_standard,  # Grosor estándar
                        shape='spline'
                    ),
                    marker=dict(
                        size=8,  # Tamaño estándar
                        color=color,
                        line=dict(color='white', width=2),
                        symbol='circle'
                    ),
                    hovertemplate="<b>%{fullData.name}</b> | 💰 %{customdata[0]} | 📋 %{customdata[1]} | 🎯 %{customdata[2]}<extra></extra>",
                    customdata=[[format_currency_int(val), f"{facturas} facturas", format_currency_int(volumen_total)]
                                for val, facturas in zip(data['valor_neto'], data['documento_id'])]
                ))

            # Línea de promedio con estilo destacado
            fig.add_trace(go.Scatter(
                x=all_months,
                y=promedio_valores,
                mode='lines+markers',
                name='📊 PROMEDIO',
                line=dict(
                    color='#E74C3C',
                    width=5,
                    dash='dot'
                ),
                marker=dict(
                    size=12,
                    color='#E74C3C',
                    symbol='diamond',
                    line=dict(color='white', width=2)
                ),
                hovertemplate="<b>📊 Promedio</b> | %{x} | 💰 %{customdata}<extra></extra>",
                customdata=[format_currency_int(val)
                            for val in promedio_valores]
            ))

            # Área de fondo para zona de alto rendimiento
            if promedio_valores:
                max_promedio = max(promedio_valores)
                fig.add_trace(go.Scatter(
                    x=all_months + all_months[::-1],
                    y=[max_promedio * 1.2] *
                    len(all_months) + promedio_valores[::-1],
                    fill='toself',
                    fillcolor='rgba(39, 174, 96, 0.1)',
                    line=dict(color='rgba(255,255,255,0)'),
                    showlegend=False,
                    hoverinfo='skip',
                    name='Zona de Alto Rendimiento'
                ))

            fig.update_layout(
                height=950,
                plot_bgcolor=theme_styles['plot_bg'],
                paper_bgcolor=theme_styles['plot_bg'],
                font=dict(family="Inter", size=12,
                          color=theme_styles['text_color']),
                xaxis=dict(
                    showgrid=True,
                    gridcolor=theme_styles['grid_color'],
                    tickangle=-45,
                    linecolor=theme_styles['line_color'],
                    linewidth=2
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor=theme_styles['grid_color'],
                    tickformat='$,.0f',
                    linecolor=theme_styles['line_color'],
                    linewidth=2
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.4,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=11),
                    bgcolor="rgba(255,255,255,0.8)" if theme == 'light' else "rgba(0,0,0,0.8)",
                    bordercolor=theme_styles['line_color'],
                    borderwidth=1
                ),
                margin=dict(t=20, b=170, l=80, r=40),
                hovermode='x unified'
            )

            # Aplicar estilo de hover más compacto
            fig.update_traces(
                hoverlabel=dict(
                    bgcolor="white" if theme == 'light' else "#2d2d2d",
                    bordercolor=theme_styles['line_color'],
                    font=dict(size=11, family="Inter")  # Texto más pequeño
                )
            )

        else:  # barras agrupadas con colores por volumen
            # Preparar datos para barras con colores basados en volumen
            for i, (vendedor, data) in enumerate(datos_vendedores.items()):
                valores_por_mes = dict(
                    zip(data['mes_nombre'], data['valor_neto']))
                valores_ordenados = [valores_por_mes.get(
                    mes, 0) for mes in all_months]

                volumen_total = volumenes_vendedores[vendedor]
                color = get_color_by_volume(volumen_total)

                # Crear gradiente de colores basado en altura pero manteniendo el color base
                max_valor = max(valores_ordenados) if valores_ordenados else 1
                bar_colors = []
                for valor in valores_ordenados:
                    intensity = valor / max_valor if max_valor > 0 else 0
                    # Más intenso = más opaco, pero manteniendo el color del volumen
                    alpha = 0.4 + (intensity * 0.6)
                    rgb = px.colors.hex_to_rgb(color)
                    bar_colors.append(
                        f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})")

                # Categoría de performance
                normalized_vol = (volumen_total - min_volumen) / (max_volumen -
                                                                  min_volumen) if max_volumen != min_volumen else 0.5
                if normalized_vol >= 0.8:
                    performance = "🟢 TOP"
                elif normalized_vol >= 0.6:
                    performance = "🟢 Alto"
                elif normalized_vol >= 0.4:
                    performance = "🟡 M-Alto"
                elif normalized_vol >= 0.2:
                    performance = "🟠 Medio"
                else:
                    performance = "🔴 Bajo"

                display_name = f"{vendedor[:30]}{'...' if len(vendedor) > 30 else ''} ({performance})"

                fig.add_trace(go.Bar(
                    x=all_months,
                    y=valores_ordenados,
                    name=display_name,
                    marker=dict(
                        color=bar_colors,
                        line=dict(color=color, width=2),
                        pattern=dict(shape="/", bgcolor="white",
                                     size=8, solidity=0.1)  # Patrón sutil
                    ),
                    hovertemplate="<b>%{fullData.name}</b> | 💰 %{customdata[0]} | 📊 %{customdata[1]} | 🎯 %{customdata[2]}<extra></extra>",
                    customdata=[[
                        format_currency_int(val),
                        f"🔥 +{format_currency_int(val - promedios_mensuales.get(mes, 0))}" if val > promedios_mensuales.get(mes, 0)
                        else f"📉 {format_currency_int(val - promedios_mensuales.get(mes, 0))}",
                        format_currency_int(volumen_total)
                    ] for mes, val in zip(all_months, valores_ordenados)]
                ))

            # Línea de promedio con marcadores especiales
            fig.add_trace(go.Scatter(
                x=all_months,
                y=promedio_valores,
                mode='lines+markers',
                name='📊 PROMEDIO',
                line=dict(color='#E74C3C', width=5),
                marker=dict(
                    size=15,
                    color='#E74C3C',
                    symbol='star',
                    line=dict(color='white', width=3)
                ),
                hovertemplate="<b>📊 Promedio</b> | %{x} | 💰 %{customdata}<extra></extra>",
                customdata=[format_currency_int(val)
                            for val in promedio_valores]
            ))

            fig.update_layout(
                height=700,
                plot_bgcolor=theme_styles['plot_bg'],
                paper_bgcolor=theme_styles['plot_bg'],
                font=dict(family="Inter", size=12,
                          color=theme_styles['text_color']),
                xaxis=dict(
                    showgrid=False,
                    tickangle=-45,
                    linecolor=theme_styles['line_color'],
                    linewidth=2
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor=theme_styles['grid_color'],
                    tickformat='$,.0f',
                    linecolor=theme_styles['line_color'],
                    linewidth=2
                ),
                barmode='group',
                bargap=0.15,
                bargroupgap=0.1,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.45,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=11),
                    bgcolor="rgba(255,255,255,0.8)" if theme == 'light' else "rgba(0,0,0,0.8)",
                    bordercolor=theme_styles['line_color'],
                    borderwidth=1
                ),
                margin=dict(t=100, b=160, l=80, r=40)
            )

        return fig

    except Exception as e:
        print(f"Error en update_comparativa_vendedores: {e}")
        fig = go.Figure()
        fig.add_annotation(
            text="Error al cargar datos de comparativa",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color='#e74c3c')
        )
        fig.update_layout(height=400)
        return fig


@callback(
    Output('ventas-graficos-area-individuales', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-theme-store', 'data')]
)
def update_area_charts_individuales(session_data, theme):
    """
    Create individual area charts for each vendor (4 per row, all vendors).
    """
    from utils import can_see_all_vendors

    try:
        theme_styles = get_theme_styles(theme)

        # Solo mostrar si es administrador
        if not session_data or not \
                can_see_all_vendors(session_data):
            fig = go.Figure()
            fig.add_annotation(
                text="Gráficos disponibles solo para administradores",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                # ← USAR THEME
                font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=300,
                paper_bgcolor=theme_styles['plot_bg'],
                plot_bgcolor=theme_styles['plot_bg']
            )
            return fig

        # Obtener datos para TODOS los vendedores (sin límite)
        # Excluir 'Todos'
        vendedores_disponibles = analyzer.vendedores_list[1:]
        datos_vendedores = {}

        # Incluir TODOS los vendedores que tengan al menos una venta > 0
        for vendedor in vendedores_disponibles:
            try:
                data_vendedor = analyzer.get_ventas_por_mes(vendedor)
                if not data_vendedor.empty and data_vendedor['valor_neto'].sum() > 0:
                    datos_vendedores[vendedor] = data_vendedor
            except:
                continue

        if not datos_vendedores:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos disponibles",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=300, paper_bgcolor=theme_styles['plot_bg'])
            return fig

        # Calcular layout de subplots (4 columnas)
        num_vendedores = len(datos_vendedores)
        cols = 4
        rows = math.ceil(num_vendedores / cols)

        # Crear títulos completos para los vendedores
        subplot_titles = []

        for vendedor in datos_vendedores.keys():
            subplot_titles.append(vendedor)

        # Crear subplots con títulos más pequeños y menos espacio vertical
        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=subplot_titles,
            vertical_spacing=0.08,  # Reducido de 0.15 a 0.08
            horizontal_spacing=0.08
        )

        # Colores modernos para cada vendedor
        modern_colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
            '#F8C471', '#82E0AA', '#F1948A', '#85C1E9', '#D7BDE2',
            '#AED6F1', '#A9DFBF', '#F9E79F', '#D2B4DE', '#85C1E9'
        ]

        # Añadir cada vendedor como área chart
        for i, (vendedor, data) in enumerate(datos_vendedores.items()):
            row = (i // cols) + 1
            col = (i % cols) + 1

            color = modern_colors[i % len(modern_colors)]

            fig.add_trace(
                go.Scatter(
                    x=data['mes_nombre'],
                    y=data['valor_neto'],
                    fill='tozeroy',
                    mode='lines+markers',
                    line=dict(color=color, width=3, shape='spline'),
                    marker=dict(size=6, color=color, line=dict(
                        color='white', width=1)),
                    fillcolor=f"rgba{tuple(list(px.colors.hex_to_rgb(color)) + [0.4])}",
                    name=vendedor,
                    showlegend=False,
                    hovertemplate="<b>" + vendedor + "</b><br>" +
                    "%{x}<br>" +
                    "💰 Ventas: %{customdata[0]}<br>" +
                    "📋 Facturas: %{customdata[1]}<br>" +
                    "<extra></extra>",
                    customdata=[[format_currency_int(val), facturas]
                                for val, facturas in zip(data['valor_neto'], data['documento_id'])]
                ),
                row=row, col=col
            )

        # Actualizar layout con títulos más pequeños y altura reducida
        fig.update_layout(
            title="📈 Evolución Individual por Vendedor (Gráficos de Área)",
            title_x=0.5,
            height=200 * rows,  # Reducido de 250 a 200 por fila
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=10,
                      color=theme_styles['text_color']),
            showlegend=False,
            margin=dict(t=80, b=40, l=60, r=60)
        )

        # Actualizar ejes individuales
        for i in range(1, rows + 1):
            for j in range(1, cols + 1):
                fig.update_xaxes(
                    showgrid=True,
                    gridcolor=theme_styles['grid_color'],
                    tickangle=-45,
                    tickfont=dict(size=8, color=theme_styles['text_color']),
                    linecolor=theme_styles['line_color'],
                    row=i, col=j
                )
                fig.update_yaxes(
                    showgrid=True,
                    gridcolor=theme_styles['grid_color'],
                    tickformat='$,.0f',
                    tickfont=dict(size=8, color=theme_styles['text_color']),
                    linecolor=theme_styles['line_color'],
                    row=i, col=j
                )

        # Actualizar títulos de subplots para que sean más pequeños
        for i in range(len(subplot_titles)):
            fig.layout.annotations[i].update(
                font=dict(size=10, color=theme_styles['text_color']))

        return fig

    except Exception as e:
        print(f"Error en update_area_charts_individuales: {e}")
        theme_styles = get_theme_styles(theme)

        fig = go.Figure()
        fig.add_annotation(
            text="Error al cargar gráficos de área",
            xref="paper", yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color=theme_styles['text_color'])
        )
        fig.update_layout(
            height=300,
            paper_bgcolor=theme_styles['plot_bg'],
            plot_bgcolor=theme_styles['plot_bg']
        )
        return fig


@callback(
    Output('ventas-row1-2-container', 'style'),
    [Input('session-store', 'data'),
     Input('ventas-theme-store', 'data')]
)
def update_comparativa_visibility(session_data, theme):
    """
    Mostrar/ocultar sección de comparativa según permisos del usuario.
    """
    from utils import can_see_all_vendors

    theme_styles = get_theme_styles(theme)

    try:
        if not session_data or not can_see_all_vendors(session_data):
            # Ocultar para usuarios normales
            return {'display': 'none'}
        else:
            # Mostrar para administradores
            return {
                'backgroundColor': theme_styles['paper_color'],
                'padding': '20px',
                'borderRadius': '8px',
                'boxShadow': theme_styles['card_shadow'],
                'margin': '10px 0',
                'color': theme_styles['text_color']
            }
    except Exception as e:
        print(f"Error en update_comparativa_visibility: {e}")
        return {'display': 'none'}


@callback(
    [Output('ventas-dropdown-vendedor-container', 'style'),
     Output('ventas-dropdown-vendedor-label', 'style')],
    [Input('session-store', 'data')]
)
def update_dropdown_visibility(session_data):
    """
    Mostrar/ocultar dropdown de vendedores según permisos del usuario.
    """
    from utils import can_see_all_vendors

    try:
        if not session_data or not can_see_all_vendors(session_data):
            # Ocultar para usuarios normales o sin sesión
            return {'display': 'none'}, {'display': 'none'}
        else:
            # Mostrar para administradores
            base_style = {
                'width': '20%',
                'display': 'inline-block',
                'verticalAlign': 'top',
                'marginLeft': '2%'
            }
            label_style = {
                'fontWeight': 'bold',
                'marginBottom': '5px',
                'fontFamily': 'Inter'
            }
            return base_style, label_style
    except Exception as e:
        print(f"Error en update_dropdown_visibility: {e}")
        return {'display': 'none'}, {'display': 'none'}


@callback(
    [Output('ventas-theme-store', 'data'),
     Output('ventas-theme-toggle', 'children'),
     Output('ventas-main-container', 'style'),
     Output('ventas-header-container', 'style')],
    [Input('ventas-theme-toggle', 'n_clicks')],
    [State('ventas-theme-store', 'data')]
)
def toggle_theme(n_clicks, current_theme):
    """Toggle between light and dark themes."""
    if n_clicks % 2 == 1:
        new_theme = 'dark'
        icon = '☀️'
    else:
        new_theme = 'light'
        icon = '🌙'

    theme_styles = get_theme_styles(new_theme)

    main_style = {
        'fontFamily': 'Inter',
        'backgroundColor': theme_styles['bg_color'],
        'padding': '20px',
        'color': theme_styles['text_color']
    }

    header_style = {
        'marginBottom': '30px',
        'padding': '20px',
        'backgroundColor': theme_styles['paper_color'],
        'borderRadius': '8px'
    }

    return new_theme, icon, main_style, header_style


# Dropdown theme styling callback
@callback(
    [Output('ventas-dropdown-vendedor', 'style'),
     Output('ventas-dropdown-mes', 'style'),
     Output('ventas-dropdown-cliente', 'style'),
     Output('ventas-dropdown-vista-recaudo', 'style'),
     Output('ventas-dropdown-tipo-grafico', 'style'),
     Output('ventas-dropdown-vendedor', 'className'),
     Output('ventas-dropdown-mes', 'className'),
     Output('ventas-dropdown-cliente', 'className'),
     Output('ventas-dropdown-vista-recaudo', 'className'),
     Output('ventas-dropdown-tipo-grafico', 'className')],
    [Input('ventas-theme-store', 'data'),
     Input('session-store', 'data')]
)
def update_dropdown_styles(theme, session_data):
    """
    Update dropdown styles based on theme and visibility.
    """
    from utils import can_see_all_vendors

    dropdown_style = get_dropdown_style(theme)
    dropdown_style['fontFamily'] = 'Inter'

    # Special handling for vendor dropdown - hide if not admin
    if not session_data or not can_see_all_vendors(session_data):
        vendedor_style = {'display': 'none'}
        tipo_grafico_style = {'display': 'none'}
    else:
        vendedor_style = dropdown_style.copy()
        tipo_grafico_style = dropdown_style.copy()
        tipo_grafico_style.update(
            {'width': '250px', 'display': 'inline-block'})

    vista_style = dropdown_style.copy()
    vista_style.update({'width': '200px', 'display': 'inline-block'})

    # CSS class for dark theme
    css_class = 'dash-dropdown dark-theme' if theme == 'dark' else 'dash-dropdown'

    return vendedor_style, dropdown_style, dropdown_style, vista_style, tipo_grafico_style, css_class, css_class, css_class, css_class, css_class


@callback(
    [Output('ventas-card-1', 'style'),
     Output('ventas-card-2', 'style'),
     Output('ventas-card-3', 'style'),
     Output('ventas-card-4', 'style'),
     Output('ventas-card-5', 'style'),
     Output('ventas-card-6', 'style'),
     Output('ventas-card-7', 'style'),
     Output('ventas-card-8', 'style')],
    [Input('ventas-theme-store', 'data')]
)
def update_card_styles(theme):
    """
    Update styles for summary cards based on theme.
    """
    theme_styles = get_theme_styles(theme)

    card_style = {
        'backgroundColor': theme_styles['paper_color'],
        'padding': '15px',
        'borderRadius': '8px',
        'boxShadow': theme_styles['card_shadow'],
        'textAlign': 'center',
        'width': '20%',
        'display': 'inline-block',
        'margin': '1.5%',
        'color': theme_styles['text_color']
    }

    return [card_style] * 8


# Container styles callback
@callback(
    [Output('ventas-row1-container', 'style'),
     #  Output('ventas-row1-2-container', 'style'),
     #  Output('ventas-row1-3-container', 'style'),
     Output('ventas-row1-5-container', 'style'),
     Output('ventas-row-nueva-treemap', 'style'),
     Output('ventas-row2-container', 'style'),
     Output('ventas-row2-5-container', 'style'),
     Output('ventas-row3-container', 'style'),
     Output('ventas-row4-container', 'style'),
     Output('ventas-row5-container', 'style'),
     Output('ventas-row6-container', 'style')],
    [Input('ventas-theme-store', 'data')]
)
def update_container_styles(theme):
    """
    Update styles for chart containers based on theme.
    """
    theme_styles = get_theme_styles(theme)

    chart_style = \
        {
            'backgroundColor': theme_styles['paper_color'],
            'padding': '20px',
            'borderRadius': '8px',
            'boxShadow': theme_styles['card_shadow'],
            'margin': '10px 0',
            'color': theme_styles['text_color']
        }

    return [chart_style] * 9  # 10 containers now


@callback(
    [Output('ventas-container-vendedor', 'style'),
     Output('ventas-vista-recaudo-container', 'style'),
     Output('ventas-titulo-recaudo-temporal', 'children')],
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-vista-recaudo', 'value')]
)
def update_recaudo_visibility(session_data, dropdown_value, vista_recaudo):
    """
    Show/hide recaudo components based on vendor selection.
    """
    vendedor = get_selected_vendor(session_data, dropdown_value)

    if vendedor == 'Todos':
        # Show vendor chart and vista selector
        vendor_style = {'width': '100%',
                        'marginBottom': '20px', 'display': 'block'}
        vista_style = {'display': 'flex', 'alignItems': 'center',
                       'justifyContent': 'center', 'marginBottom': '20px'}
        titulo_temporal = f"Evolución {vista_recaudo.title()} - Todos los Vendedores"
    else:
        # Hide vendor chart, still show vista selector
        vendor_style = {'display': 'none'}
        vista_style = {'display': 'flex', 'alignItems': 'center',
                       'justifyContent': 'center', 'marginBottom': '20px'}
        titulo_temporal = f"Evolución {vista_recaudo.title()} - {vendedor}"

    return vendor_style, vista_style, titulo_temporal


@callback(
    Output('ventas-titulo-dashboard', 'children'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value')]
)
def update_title(session_data, dropdown_value, mes):
    """
    Update dashboard title based on filters.
    """
    from utils import can_see_all_vendors, get_user_vendor_filter

    try:
        if not session_data:
            return "Dashboard de Ventas"

        if can_see_all_vendors(session_data):
            vendedor = dropdown_value if dropdown_value else 'Todos'
            title = "Dashboard de Ventas"
            if vendedor != 'Todos' and mes != 'Todos':
                title += f" - {vendedor} - {mes}"
            elif vendedor != 'Todos':
                title += f" - {vendedor}"
            elif mes != 'Todos':
                title += f" - {mes}"
            else:
                title += " - Todos los Vendedores"
            return title
        else:
            vendor = get_user_vendor_filter(session_data)
            title = f"Dashboard de Ventas - {vendor}"
            if mes != 'Todos':
                title += f" - {mes}"
            return title
    except Exception as e:
        print(f"Error en update_title: {e}")
        return "Dashboard de Ventas"


@callback(
    [
        Output('ventas-ventas-totales', 'children'),
        Output('ventas-ventas-netas', 'children'),
        Output('ventas-total-devoluciones', 'children'),
        Output('ventas-total-descuentos', 'children'),
        Output('ventas-valor-promedio', 'children'),
        Output('ventas-num-facturas', 'children'),
        Output('ventas-num-devoluciones', 'children'),
        Output('ventas-num-clientes', 'children')],
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-btn-actualizar', 'n_clicks')]
)
def update_cards(session_data, dropdown_value, mes, n_clicks):
    """
    Update summary cards with sales statistics.
    """
    try:
        vendedor = \
            get_selected_vendor(session_data, dropdown_value)
        resumen = \
            analyzer.get_resumen_ventas(vendedor, mes)

        return \
            (
                format_currency_int(resumen['total_ventas']),
                format_currency_int(resumen['ventas_netas']),
                format_currency_int(resumen['total_devoluciones']),
                format_currency_int(resumen['total_descuentos']),
                format_currency_int(resumen['ticket_promedio']),
                f"{resumen['num_facturas']:,}",
                f"{resumen['num_devoluciones']:,}",
                f"{resumen['num_clientes']:,}",
            )
    except Exception as e:
        print(f"Error en update_cards: {e}")
        return "$0", "$0", "0", "$0", "0", "0", "$0", "0%"


@callback(
    Output('ventas-grafico-ventas-mes', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-theme-store', 'data')]
)
def update_ventas_mes(session_data, dropdown_value, theme):
    """
    Update monthly sales evolution chart with area fill and smooth lines.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_ventas_por_mes(vendedor)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos disponibles",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=400,
                paper_bgcolor=theme_styles['plot_bg'],
                plot_bgcolor=theme_styles['plot_bg'],
                font=dict(color=theme_styles['text_color'])
            )
            return fig

        fig = go.Figure()

        # Área azul moderna con gradiente
        fig.add_trace(go.Scatter(
            x=data['mes_nombre'],
            y=data['valor_neto'],
            mode='lines+markers',
            name='Ventas',
            line=dict(
                color='rgba(74, 144, 226, 0.9)',  # Azul moderno
                width=4,
                shape='spline',  # Líneas redondeadas/suaves
                smoothing=1.0    # Máximo suavizado
            ),
            marker=dict(
                size=10,
                color='rgba(74, 144, 226, 1.0)',
                line=dict(color='white', width=3),
                symbol='circle'
            ),
            fill='tozeroy',  # Rellenar hasta el eje Y (área)
            fillcolor='rgba(74, 144, 226, 0.2)',  # Azul claro transparente
            hovertemplate="<b>%{x}</b><br>Ventas: %{customdata}<br>Facturas: %{text}<extra></extra>",
            customdata=[format_currency_int(val)
                        for val in data['valor_neto']],
            text=data['documento_id']
        ))

        fig.update_layout(
            height=400,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=12,
                      color=theme_styles['text_color']),
            xaxis=dict(
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                tickangle=-45,
                title="Mes",
                tickfont=dict(color=theme_styles['text_color']),
                linecolor=theme_styles['line_color']
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                tickformat='$,.0f',
                title="Ventas ($)",
                tickfont=dict(color=theme_styles['text_color']),
                linecolor=theme_styles['line_color']
            ),
            showlegend=False,
            margin=dict(t=20, b=80, l=80, r=20),
            hovermode='x unified'
        )

        return fig
    except Exception as e:
        print(f"Error en update_ventas_mes: {e}")
        return go.Figure()


@callback(
    Output('ventas-grafico-estacionalidad', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-theme-store', 'data')]
)
def update_estacionalidad(session_data, dropdown_value, mes, theme):
    """
    Update seasonality chart by day of week with pastel colors and transparency.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_ventas_por_dia_semana(vendedor, mes)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            fig = go.Figure()
            fig.add_annotation(text="No hay datos disponibles", xref="paper", yref="paper",
                               x=0.5, y=0.5, showarrow=False, font=dict(size=16, color=theme_styles['text_color']))
            fig.update_layout(
                height=400, paper_bgcolor=theme_styles['plot_bg'])
            return fig

        # Colores pasteles con transparencia
        pastel_colors = [
            'rgba(173, 216, 230, 0.6)',  # Light Blue
            'rgba(255, 182, 193, 0.6)',  # Light Pink
            'rgba(144, 238, 144, 0.6)',  # Light Green
            'rgba(255, 218, 185, 0.6)',  # Peach
            'rgba(221, 160, 221, 0.6)',  # Plum
            'rgba(175, 238, 238, 0.6)',  # Pale Turquoise
            'rgba(211, 211, 211, 0.6)'   # Light Gray
        ]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=data['dia_semana_es'],
            y=data['valor_neto'],
            marker=dict(
                color=[pastel_colors[i % len(pastel_colors)]
                       for i in range(len(data))],
                line=dict(color='white', width=2),
                opacity=0.8  # Transparencia adicional
            ),
            text=[format_currency_int(val) for val in data['valor_neto']],
            textposition='outside',
            textfont=dict(size=10, color=theme_styles['text_color']),
            hovertemplate="<b>%{x}</b><br>" +
                         "Ventas: %{customdata[0]}<br>" +
                         "Facturas: %{customdata[1]}<br>" +
                         "<extra></extra>",
            customdata=[[format_currency_int(val), facturas] for val, facturas in zip(
                data['valor_neto'], data['documento_id'])]
        ))

        fig.update_layout(
            height=400,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=12,
                      color=theme_styles['text_color']),
            xaxis=dict(
                showgrid=False,
                title="Día de la Semana"
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                tickformat='$,.0f',
                title="Ventas ($)"
            ),
            showlegend=False,
            margin=dict(t=20, b=60, l=80, r=20)
        )

        return fig
    except Exception as e:
        print(f"Error en update_estacionalidad: {e}")
        return go.Figure()


@callback(
    Output('ventas-treemap-dias-sin-venta', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-theme-store', 'data')]
)
def update_treemap_dias_sin_venta(session_data, dropdown_value, theme):
    """
    Update days without sales treemap.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_dias_sin_venta_por_cliente(vendedor)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay clientes sin ventas recientes",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False,
                font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=500, paper_bgcolor=theme_styles['plot_bg'])
            return fig

        # Create labels with client name and days
        labels = [f"{cliente}<br>{dias} días" for cliente, dias in
                  zip(data['cliente_completo'], data['dias_sin_venta'])]

        # Format dates safely
        fechas_formatted = []
        for fecha in data['fecha']:
            try:
                if pd.isna(fecha):
                    fechas_formatted.append("Sin fecha")
                else:
                    fechas_formatted.append(
                        pd.to_datetime(fecha).strftime('%Y-%m-%d'))
            except:
                fechas_formatted.append("Sin fecha")

        # Create treemap with size based on days without sales
        fig = go.Figure(go.Treemap(
            labels=labels,
            values=data['dias_sin_venta'],  # Size by days without sales
            parents=[""] * len(data),
            texttemplate="<b>%{label}</b><br>Ventas: %{customdata}",
            hovertemplate="<b>%{text}</b><br>" +
                         # %{value} now shows days
                         "Días sin venta: %{value}<br>" +
                         "Ventas históricas: %{customdata[0]}<br>" +
                         "Última venta: %{customdata[1]}<br>" +
                         "<extra></extra>",
            text=[cliente[:80] + "..." if len(cliente) > 80 else cliente
                  for cliente in data['cliente_completo']],
            customdata=[[format_currency_int(ventas), fecha_str]
                        for ventas, fecha_str in zip(
                data['valor_neto'],
                fechas_formatted)],
            marker=dict(
                colors=data['dias_sin_venta'],  # Color by days without sales
                # Red to Blue, reversed (red = more days)
                colorscale='RdYlBu_r',
                colorbar=dict(title="Días sin venta"),
                line=dict(width=2, color='white'),
                cmin=data['dias_sin_venta'].min(),
                cmax=data['dias_sin_venta'].max()
            ),
            textfont=dict(size=10, color='white')
        ))

        fig.update_layout(
            height=500,
            font=dict(family="Inter", size=12,
                      color=theme_styles['text_color']),
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            margin=dict(t=0, b=0, l=0, r=0)
        )

        return fig
    except Exception as e:
        print(f"Error en update_treemap_dias_sin_venta: {e}")
        return go.Figure()


@callback(
    Output('ventas-grafico-zona', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-theme-store', 'data')]
)
def update_zona(session_data, dropdown_value, mes, theme):
    """
    Update sales by zone chart with red-to-green color scale and transparency.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_ventas_por_zona(vendedor, mes)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            fig = go.Figure()
            fig.add_annotation(text="No hay datos disponibles", xref="paper", yref="paper",
                               x=0.5, y=0.5, showarrow=False, font=dict(size=16, color=theme_styles['text_color']))
            fig.update_layout(
                height=350,
                paper_bgcolor=theme_styles['plot_bg'],
                plot_bgcolor=theme_styles['plot_bg']
            )
            return fig

        # Normalizar valores para escala de color (0-1)
        min_val = data['valor_neto'].min()
        max_val = data['valor_neto'].max()

        # Crear colores basados en escala rojo-verde con transparencia
        colors_red_to_green = []
        for val in data['valor_neto']:
            if max_val == min_val:
                normalized = 0.5  # Si todos son iguales, usar color medio
            else:
                normalized = (val - min_val) / (max_val - min_val)

            # Escala de rojo (0) a verde (1)
            if normalized <= 0.5:
                # De rojo a amarillo
                red = 255
                green = int(255 * (normalized * 2))
                blue = 0
            else:
                # De amarillo a verde
                red = int(255 * (2 - normalized * 2))
                green = 255
                blue = 0

            # Agregar transparencia
            alpha = 0.8
            colors_red_to_green.append(
                f'rgba({red}, {green}, {blue}, {alpha})')

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=data['zona'],
            y=data['valor_neto'],
            marker=dict(
                color=colors_red_to_green,
                line=dict(color='white', width=2),
                opacity=0.4
            ),
            text=[format_currency_int(val) for val in data['valor_neto']],
            textposition='outside',
            textfont=dict(size=10, color=theme_styles['text_color']),
            hovertemplate="<b>%{x}</b><br>Ventas: %{customdata[0]}<br>Clientes: %{customdata[1]}<extra></extra>",
            customdata=[[format_currency_int(val), clientes] for val, clientes in zip(
                data['valor_neto'], data['cliente'])]
        ))

        fig.update_layout(
            height=350,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=12,
                      color=theme_styles['text_color']),
            xaxis=dict(
                tickangle=-45,
                showgrid=False,
                tickfont=dict(color=theme_styles['text_color']),
                linecolor=theme_styles['line_color']
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                tickformat='$,.0f',
                tickfont=dict(color=theme_styles['text_color']),
                linecolor=theme_styles['line_color']
            ),
            showlegend=False,
            margin=dict(t=20, b=80, l=80, r=20)
        )

        return fig
    except Exception as e:
        print(f"Error en update_zona: {e}")
        return go.Figure()


@callback(
    Output('ventas-grafico-forma-pago', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-theme-store', 'data')]
)
def update_forma_pago(session_data, dropdown_value, mes, theme):
    """
    Update payment method chart.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_forma_pago_distribution(vendedor, mes)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos disponibles",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=350,
                paper_bgcolor=theme_styles['plot_bg']
            )
            return fig

        fig = go.Figure(data=[go.Pie(
            labels=data['forma_pago'],
            values=data['valor_neto'],
            hole=.4,
            opacity=0.6,
            textinfo='percent',
            marker=dict(colors=['#3498DB', '#E74C3C', '#2ECC71', '#F39C12',
                        '#9B59B6'], line=dict(color='#FFFFFF', width=2)),
            hovertemplate="<b>%{label}</b><br>Ventas: %{customdata}<br>Porcentaje: %{percent}<extra></extra>",
            customdata=[format_currency_int(val) for val in data['valor_neto']]
        )])

        fig.update_layout(
            height=350,
            font=dict(family="Inter", size=12,
                      color=theme_styles['text_color']),
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle",
                        y=0.5, xanchor="left", x=1.05),
            margin=dict(t=0, b=0, l=0, r=150)
        )

        return fig
    except Exception as e:
        print(f"Error en update_forma_pago: {e}")
        return go.Figure()


@callback(
    Output('ventas-treemap-ventas', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-theme-store', 'data')]
)
def update_treemap(session_data, dropdown_value, mes, theme):
    """
    Update sales treemap.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_treemap_data(vendedor, mes)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            fig = go.Figure()
            fig.add_annotation(text="No hay datos disponibles", xref="paper", yref="paper",
                               x=0.5, y=0.5, showarrow=False, font=dict(size=16, color=theme_styles['text_color']))
            fig.update_layout(
                height=500, paper_bgcolor=theme_styles['plot_bg'])
            return fig

        fig = go.Figure(go.Treemap(
            labels=data['cliente_completo'],
            values=data['valor_neto'],
            parents=[""] * len(data),
            texttemplate="<b>%{label}</b><br>%{customdata}",
            hovertemplate="<b>%{label}</b><br>Ventas: %{customdata}<br><extra></extra>",
            customdata=[format_currency_int(val)
                        for val in data['valor_neto']],
            marker=dict(colorscale='Aggrnyl_r', colorbar=dict(
                title="Ventas"), line=dict(width=2, color='white')),
            textfont=dict(size=12, color='white')
        ))

        fig.update_layout(
            height=500,
            font=dict(family="Inter", size=12,
                      color=theme_styles['text_color']),
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            margin=dict(t=0, b=0, l=0, r=0)
        )

        return fig
    except Exception as e:
        print(f"Error en update_treemap: {e}")
        return go.Figure()


@callback(
    Output('ventas-top-clientes', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-theme-store', 'data')]
)
def update_top_clientes(session_data, dropdown_value, mes, theme):
    """
    Update top customers chart.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_top_clientes(vendedor, mes)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos disponibles",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=400, paper_bgcolor=theme_styles['plot_bg'])
            return fig

        data_sorted = data.sort_values('valor_neto', ascending=True)
        data_sorted['rank'] = sorted(
            range(1, len(data_sorted) + 1), reverse=True)
        data_sorted['short_label'] = [f"#{i}" for i in data_sorted['rank']]

        fig = px.bar(
            data_sorted,
            x='valor_neto',
            y='short_label',
            orientation='h',
            color='valor_neto',
            color_continuous_scale='Blugrn'
        )

        fig.update_traces(
            text=[
                name[:50] + "..." if len(name) > 50 else name for name in data_sorted['cliente_completo']],
            textposition='inside',
            textfont=dict(color='white', size=10),
            hovertemplate="<b>%{customdata[0]}</b><br>Ventas: %{customdata[1]}<br>Facturas: %{customdata[2]}<extra></extra>",
            customdata=[[cliente, format_currency_int(ventas), facturas] for cliente, ventas, facturas in zip(
                data_sorted['cliente_completo'], data_sorted['valor_neto'], data_sorted['documento_id'])]
        )

        fig.update_layout(
            height=400,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=12,
                      color=theme_styles['text_color']),
            xaxis=dict(tickformat='$,.0f', showgrid=True,
                       gridcolor=theme_styles['grid_color']),
            yaxis=dict(title="Ranking", categoryorder='array',
                       categoryarray=data_sorted['short_label']),
            showlegend=False,
            margin=dict(t=20, b=40, l=80, r=80)
        )

        return fig
    except Exception as e:
        print(f"Error en update_top_clientes: {e}")
        return go.Figure()


# Callback para actualizar lista de clientes
@callback(
    Output('ventas-dropdown-cliente', 'options'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value')]
)
def update_clientes_dropdown(session_data, dropdown_value):
    """
    Update client dropdown based on selected salesperson.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        clientes = analyzer.get_clientes_list(vendedor)
        return [{'label': cliente, 'value': cliente} for cliente in clientes]
    except Exception as e:
        print(f"Error en update_clientes_dropdown: {e}")
        return [{'label': 'Seleccione un cliente', 'value': 'Seleccione un cliente'}]


# Callback para limpiar selección de cliente cuando cambia vendedor
@callback(
    Output('ventas-dropdown-cliente', 'value'),
    [Input('ventas-dropdown-vendedor', 'value')]
)
def reset_cliente_selection(vendedor):
    """
    Reset client selection when salesperson changes.
    """
    return 'Seleccione un cliente'


@callback(
    Output('ventas-grafico-evolucion-cliente', 'figure'),
    [Input('ventas-dropdown-cliente', 'value'),
     Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-theme-store', 'data')]
)
def update_evolucion_cliente(cliente, session_data, dropdown_value, mes, theme):
    """
    Update client evolution chart - filtered by month using main DataFrame.
    """
    try:
        vendedor = \
            get_selected_vendor(session_data, dropdown_value)
        theme_styles = \
            get_theme_styles(theme)

        if cliente == 'Seleccione un cliente':
            fig = go.Figure()
            fig.add_annotation(
                text="Seleccione un cliente para ver su evolución diaria de ventas",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False,
                font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=400,
                plot_bgcolor=theme_styles['plot_bg'],
                paper_bgcolor=theme_styles['plot_bg'],
                font=dict(family="Inter", size=12,
                          color=theme_styles['text_color'])
            )
            return fig

        # Filter dataframe based on client's name
        data_filtered = df[df['cliente_completo'] == cliente].copy()

        # Filtro por vendedor
        if vendedor and vendedor != 'Todos':
            data_filtered = data_filtered[data_filtered['vendedor'] == vendedor]

        # FILTRO POR MES - AQUÍ ES DONDE ESTABA EL PROBLEMA
        if mes and mes != 'Todos':
            data_filtered = data_filtered[data_filtered['mes_nombre'] == mes]
            print(
                f"Filtrando {cliente} por mes {mes}: {len(data_filtered)} registros")

        if data_filtered.empty:
            mensaje = f"No hay datos para {cliente}"
            if mes != 'Todos':
                mensaje += f" en {mes}"

            fig = go.Figure()
            fig.add_annotation(
                text=mensaje,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                xanchor='center',
                yanchor='middle',
                showarrow=False,
                font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=400,
                plot_bgcolor=theme_styles['plot_bg'],
                paper_bgcolor=theme_styles['plot_bg'],
                font=dict(family="Inter", size=12,
                          color=theme_styles['text_color'])
            )
            return fig

        # Crear fecha_str si no existe
        data_filtered = data_filtered.copy()
        data_filtered['fecha_str'] = pd.to_datetime(
            data_filtered['fecha']).dt.strftime('%Y-%m-%d')

        # Agrupar por fecha para obtener ventas diarias
        data = data_filtered.groupby(['fecha', 'fecha_str']).agg({
            'valor_neto': 'sum',
            'documento_id': 'count'
        }).reset_index().sort_values('fecha')

        # Calcular total del período FILTRADO
        total_ventas_periodo = data['valor_neto'].sum()
        num_dias = len(data)

        # Create bar chart
        fig = go.Figure()

        pastel_colors = [
            'rgba(144, 238, 144, 0.8)', 'rgba(173, 216, 230, 0.8)',
            'rgba(255, 218, 185, 0.8)', 'rgba(221, 160, 221, 0.8)',
            'rgba(175, 238, 238, 0.8)', 'rgba(255, 182, 193, 0.8)'
        ]

        bar_colors = \
            [
                pastel_colors[i % len(pastel_colors)] for i in range(len(data))
            ]

        fig.add_trace(go.Bar(
            x=data['fecha_str'],
            y=data['valor_neto'],
            marker=dict(
                color=bar_colors,
                line=dict(color='white', width=1)
            ),
            text=[format_currency_int(
                val) if val > 50000 else '' for val in data['valor_neto']],
            textposition='outside',
            textfont=dict(size=9, color=theme_styles['text_color']),
            hovertemplate="<b>%{x}</b><br>" +
                         "Ventas: %{customdata[0]}<br>" +
                         "Facturas: %{customdata[1]}<br>" +
                         "<extra></extra>",
            customdata=[[format_currency_int(val), facturas] for val, facturas in zip(
                data['valor_neto'], data['documento_id'])]
        ))

        # Título con información específica del período
        cliente_corto = cliente[:80] + '...' if len(cliente) > 80 else cliente

        if mes != 'Todos':
            titulo_completo = f"{cliente_corto} - {mes}<br><sub>Total: {format_currency_int(total_ventas_periodo)} ({num_dias} días)</sub>"
        else:
            titulo_completo = f"{cliente_corto}<br><sub>Total: {format_currency_int(total_ventas_periodo)} ({num_dias} días)</sub>"

        fig.update_layout(
            title=dict(
                text=titulo_completo,
                x=0.5,
                font=dict(size=14, color=theme_styles['text_color'])
            ),
            height=450,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=12,
                      color=theme_styles['text_color']),
            xaxis=dict(
                title="Fecha",
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                linecolor=theme_styles['line_color'],
                tickangle=-45,
                type='category',
                tickfont=dict(color=theme_styles['text_color'])
            ),
            yaxis=dict(
                title="Ventas ($)",
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                linecolor=theme_styles['line_color'],
                tickformat='$,.0f',
                tickfont=dict(color=theme_styles['text_color'])
            ),
            showlegend=False,
            margin=dict(t=80, b=80, l=80, r=40)
        )

        return fig
    except Exception as e:
        print(f"Error en update_evolucion_cliente: {e}")
        return go.Figure()


@callback(
    Output('ventas-treemap-acumuladas', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-theme-store', 'data')]
)
def update_treemap_acumuladas(session_data, dropdown_value, mes, theme):
    """
    Update accumulated sales treemap.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_ventas_acumuladas_mes(mes, vendedor)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            fig = go.Figure()
            mensaje = f"No hay datos acumulados" + \
                (f" hasta {mes}" if mes != 'Todos' else "")
            fig.add_annotation(
                text=mensaje,
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False,
                font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=400, paper_bgcolor=theme_styles['plot_bg'])
            return fig

        fig = go.Figure(go.Treemap(
            labels=data['cliente_completo'],
            values=data['valor_neto'],
            parents=[""] * len(data),
            texttemplate="<b>%{label}</b><br>%{customdata}",
            hovertemplate="<b>%{label}</b><br>Ventas Acumuladas: %{customdata}<br>Facturas: %{text}<extra></extra>",
            customdata=[format_currency_int(val)
                        for val in data['valor_neto']],
            text=data['documento_id'],
            marker=dict(
                colorscale='Agsunset_r',
                colorbar=dict(title="Ventas Acumuladas"),
                line=dict(width=2, color='white')
            ),
            textfont=dict(size=12, color='white')
        ))

        fig.update_layout(
            height=500,  # Increased height since it's now alone in its row
            font=dict(family="Inter", size=12,
                      color=theme_styles['text_color']),
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            margin=dict(t=0, b=0, l=0, r=0)
        )

        return fig
    except Exception as e:
        print(f"Error en update_treemap_acumuladas: {e}")
        return go.Figure()


@callback(
    Output('ventas-total-recaudo-titulo', 'children'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value')]
)
def update_titulo_recaudo(session_data, dropdown_value, mes):
    """
    Update collection title with total amount.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        total_recaudo = analyzer.get_resumen_recaudo(vendedor, mes)
        periodo_text = f" - {vendedor}" if vendedor != 'Todos' else ""
        mes_text = f" - {mes}" if mes != 'Todos' else ""
        return f"Recaudo Total{periodo_text}{mes_text}: {format_currency_int(total_recaudo)}"
    except Exception as e:
        print(f"Error en update_titulo_recaudo: {e}")
        return "Recaudo Total: $0"


@callback(
    Output('ventas-grafico-clientes-impactados', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-theme-store', 'data')]
)
def update_clientes_impactados(session_data, dropdown_value, theme):
    """
    Update clients impacted chart with horizontal bars and total clients bar.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data, porcentaje_promedio, total_clientes = analyzer.get_clientes_impactados_por_periodo(
            vendedor)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos de clientes impactados",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False,
                font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=400, paper_bgcolor=theme_styles['plot_bg'])
            return fig

        fig = go.Figure()

        # Add total clients bar (background) - one trace for all months
        fig.add_trace(go.Bar(
            x=[total_clientes] * len(data),
            y=data['mes_nombre'],
            orientation='h',
            name='Total Clientes',
            marker=dict(color='#ecf0f1', opacity=0.7),
            hovertemplate="<b>%{y}</b><br>Total Clientes: %{x}<extra></extra>"
        ))

        # Calculate percentages for text display
        percentages = [(row['clientes_impactados'] / total_clientes * 100) if total_clientes > 0 else 0
                       for _, row in data.iterrows()]

        # Add impacted clients bar (foreground) - one trace for all months
        fig.add_trace(go.Bar(
            x=data['clientes_impactados'],
            y=data['mes_nombre'],
            orientation='h',
            name='Clientes Impactados',
            marker=dict(color='#3498db', opacity=0.9),
            text=[f"{pct:.1f}%" for pct in percentages],
            textposition='inside',
            textfont=dict(color='white', size=10, family='Inter'),
            hovertemplate="<b>%{y}</b><br>" +
                         "Clientes Impactados: %{x}<br>" +
                         "Porcentaje: %{text}<br>" +
                         "Ventas: %{customdata[0]}<br>" +
                         "Facturas: %{customdata[1]}<br>" +
                         "<extra></extra>",
            customdata=[[format_currency_int(row['valor_neto']), row['documento_id']]
                        for _, row in data.iterrows()]
        ))

        # Update layout for horizontal bar chart
        fig.update_layout(
            title=f"Impacto Promedio: {porcentaje_promedio:.1f}% ({total_clientes:,} clientes totales)",
            title_x=0.5,
            xaxis_title="Número de Clientes",
            yaxis_title="Mes",
            height=400,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=12,
                      color=theme_styles['text_color']),
            xaxis=dict(
                showgrid=True,
                gridcolor=theme_styles['grid_color']
            ),
            yaxis=dict(
                categoryorder='array',
                categoryarray=data['mes_nombre'].tolist()
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(t=80, b=60, l=100, r=40),
            barmode='overlay'
        )

        return fig
    except Exception as e:
        print(f"Error en update_clientes_impactados: {e}")
        return go.Figure()


@callback(
    Output('ventas-tabla-convenios', 'children'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-theme-store', 'data')]
)
def update_tabla_convenios(session_data, dropdown_value, mes, theme):
    """
    Update convenios analysis table with enhanced design and expected sales.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_analisis_convenios(vendedor, mes)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            return html.Div([
                html.P("No hay datos de convenios disponibles o no se encontraron coincidencias por NIT.",
                       style={'textAlign': 'center', 'color': 'gray', 'fontSize': '16px', 'fontFamily': 'Inter'})
            ])

        # Get expected percentage (same for all rows)
        progreso_esperado = data['progreso_esperado_pct'].iloc[0] if len(
            data) > 0 else 0

        def create_progress_bar(percentage, status_color='#27ae60', width="100px", height="20px"):
            """
            Create a progress bar with status-based color.
            """
            bar_content = [
                html.Div(
                    style={
                        'width': f'{min(percentage, 100)}%',
                        'height': '100%',
                        'backgroundColor': status_color,
                        'borderRadius': '3px',
                        'transition': 'width 0.3s ease'
                    }
                )
            ]

            return html.Div([
                html.Div(bar_content, style={
                    'width': width,
                    'height': height,
                    'backgroundColor': '#ecf0f1',
                    'borderRadius': '3px',
                    'position': 'relative',
                    'border': '1px solid #bdc3c7'
                }),
                html.Div(f"{percentage:.1f}%", style={
                    'fontSize': '10px',
                    'fontWeight': 'bold',
                    'marginTop': '2px',
                    'textAlign': 'center'
                })
            ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'})

        # Create table rows
        table_rows = []

        # Header
        header = html.Tr([
            html.Th("Cliente", style={'padding': '12px', 'backgroundColor': '#34495e',
                    'color': 'white', 'fontFamily': 'Inter', 'fontSize': '12px', 'textAlign': 'left'}),
            html.Th("Vendedor", style={'padding': '12px', 'backgroundColor': '#34495e',
                    'color': 'white', 'fontFamily': 'Inter', 'fontSize': '12px', 'textAlign': 'center'}),
            html.Th("Ventas", style={'padding': '12px', 'backgroundColor': '#34495e',
                    'color': 'white', 'fontFamily': 'Inter', 'fontSize': '12px', 'textAlign': 'center'}),
            html.Th("Ventas Esperadas", style={'padding': '12px', 'backgroundColor': '#34495e',
                    'color': 'white', 'fontFamily': 'Inter', 'fontSize': '12px', 'textAlign': 'center'}),
            html.Th("Meta", style={'padding': '12px', 'backgroundColor': '#34495e',
                    'color': 'white', 'fontFamily': 'Inter', 'fontSize': '12px', 'textAlign': 'center'}),
            html.Th("% Cumplimiento", style={'padding': '12px', 'backgroundColor': '#34495e',
                    'color': 'white', 'fontFamily': 'Inter', 'fontSize': '12px', 'textAlign': 'center'}),
            html.Th("Estado", style={'padding': '12px', 'backgroundColor': '#34495e',
                    'color': 'white', 'fontFamily': 'Inter', 'fontSize': '12px', 'textAlign': 'center'})
        ])

        # Data rows
        for _, row in data.iterrows():
            # Determine overall status comparing % Cumplimiento with % Esperado
            progreso_actual = row['progreso_meta_pct']
            cumple_meta = row['cumplimiento_meta']
            adelantado = progreso_actual > progreso_esperado  # Above expected progress
            cerca_esperado = progreso_actual >= (
                progreso_esperado - 5)  # Within 5% of expected progress

            if cumple_meta:
                estado_text = '🟢 Cumplió'
                estado_color = '#27ae60'  # Verde
            elif adelantado:
                estado_text = '🟡 Adelantado'
                estado_color = '#f3c212'  # Verde-Amarillo (YellowGreen)
            elif cerca_esperado:
                estado_text = '🟠 Cerca'
                estado_color = '#FF8C00'  # Naranja
            else:
                estado_text = '🔴 Atrasado'
                estado_color = '#e74c3c'  # Rojo

            table_row = html.Tr([
                # Cliente (left aligned)
                html.Td([
                    html.Div(row['client_name'][:50] + "..." if len(row['client_name']) > 50 else row['client_name'],
                             style={'fontWeight': 'bold', 'fontSize': '11px'}),
                    html.Div(f"NIT: {row['nit']}", style={
                             'fontSize': '9px', 'color': '#7f8c8d'})
                ], style={'padding': '8px', 'borderBottom': '1px solid #ddd', 'fontFamily': 'Inter', 'textAlign': 'left'}),

                # All other columns centered
                html.Td(row['seller_name'][:30] + "..." if len(row['seller_name']) > 30 else row['seller_name'],
                        style={'padding': '8px', 'borderBottom': '1px solid #ddd', 'fontFamily': 'Inter', 'fontSize': '10px', 'textAlign': 'center'}),

                html.Td(format_currency_int(row['valor_neto']),
                        style={'padding': '8px', 'borderBottom': '1px solid #ddd', 'fontFamily': 'Inter', 'fontSize': '10px', 'textAlign': 'center'}),

                html.Td(format_currency_int(row['ventas_esperadas']),
                        style={'padding': '8px', 'borderBottom': '1px solid #ddd', 'fontFamily': 'Inter', 'fontSize': '10px', 'textAlign': 'center'}),

                html.Td(format_currency_int(row['target_value']),
                        style={'padding': '8px', 'borderBottom': '1px solid #ddd', 'fontFamily': 'Inter', 'fontSize': '10px', 'textAlign': 'center'}),

                # Progress bar for % Cumplimiento with status color
                html.Td(create_progress_bar(row['progreso_meta_pct'], estado_color),
                        style={'padding': '8px', 'borderBottom': '1px solid #ddd', 'textAlign': 'center'}),

                html.Td(estado_text,
                        style={'padding': '8px', 'borderBottom': '1px solid #ddd', 'color': estado_color,
                               'fontWeight': 'bold', 'fontFamily': 'Inter', 'fontSize': '10px', 'textAlign': 'center'})
            ])
            table_rows.append(table_row)

        # Create table
        table = html.Table([
            html.Thead([header]),
            html.Tbody(table_rows)
        ], style={
            'width': '100%',
            'borderCollapse': 'collapse',
            'backgroundColor': theme_styles['paper_color'],
            'color': theme_styles['text_color'],
            'margin': '0 auto'  # Center the table
        })

        # Calculate summary statistics with 4 categories
        total_convenios = len(data)
        cumpliendo_meta = data['cumplimiento_meta'].sum()
        adelantados = ((data['progreso_meta_pct'] > progreso_esperado) & (
            ~data['cumplimiento_meta'])).sum()
        cerca_esperado = ((data['progreso_meta_pct'] >= (progreso_esperado - 5)) &
                          (data['progreso_meta_pct'] <= progreso_esperado) &
                          (~data['cumplimiento_meta'])).sum()
        atrasados = total_convenios - cumpliendo_meta - adelantados - cerca_esperado
        promedio_cumplimiento = data['progreso_meta_pct'].mean()

        summary = html.Div([
            html.Div([
                html.H4("📊 Resumen Ejecutivo de Convenios",
                        style={'color': theme_styles['text_color'], 'fontFamily': 'Inter', 'margin': '0 0 15px 0', 'textAlign': 'center'}),

                html.Div([
                    html.Div([
                        html.H5(f"{total_convenios}", style={
                                'margin': '0', 'fontSize': '24px', 'color': '#3498db'}),
                        html.P("Total Convenios", style={
                               'margin': '0', 'fontSize': '12px'})
                    ], style={'textAlign': 'center', 'padding': '10px', 'margin': '5px'}),

                    html.Div([
                        html.H5(f"{cumpliendo_meta}", style={
                                'margin': '0', 'fontSize': '24px', 'color': '#27ae60'}),
                        html.P("Cumpliendo", style={
                               'margin': '0', 'fontSize': '12px'})
                    ], style={'textAlign': 'center', 'padding': '10px', 'margin': '5px'}),

                    html.Div([
                        html.H5(f"{adelantados}", style={'margin': '0',
                                'fontSize': '24px', 'color': '#f3c212'}),
                        html.P("Adelantados", style={
                               'margin': '0', 'fontSize': '12px'})
                    ], style={'textAlign': 'center', 'padding': '10px', 'margin': '5px'}),

                    html.Div([
                        html.H5(f"{cerca_esperado}", style={'margin': '0',
                                'fontSize': '24px', 'color': '#FF8C00'}),
                        html.P("Cerca Esperado", style={
                               'margin': '0', 'fontSize': '12px'})
                    ], style={'textAlign': 'center', 'padding': '10px', 'margin': '5px'}),

                    html.Div([
                        html.H5(f"{atrasados}", style={'margin': '0',
                                'fontSize': '24px', 'color': '#e74c3c'}),
                        html.P("Atrasados", style={
                               'margin': '0', 'fontSize': '12px'})
                    ], style={'textAlign': 'center', 'padding': '10px', 'margin': '5px'}),

                    html.Div([
                        html.H5(f"{progreso_esperado:.1f}%", style={
                                'margin': '0', 'fontSize': '24px', 'color': '#9b59b6'}),
                        html.P("% Esperado", style={
                               'margin': '0', 'fontSize': '12px'})
                    ], style={'textAlign': 'center', 'padding': '10px', 'margin': '5px'}),

                    html.Div([
                        html.H5(f"{promedio_cumplimiento:.1f}%", style={
                                'margin': '0', 'fontSize': '24px', 'color': '#16a085'}),
                        html.P("Promedio Real", style={
                               'margin': '0', 'fontSize': '12px'})
                    ], style={'textAlign': 'center', 'padding': '10px', 'margin': '5px'})

                ], style={'display': 'flex', 'justifyContent': 'space-around', 'flexWrap': 'wrap'})
            ], style={'backgroundColor': theme_styles['paper_color'], 'padding': '15px', 'borderRadius': '8px', 'border': f'1px solid {theme_styles["line_color"]}'})
        ], style={'marginBottom': '20px'})

        return html.Div([
            summary,
            html.Div(table, style={'maxHeight': '600px', 'overflowY': 'auto',
                     'border': f'1px solid {theme_styles["line_color"]}', 'borderRadius': '5px'})
        ])
    except Exception as e:
        print(f"Error en update_tabla_convenios: {e}")
        return html.Div([html.P("Error al cargar datos")])


@callback(
    Output('ventas-grafico-recaudo-vendedor', 'figure'),
    [Input('ventas-dropdown-mes', 'value'),
     Input('ventas-theme-store', 'data')]
)
def update_grafico_recaudo_vendedor(mes, theme):
    """
    Update vendor summary chart - filter by specific month if selected.
    """
    try:
        # CAMBIO: Pasar el parámetro mes para filtrar
        data, total_recaudo = \
            analyzer.get_recaudo_por_vendedor(mes)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos de recaudo por vendedor",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=14, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=350,
                plot_bgcolor=theme_styles['plot_bg'],
                paper_bgcolor=theme_styles['plot_bg']
            )
            return fig

        # Colores pasteles con transparencia
        pastel_colors_transparent = [
            'rgba(144, 238, 144, 0.7)',   # Light Green
            'rgba(173, 216, 230, 0.7)',   # Light Blue
            'rgba(255, 182, 193, 0.7)',   # Light Pink
            'rgba(255, 218, 185, 0.7)',   # Peach
            'rgba(221, 160, 221, 0.7)',   # Plum
            'rgba(175, 238, 238, 0.7)',   # Pale Turquoise
            'rgba(211, 211, 211, 0.7)'    # Light Gray
        ]

        bar_colors = [pastel_colors_transparent[i %
                                                len(pastel_colors_transparent)] for i in range(len(data))]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=data['vendedor'],
            y=data['valor_recibo'],
            marker=dict(
                color=bar_colors,
                line=dict(color='white', width=2),
                opacity=0.8
            ),
            text=[format_currency_int(val) for val in data['valor_recibo']],
            textposition='outside',
            textfont=dict(size=9, color=theme_styles['text_color']),
            hovertemplate="<b>%{x}</b><br>Recaudo: %{customdata[0]}<br>Recibos: %{customdata[1]}<extra></extra>",
            customdata=[[format_currency_int(val), recibos] for val, recibos in zip(
                data['valor_recibo'], data['recibo_id'])]
        ))

        # Título dinámico basado en filtro de mes
        titulo_mes = f" - {mes}" if mes != 'Todos' else ""

        fig.update_layout(
            title=f"Recaudo por Vendedor{titulo_mes}",
            title_x=0.5,
            height=500,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=11,
                      color=theme_styles['text_color']),
            xaxis=dict(
                showgrid=False,
                tickangle=-45,
                title="Vendedor",
                tickfont=dict(color=theme_styles['text_color']),
                linecolor=theme_styles['line_color']
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                tickformat='$,.0f',
                title="Recaudo ($)",
                tickfont=dict(color=theme_styles['text_color']),
                linecolor=theme_styles['line_color']
            ),
            showlegend=False,
            margin=dict(t=50, b=80, l=60, r=20)
        )

        return fig
    except Exception as e:
        print(f"Error en update_grafico_recaudo_vendedor: {e}")
        return go.Figure()


@callback(
    Output('ventas-grafico-recaudo-temporal', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-vista-recaudo', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-theme-store', 'data')]
)
def update_grafico_recaudo_temporal(session_data, dropdown_value, vista_recaudo, mes, theme):
    """
    Update temporal recaudo chart with ascending/descending colors for daily view.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        theme_styles = get_theme_styles(theme)

        # Get data based on view type
        if vista_recaudo == 'mensual':
            data, total_recaudo = \
                analyzer.get_recaudo_por_mes(vendedor)
            x_field = 'mes_nombre'
            x_title = "Mes"
            chart_type = 'line'
        else:
            data, total_recaudo = \
                analyzer.get_recaudo_por_dia(vendedor, mes)
            x_field = 'fecha_str'
            x_title = "Fecha"
            chart_type = 'bar'

        if data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos de recaudo disponibles",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=14, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=350,
                plot_bgcolor=theme_styles['plot_bg'],
                paper_bgcolor=theme_styles['plot_bg']
            )
            return fig

        # Create chart
        fig = go.Figure()

        if chart_type == 'line':
            # Line chart for monthly evolution with pastel color
            fig.add_trace(go.Scatter(
                x=data[x_field],
                y=data['valor_recibo'],
                mode='lines+markers',
                # Light green with transparency
                line=dict(color='rgba(144, 238, 144, 0.8)', width=3),
                marker=dict(size=8, color='rgba(144, 238, 144, 0.9)',
                            line=dict(color='white', width=2)),
                hovertemplate="<b>%{x}</b><br>Recaudo: %{customdata}<br>Recibos: %{text}<extra></extra>",
                customdata=[format_currency_int(val)
                            for val in data['valor_recibo']],
                text=data['recibo_id']
            ))
        else:
            # Bar chart for daily with ascending/descending colors
            # Calcular diferencias para determinar ascendente/descendente
            valores = data['valor_recibo'].tolist()
            bar_colors = []

            # Color para la primera barra (neutro)
            bar_colors.append('rgba(173, 216, 230, 0.8)')  # Light blue

            # Determinar colores basado en tendencia
            for i in range(1, len(valores)):
                if valores[i] > valores[i-1]:
                    # Ascendente - Verde pastel
                    bar_colors.append(
                        'rgba(144, 238, 144, 0.8)')  # Light green
                elif valores[i] < valores[i-1]:
                    # Descendente - Rosa pastel
                    bar_colors.append('rgba(255, 182, 193, 0.8)')  # Light pink
                else:
                    # Igual - Azul pastel
                    bar_colors.append('rgba(173, 216, 230, 0.8)')  # Light blue

            fig.add_trace(go.Bar(
                x=data[x_field],
                y=data['valor_recibo'],
                marker=dict(
                    color=bar_colors,
                    line=dict(color='white', width=2),
                    opacity=0.8
                ),
                text=[format_currency_int(
                    val) if val > 0 else '' for val in data['valor_recibo']],
                textposition='outside',
                textfont=dict(size=8, color=theme_styles['text_color']),
                hovertemplate="<b>%{x}</b><br>Recaudo: %{customdata[0]}<br>Recibos: %{customdata[1]}<extra></extra>",
                customdata=[[format_currency_int(val), recibos] for val, recibos in zip(
                    data['valor_recibo'], data['recibo_id'])]
            ))

        fig.update_layout(
            height=350,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=11,
                      color=theme_styles['text_color']),
            xaxis=dict(showgrid=True, gridcolor=theme_styles['grid_color'],
                       title=x_title, tickangle=-45 if chart_type == 'bar' else 0),
            yaxis=dict(
                showgrid=True, gridcolor=theme_styles['grid_color'], tickformat='$,.0f', title="Recaudo ($)"),
            showlegend=False,
            margin=dict(t=40, b=80, l=60, r=20)
        )

        return fig
    except Exception as e:
        print(f"Error en update_grafico_recaudo_temporal: {e}")
        return go.Figure()

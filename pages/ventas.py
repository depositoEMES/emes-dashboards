import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.express as px
import plotly.graph_objects as go
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


# Función auxiliar para obtener el vendedor seleccionado
def get_selected_vendor(session_data, dropdown_value):
    """Obtener vendedor basado en permisos y selección."""
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


# Add CSS for dropdown menu styling
index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Dark theme dropdown styling */
            .dash-dropdown.dark-theme .Select-control {
                background-color: #2d2d2d !important;
                color: #ffffff !important;
                border: 1px solid #505050 !important;
            }
            
            .dash-dropdown.dark-theme .Select-input > input {
                color: #ffffff !important;
            }
            
            .dash-dropdown.dark-theme .Select-placeholder {
                color: #bbbbbb !important;
            }
            
            .dash-dropdown.dark-theme .Select-menu-outer {
                background-color: #2d2d2d !important;
                border: 1px solid #505050 !important;
            }
            
            .dash-dropdown.dark-theme .Select-option {
                background-color: #2d2d2d !important;
                color: #ffffff !important;
            }
            
            .dash-dropdown.dark-theme .Select-option:hover {
                background-color: #404040 !important;
                color: #ffffff !important;
            }
            
            .dash-dropdown.dark-theme .Select-option.is-selected {
                background-color: #505050 !important;
                color: #ffffff !important;
            }
            
            .dash-dropdown.dark-theme .Select-option.is-focused {
                background-color: #404040 !important;
                color: #ffffff !important;
            }
            
            .dash-dropdown.dark-theme .Select-arrow {
                border-color: #ffffff transparent transparent !important;
            }
            
            .dash-dropdown.dark-theme .Select-value-label {
                color: #ffffff !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

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
                       'fontWeight': 'bold', 'marginBottom': '5px', 'fontFamily': 'Arial'}, id='ventas-dropdown-vendedor-label'),
            dcc.Dropdown(
                id='ventas-dropdown-vendedor',
                options=[{'label': v, 'value': v}
                         for v in analyzer.vendedores_list],
                value='Todos',
                style={'fontFamily': 'Arial'},
                className='custom-dropdown'
            )
        ], style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '2%'}, id='ventas-dropdown-vendedor-container'),

        html.Div([
            html.Label("Mes:", style={
                       'fontWeight': 'bold', 'marginBottom': '5px', 'fontFamily': 'Arial'}),
            dcc.Dropdown(
                id='ventas-dropdown-mes',
                options=[{'label': m, 'value': m}
                         for m in analyzer.meses_list],
                value='Todos',
                style={'fontFamily': 'Arial'},
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
                html.H3("Ventas Netas", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Arial'}),
                html.H2(id='ventas-ventas-netas', children="$0", style={'color': '#2ecc71',
                        'fontSize': '20px', 'margin': '0', 'fontFamily': 'Arial'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='ventas-card-1'),

            html.Div([
                html.H3("Devoluciones", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Arial'}),
                html.H2(id='ventas-total-devoluciones', children="$0", style={
                        'color': '#e74c3c', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Arial'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='ventas-card-2'),

            html.Div([
                html.H3("# Devoluciones", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Arial'}),
                html.H2(id='ventas-num-devoluciones', children="0", style={
                        'color': '#c0392b', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Arial'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='ventas-card-3'),

            html.Div([
                html.H3("Valor Promedio", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Arial'}),
                html.H2(id='ventas-valor-promedio', children="$0", style={
                        'color': '#9b59b6', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Arial'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='ventas-card-4')
        ], style={'marginBottom': '15px'}),

        # Segunda fila de cards
        html.Div([
            html.Div([
                html.H3("Facturas", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Arial'}),
                html.H2(id='ventas-num-facturas', children="0", style={'color': '#3498db',
                        'fontSize': '20px', 'margin': '0', 'fontFamily': 'Arial'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='ventas-card-5'),

            html.Div([
                html.H3("Clientes", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Arial'}),
                html.H2(id='ventas-num-clientes', children="0", style={'color': '#e67e22',
                        'fontSize': '20px', 'margin': '0', 'fontFamily': 'Arial'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='ventas-card-6'),

            html.Div([
                html.H3("Descuentos", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Arial'}),
                html.H2(id='ventas-total-descuentos', children="$0", style={
                        'color': '#f39c12', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Arial'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='ventas-card-7'),

            html.Div([
                html.H3("% Descuento", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Arial'}),
                html.H2(id='ventas-porcentaje-descuento', children="0%", style={
                        'color': '#16a085', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Arial'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='ventas-card-8')
        ])
    ], style={'marginBottom': '30px'}),

    # Fila 1: Evolución Mensual y Análisis de Estacionalidad
    html.Div([
        html.Div([
            html.H3("Evolución de Ventas por Mes", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Arial'}),
            dcc.Graph(id='ventas-grafico-ventas-mes')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'}),

        html.Div([
            html.H3("Estacionalidad por Día de la Semana", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Arial'}),
            dcc.Graph(id='ventas-grafico-estacionalidad')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'})
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'}, id='ventas-row1-container'),

    # Fila 1.5: Evolución de Ventas por Cliente Específico
    html.Div([
        html.H3("Evolución Diaria de Ventas por Cliente", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Arial'}),
        html.Div([
            html.Label("Seleccionar Cliente:", style={
                       'fontWeight': 'bold', 'marginBottom': '10px', 'fontFamily': 'Arial'}),
            dcc.Dropdown(
                id='ventas-dropdown-cliente',
                options=[{'label': 'Seleccione un cliente',
                          'value': 'Seleccione un cliente'}],
                value='Seleccione un cliente',
                style={'fontFamily': 'Arial', 'marginBottom': '20px'},
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
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Arial'}),
            dcc.Graph(id='ventas-grafico-zona')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'}),

        html.Div([
            html.H3("Distribución por Forma de Pago", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Arial'}),
            dcc.Graph(id='ventas-grafico-forma-pago')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'})
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'}, id='ventas-row2-container'),

    # Fila 2.5: Ventas Acumuladas por Cliente (Treemap solo)
    html.Div([
        html.H3("Ventas Acumuladas por Cliente", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Arial'}),
        html.P("(Acumulado hasta el mes seleccionado)", style={
               'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '12px', 'margin': '0 0 20px 0'}),
        dcc.Graph(id='ventas-treemap-acumuladas')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'}, id='ventas-row2-5-container'),

    # Fila 3: Treemap de Ventas por Cliente del Período (Treemap solo)
    html.Div([
        html.H3("Mapa de Ventas por Cliente (Período Seleccionado)", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Arial'}),
        dcc.Graph(id='ventas-treemap-ventas')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'}, id='ventas-row3-container'),

    # Fila 3.5: Top Clientes y Clientes Impactados
    html.Div([
        html.H3("Clientes por Días Sin Venta", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Arial'}),
        html.P("(Clientes que no han comprado en 7+ días - Tamaño por total de ventas históricas)", style={
               'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '12px', 'margin': '0 0 20px 0'}),
        dcc.Graph(id='ventas-treemap-dias-sin-venta')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'}, id='ventas-row-nueva-treemap'),

    # Fila 4: Top Clientes y Clientes Impactados
    html.Div([
        html.Div([
            html.H3("Top 10 - Clientes", style={'textAlign': 'center',
                    'marginBottom': '20px', 'fontFamily': 'Arial'}),
            dcc.Graph(id='ventas-top-clientes')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'}),

        html.Div([
            html.H3("Clientes Impactados por Mes", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Arial'}),
            html.P("(Número de clientes únicos que compraron vs total disponible)", style={
                   'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '12px', 'margin': '0 0 20px 0'}),
            dcc.Graph(id='ventas-grafico-clientes-impactados')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'})
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'}, id='ventas-row4-container'),

    # Fila 5: Análisis de Convenios
    html.Div([
        html.H3("Análisis de Cumplimiento de Convenios", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Arial'}),
        html.P("(Comparación entre metas vs. ventas reales y descuentos acordados vs. descuentos aplicados)", style={
               'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '12px', 'margin': '0 0 20px 0'}),
        html.Div(id='ventas-tabla-convenios')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'}, id='ventas-row5-container'),

    # Fila 6: Análisis de Recaudo
    html.Div([
        html.Div([
            html.H3("Análisis de Recaudo", style={
                    'textAlign': 'center', 'marginBottom': '10px', 'fontFamily': 'Arial'}),
            html.H2(id='ventas-total-recaudo-titulo', style={'textAlign': 'center',
                    'color': '#27ae60', 'marginBottom': '20px', 'fontFamily': 'Arial'}),

            # DROPDOWN VISTA RECAUDO - Now always present in layout
            html.Div([
                html.Label("Vista Temporal:", style={
                           'fontWeight': 'bold', 'marginRight': '10px', 'fontFamily': 'Arial'}),
                dcc.Dropdown(
                    id='ventas-dropdown-vista-recaudo',
                    options=[
                        {'label': 'Recaudo Diario', 'value': 'diario'},
                        {'label': 'Recaudo Mensual', 'value': 'mensual'}
                    ],
                    value='diario',
                    style={'width': '200px', 'fontFamily': 'Arial',
                           'display': 'inline-block'},
                    clearable=False
                )
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'marginBottom': '20px'}, id='ventas-vista-recaudo-container'),

            # GRAFICOS DE RECAUDO - Now always present in layout
            html.Div([
                # Gráfico por vendedor (solo se muestra cuando vendedor = 'Todos')
                html.Div([
                    html.H4("Resumen por Vendedor", style={
                            'textAlign': 'center', 'marginBottom': '15px', 'fontFamily': 'Arial'}),
                    dcc.Graph(id='ventas-grafico-recaudo-vendedor')
                ], style={'width': '100%', 'marginBottom': '20px'}, id='ventas-container-vendedor'),

                # Gráfico temporal (siempre se muestra)
                html.Div([
                    html.H4(id='ventas-titulo-recaudo-temporal', style={
                            'textAlign': 'center', 'marginBottom': '15px', 'fontFamily': 'Arial'}),
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
                           'fontFamily': 'Arial'})
    ], style={'textAlign': 'center', 'margin': '20px 0'})

], style={'fontFamily': 'Arial', 'backgroundColor': '#f5f5f5', 'padding': '20px'}, id='ventas-main-container')


# Callback para controlar visibilidad del dropdown de vendedores
@callback(
    [Output('ventas-dropdown-vendedor-container', 'style'),
     Output('ventas-dropdown-vendedor-label', 'style')],
    [Input('session-store', 'data')]
)
def update_dropdown_visibility(session_data):
    """Mostrar/ocultar dropdown de vendedores según permisos del usuario."""
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
                'fontFamily': 'Arial'
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
        'fontFamily': 'Arial',
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
     Output('ventas-dropdown-vendedor', 'className'),
     Output('ventas-dropdown-mes', 'className'),
     Output('ventas-dropdown-cliente', 'className'),
     Output('ventas-dropdown-vista-recaudo', 'className')],
    [Input('ventas-theme-store', 'data'),
     Input('session-store', 'data')]
)
def update_dropdown_styles(theme, session_data):
    """Update dropdown styles based on theme and visibility."""
    from utils import can_see_all_vendors

    dropdown_style = get_dropdown_style(theme)
    dropdown_style['fontFamily'] = 'Arial'

    # Special handling for vendor dropdown - hide if not admin
    if not session_data or not can_see_all_vendors(session_data):
        vendedor_style = {'display': 'none'}
    else:
        vendedor_style = dropdown_style.copy()

    vista_style = dropdown_style.copy()
    vista_style.update({'width': '200px', 'display': 'inline-block'})

    # CSS class for dark theme
    css_class = 'dash-dropdown dark-theme' if theme == 'dark' else 'dash-dropdown'

    return vendedor_style, dropdown_style, dropdown_style, vista_style, css_class, css_class, css_class, css_class


@callback(
    [Output('ventas-card-1', 'style'), Output('ventas-card-2', 'style'), Output('ventas-card-3', 'style'), Output('ventas-card-4', 'style'),
     Output('ventas-card-5', 'style'), Output('ventas-card-6', 'style'), Output('ventas-card-7', 'style'), Output('ventas-card-8', 'style')],
    [Input('ventas-theme-store', 'data')]
)
def update_card_styles(theme):
    """Update styles for summary cards based on theme."""
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
    [Output('ventas-row1-container', 'style'), Output('ventas-row1-5-container', 'style'), Output('ventas-row-nueva-treemap', 'style'), Output('ventas-row2-container', 'style'),
     Output('ventas-row2-5-container', 'style'), Output('ventas-row3-container',
                                                        'style'), Output('ventas-row4-container', 'style'),
     Output('ventas-row5-container', 'style'), Output('ventas-row6-container', 'style')],
    [Input('ventas-theme-store', 'data')]
)
def update_container_styles(theme):
    """Update styles for chart containers based on theme."""
    theme_styles = get_theme_styles(theme)

    chart_style = {
        'backgroundColor': theme_styles['paper_color'],
        'padding': '20px',
        'borderRadius': '8px',
        'boxShadow': theme_styles['card_shadow'],
        'margin': '10px 0',
        'color': theme_styles['text_color']
    }

    return [chart_style] * 9  # 9 containers now


@callback(
    [Output('ventas-container-vendedor', 'style'),
     Output('ventas-vista-recaudo-container', 'style'),
     Output('ventas-titulo-recaudo-temporal', 'children')],
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-vista-recaudo', 'value')]
)
def update_recaudo_visibility(session_data, dropdown_value, vista_recaudo):
    """Show/hide recaudo components based on vendor selection."""
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
    """Update dashboard title based on filters."""
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
    [Output('ventas-ventas-netas', 'children'), Output('ventas-total-devoluciones', 'children'),
     Output('ventas-num-devoluciones',
            'children'), Output('ventas-valor-promedio', 'children'),
     Output('ventas-num-facturas',
            'children'), Output('ventas-num-clientes', 'children'),
     Output('ventas-total-descuentos', 'children'), Output('ventas-porcentaje-descuento', 'children')],
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-btn-actualizar', 'n_clicks')]
)
def update_cards(session_data, dropdown_value, mes, n_clicks):
    """Update summary cards with sales statistics."""
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        resumen = analyzer.get_resumen_ventas(vendedor, mes)

        return (
            format_currency_int(resumen['ventas_netas']),
            format_currency_int(resumen['total_devoluciones']),
            f"{resumen['num_devoluciones']:,}",
            format_currency_int(resumen['ticket_promedio']),
            f"{resumen['num_facturas']:,}",
            f"{resumen['num_clientes']:,}",
            format_currency_int(resumen['total_descuentos']),
            f"{resumen['porcentaje_descuento']:.1f}%"
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
    """Update monthly sales evolution chart."""
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_ventas_por_mes(vendedor)
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

        fig = go.Figure()

        # Add sales line
        fig.add_trace(go.Scatter(
            x=data['mes_nombre'],
            y=data['valor_neto'],
            mode='lines+markers',
            name='Ventas',
            line=dict(color='#27ae60', width=3),
            marker=dict(size=8, color='#27ae60'),
            hovertemplate="<b>%{x}</b><br>Ventas: %{customdata}<br>Facturas: %{text}<extra></extra>",
            customdata=[format_currency_int(val)
                        for val in data['valor_neto']],
            text=data['documento_id']
        ))

        fig.update_layout(
            height=400,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Arial", size=12,
                      color=theme_styles['text_color']),
            xaxis=dict(
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                tickangle=-45,
                title="Mes"
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                tickformat='$,.0f',
                title="Ventas ($)"
            ),
            showlegend=False,
            margin=dict(t=20, b=80, l=80, r=20)
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
    """Update seasonality chart by day of week."""
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

        # Create bar chart with different colors for each day
        colors = ['#3498db', '#e74c3c', '#2ecc71',
                  '#f39c12', '#9b59b6', '#1abc9c', '#34495e']

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=data['dia_semana_es'],
            y=data['valor_neto'],
            marker=dict(
                color=[colors[i % len(colors)] for i in range(len(data))],
                line=dict(color='white', width=1)
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
            font=dict(family="Arial", size=12,
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
    """Update days without sales treemap."""
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
            text=[cliente[:40] + "..." if len(cliente) > 40 else cliente
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
            font=dict(family="Arial", size=12,
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
    """Update sales by zone chart."""
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_ventas_por_zona(vendedor, mes)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            fig = go.Figure()
            fig.add_annotation(text="No hay datos disponibles", xref="paper", yref="paper",
                               x=0.5, y=0.5, showarrow=False, font=dict(size=16, color=theme_styles['text_color']))
            fig.update_layout(
                height=350, paper_bgcolor=theme_styles['plot_bg'])
            return fig

        fig = px.bar(data, x='zona', y='valor_neto',
                     color='valor_neto', color_continuous_scale='Blues')

        fig.update_traces(
            text=[format_currency_int(val) for val in data['valor_neto']],
            textposition='outside',
            hovertemplate="<b>%{x}</b><br>Ventas: %{customdata[0]}<br>Clientes: %{customdata[1]}<extra></extra>",
            customdata=[[format_currency_int(val), clientes] for val, clientes in zip(
                data['valor_neto'], data['cliente'])]
        )

        fig.update_layout(
            height=350,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Arial", size=12,
                      color=theme_styles['text_color']),
            xaxis=dict(tickangle=-45, showgrid=False),
            yaxis=dict(showgrid=True,
                       gridcolor=theme_styles['grid_color'], tickformat='$,.0f'),
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
    """Update payment method chart."""
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_forma_pago_distribution(vendedor, mes)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            fig = go.Figure()
            fig.add_annotation(text="No hay datos disponibles", xref="paper", yref="paper",
                               x=0.5, y=0.5, showarrow=False, font=dict(size=16, color=theme_styles['text_color']))
            fig.update_layout(
                height=350, paper_bgcolor=theme_styles['plot_bg'])
            return fig

        fig = go.Figure(data=[go.Pie(
            labels=data['forma_pago'],
            values=data['valor_neto'],
            hole=.4,
            textinfo='percent',
            marker=dict(colors=['#3498DB', '#E74C3C', '#2ECC71', '#F39C12',
                        '#9B59B6'], line=dict(color='#FFFFFF', width=2)),
            hovertemplate="<b>%{label}</b><br>Ventas: %{customdata}<br>Porcentaje: %{percent}<extra></extra>",
            customdata=[format_currency_int(val) for val in data['valor_neto']]
        )])

        fig.update_layout(
            height=350,
            font=dict(family="Arial", size=12,
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
    """Update sales treemap."""
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
            font=dict(family="Arial", size=12,
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
    """Update top customers chart."""
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
            font=dict(family="Arial", size=12,
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
    """Update client dropdown based on selected salesperson."""
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
    """Reset client selection when salesperson changes."""
    return 'Seleccione un cliente'


@callback(
    Output('ventas-grafico-evolucion-cliente', 'figure'),
    [Input('ventas-dropdown-cliente', 'value'),
     Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-theme-store', 'data')]
)
def update_evolucion_cliente(cliente, session_data, dropdown_value, theme):
    """Update client evolution chart - now showing daily sales."""
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_evolucion_cliente(cliente, vendedor)
        theme_styles = get_theme_styles(theme)

        if data.empty or cliente == 'Seleccione un cliente':
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
                font=dict(family="Arial", size=12,
                          color=theme_styles['text_color'])
            )
            return fig

        # Create bar chart with daily data
        fig = go.Figure()

        # Add bars with gradient colors
        colors = ['#27ae60', '#2ecc71', '#58d68d',
                  '#82e0aa', '#abebc6', '#d5f4e6']
        bar_colors = [colors[i % len(colors)] for i in range(len(data))]

        fig.add_trace(go.Bar(
            x=data['fecha_str'],
            y=data['valor_neto'],
            marker=dict(
                color=bar_colors,
                line=dict(color='white', width=1)
            ),
            text=[format_currency_int(val) if val >
                  50000 else '' for val in data['valor_neto']],
            textposition='outside',
            textfont=dict(size=9, color=theme_styles['text_color']),
            hovertemplate="<b>%{x}</b><br>" +
                         "Ventas: %{customdata[0]}<br>" +
                         "Facturas: %{customdata[1]}<br>" +
                         "<extra></extra>",
            customdata=[[format_currency_int(val), facturas] for val, facturas in zip(
                data['valor_neto'], data['documento_id'])]
        ))

        fig.update_layout(
            title=f"Evolución Diaria - {cliente[:50]}{'...' if len(cliente) > 50 else ''}",
            title_x=0.5,
            xaxis_title="Fecha",
            yaxis_title="Ventas ($)",
            height=400,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Arial", size=12,
                      color=theme_styles['text_color']),
            xaxis=dict(
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                linecolor=theme_styles['line_color'],
                tickangle=-45,
                type='category'  # Treat dates as categories for better spacing
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                linecolor=theme_styles['line_color'],
                tickformat='$,.0f'
            ),
            showlegend=False,
            margin=dict(t=60, b=80, l=80, r=40)
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
    """Update accumulated sales treemap."""
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
            font=dict(family="Arial", size=12,
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
    """Update collection title with total amount."""
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
    """Update clients impacted chart with horizontal bars and total clients bar."""
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
            textfont=dict(color='white', size=10, family='Arial'),
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
            font=dict(family="Arial", size=12,
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
    """Update convenios analysis table with enhanced design and expected sales."""
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_analisis_convenios(vendedor, mes)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            return html.Div([
                html.P("No hay datos de convenios disponibles o no se encontraron coincidencias por NIT.",
                       style={'textAlign': 'center', 'color': 'gray', 'fontSize': '16px', 'fontFamily': 'Arial'})
            ])

        # Get expected percentage (same for all rows)
        progreso_esperado = data['progreso_esperado_pct'].iloc[0] if len(
            data) > 0 else 0

        def create_progress_bar(percentage, status_color='#27ae60', width="100px", height="20px"):
            """Create a progress bar with status-based color."""
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
                    'color': 'white', 'fontFamily': 'Arial', 'fontSize': '12px', 'textAlign': 'left'}),
            html.Th("Vendedor", style={'padding': '12px', 'backgroundColor': '#34495e',
                    'color': 'white', 'fontFamily': 'Arial', 'fontSize': '12px', 'textAlign': 'center'}),
            html.Th("Ventas", style={'padding': '12px', 'backgroundColor': '#34495e',
                    'color': 'white', 'fontFamily': 'Arial', 'fontSize': '12px', 'textAlign': 'center'}),
            html.Th("Ventas Esperadas", style={'padding': '12px', 'backgroundColor': '#34495e',
                    'color': 'white', 'fontFamily': 'Arial', 'fontSize': '12px', 'textAlign': 'center'}),
            html.Th("Meta", style={'padding': '12px', 'backgroundColor': '#34495e',
                    'color': 'white', 'fontFamily': 'Arial', 'fontSize': '12px', 'textAlign': 'center'}),
            html.Th("% Cumplimiento", style={'padding': '12px', 'backgroundColor': '#34495e',
                    'color': 'white', 'fontFamily': 'Arial', 'fontSize': '12px', 'textAlign': 'center'}),
            html.Th("Estado", style={'padding': '12px', 'backgroundColor': '#34495e',
                    'color': 'white', 'fontFamily': 'Arial', 'fontSize': '12px', 'textAlign': 'center'})
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
                ], style={'padding': '8px', 'borderBottom': '1px solid #ddd', 'fontFamily': 'Arial', 'textAlign': 'left'}),

                # All other columns centered
                html.Td(row['seller_name'][:30] + "..." if len(row['seller_name']) > 30 else row['seller_name'],
                        style={'padding': '8px', 'borderBottom': '1px solid #ddd', 'fontFamily': 'Arial', 'fontSize': '10px', 'textAlign': 'center'}),

                html.Td(format_currency_int(row['valor_neto']),
                        style={'padding': '8px', 'borderBottom': '1px solid #ddd', 'fontFamily': 'Arial', 'fontSize': '10px', 'textAlign': 'center'}),

                html.Td(format_currency_int(row['ventas_esperadas']),
                        style={'padding': '8px', 'borderBottom': '1px solid #ddd', 'fontFamily': 'Arial', 'fontSize': '10px', 'textAlign': 'center'}),

                html.Td(format_currency_int(row['target_value']),
                        style={'padding': '8px', 'borderBottom': '1px solid #ddd', 'fontFamily': 'Arial', 'fontSize': '10px', 'textAlign': 'center'}),

                # Progress bar for % Cumplimiento with status color
                html.Td(create_progress_bar(row['progreso_meta_pct'], estado_color),
                        style={'padding': '8px', 'borderBottom': '1px solid #ddd', 'textAlign': 'center'}),

                html.Td(estado_text,
                        style={'padding': '8px', 'borderBottom': '1px solid #ddd', 'color': estado_color,
                               'fontWeight': 'bold', 'fontFamily': 'Arial', 'fontSize': '10px', 'textAlign': 'center'})
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
                        style={'color': theme_styles['text_color'], 'fontFamily': 'Arial', 'margin': '0 0 15px 0', 'textAlign': 'center'}),

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
    """Update vendor summary chart (only when 'Todos' is selected)."""
    try:
        data, total_recaudo = analyzer.get_recaudo_por_vendedor()
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
                height=350, plot_bgcolor=theme_styles['plot_bg'], paper_bgcolor=theme_styles['plot_bg'])
            return fig

        # Create bar chart with different colors for each vendor
        colors = ['#27ae60', '#3498db', '#e74c3c',
                  '#f39c12', '#9b59b6', '#1abc9c', '#34495e']
        bar_colors = [colors[i % len(colors)] for i in range(len(data))]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=data['vendedor'],
            y=data['valor_recibo'],
            marker=dict(color=bar_colors, line=dict(color='white', width=1)),
            text=[format_currency_int(val) for val in data['valor_recibo']],
            textposition='outside',
            textfont=dict(size=9, color=theme_styles['text_color']),
            hovertemplate="<b>%{x}</b><br>Recaudo: %{customdata[0]}<br>Recibos: %{customdata[1]}<extra></extra>",
            customdata=[[format_currency_int(val), recibos] for val, recibos in zip(
                data['valor_recibo'], data['recibo_id'])]
        ))

        fig.update_layout(
            height=450,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Arial", size=11,
                      color=theme_styles['text_color']),
            xaxis=dict(showgrid=False, tickangle=-45, title="Vendedor"),
            yaxis=dict(
                showgrid=True, gridcolor=theme_styles['grid_color'], tickformat='$,.0f', title="Recaudo ($)"),
            showlegend=False,
            margin=dict(t=20, b=80, l=60, r=20)
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
    """Update temporal recaudo chart."""
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        theme_styles = get_theme_styles(theme)

        # Get data based on view type
        if vista_recaudo == 'mensual':
            data, total_recaudo = analyzer.get_recaudo_por_mes(vendedor)
            x_field = 'mes_nombre'
            x_title = "Mes"
            chart_type = 'line'
        else:
            data, total_recaudo = analyzer.get_recaudo_por_dia(vendedor, mes)
            x_field = 'fecha_str'
            x_title = "Fecha"
            chart_type = 'bar'

        if data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos de recaudo disponibles",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=14, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=350, plot_bgcolor=theme_styles['plot_bg'], paper_bgcolor=theme_styles['plot_bg'])
            return fig

        # Create chart
        fig = go.Figure()

        if chart_type == 'line':
            # Line chart for monthly evolution
            fig.add_trace(go.Scatter(
                x=data[x_field],
                y=data['valor_recibo'],
                mode='lines+markers',
                line=dict(color='#27ae60', width=3),
                marker=dict(size=6, color='#27ae60'),
                hovertemplate="<b>%{x}</b><br>Recaudo: %{customdata}<br>Recibos: %{text}<extra></extra>",
                customdata=[format_currency_int(val)
                            for val in data['valor_recibo']],
                text=data['recibo_id']
            ))
        else:
            # Bar chart for daily
            fig.add_trace(go.Bar(
                x=data[x_field],
                y=data['valor_recibo'],
                marker=dict(color='#27ae60', line=dict(
                    color='white', width=1)),
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
            font=dict(family="Arial", size=11,
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

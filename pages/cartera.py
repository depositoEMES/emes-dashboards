import time
import pandas as pd
from datetime import datetime

import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.express as px
import plotly.graph_objects as go

from analyzers import CarteraAnalyzer
from utils import format_currency_int, get_theme_styles


# Initialize analyzer
analyzer = CarteraAnalyzer()

try:
    print("🚀 [CarteraPage] Inicializando CarteraAnalyzer...")
    df = analyzer.load_data_from_firebase()
    print(f"✅ [CarteraPage] Carga inicial completada: {len(df)} registros")
except Exception as e:
    print(
        f"⚠️ [CarteraPage] Carga inicial falló (se recargará on-demand): {e}")
    df = pd.DataFrame()

# Definir paletas de colores pasteles
PALETA_PASTELES_BARRAS = [
    '#3498DB', '#E74C3C', '#2ECC71', '#F39C12',
    '#9B59B6'
]

PALETA_PASTELES_DONA = [
    '#3498DB', '#E74C3C', '#2ECC71', '#F39C12',
    '#9B59B6'
]

layout = html.Div([
    # Store for theme
    dcc.Store(id='cartera-theme-store', data='light'),
    dcc.Store(id='cartera-data-store', data={'last_update': 0}),

    html.Div(id='cartera-notification-area', children=[], style={
        'position': 'fixed',
        'top': '20px',
        'right': '20px',
        'zIndex': '1000',
        'maxWidth': '300px'
    }),

    # Header
    html.Div([
        # Fila del título - separada y llamativa
        html.Div([
            html.H1(
                id='cartera-titulo-dashboard',
                children="Dashboard de Cartera",
                style={
                    'textAlign': 'center',
                    'fontSize': '2.5rem',
                    'fontWeight': '700',
                    'fontFamily': 'Inter',
                    'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    'webkitBackgroundClip': 'text',
                    'webkitTextFillColor': 'transparent',
                    'backgroundClip': 'text',
                    'margin': '0 0 20px 0',
                    'letterSpacing': '-0.02em',
                    'textShadow': '0 2px 4px rgba(0,0,0,0.1)'
                }
            )
        ], style={'width': '100%', 'marginBottom': '25px'}),

        # Fila de controles - con mejor alineación
        html.Div([
            # Dropdown para vendedores
            html.Div([
                html.Label("Vendedor:", style={
                    'fontWeight': 'bold',
                    'marginBottom': '8px',
                    'fontFamily': 'Inter',
                    'fontSize': '14px'
                }, id='cartera-dropdown-vendedor-label'),
                dcc.Dropdown(
                    id='cartera-dropdown-vendedor',
                    options=[{'label': v, 'value': v}
                             for v in analyzer.vendedores_list],
                    value='Todos',
                    style={'fontFamily': 'Inter'},
                    className='custom-dropdown'
                )
            ], style={
                'flex': '0 0 40%'
            }, id='cartera-dropdown-vendedor-container'),

            # Espacio flexible para empujar el botón a la derecha
            html.Div(style={'flex': '1'}),

            # Botón de tema alineado correctamente
            html.Div([
                html.Button(
                    html.Div([
                        html.Span('🌙', id='cartera-theme-icon',
                                  style={'fontSize': '18px'}),
                        html.Span('Oscuro', id='cartera-theme-text', style={
                            'marginLeft': '8px',
                            'fontSize': '13px',
                            'fontWeight': '500'
                        })
                    ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}),
                    id='cartera-theme-toggle',
                    n_clicks=0,
                    style={
                        'backgroundColor': '#f8f9fa',
                        'border': '2px solid #e9ecef',
                        'borderRadius': '12px',
                        'padding': '10px 16px',
                        'cursor': 'pointer',
                        'fontFamily': 'Inter',
                        'fontSize': '13px',
                        'fontWeight': '500',
                        'transition': 'all 0.3s ease',
                        'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                        'height': '40px',
                        'display': 'flex',
                        'alignItems': 'center',
                        'justifyContent': 'center',
                        'outline': 'none'
                    }
                )
            ], style={
                'flex': '0 0 140px',
                'display': 'flex',
                'alignItems': 'flex-end',
                'height': '100%',
                'paddingBottom': '0px'
            })
        ], style={
            'width': '100%',
            'display': 'flex',
            'alignItems': 'flex-end',
            'minHeight': '68px'
        })
    ], style={'marginBottom': '35px', 'padding': '25px'}, id='cartera-header-container'),

    # Cards de resumen - 8 cards en 2 filas de 4 columnas
    html.Div([
        # Primera fila de cards
        html.Div([
            html.Div([
                html.H3("Cartera Total", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}, id='cartera-card-1-title'),
                html.H2(
                    id='cartera-total-cartera', children="$0", style={'color': '#e74c3c', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='cartera-card-1'),

            html.Div([
                html.H3("Vencida", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}, id='cartera-card-2-title'),
                html.H2(
                    id='cartera-total-vencida', children="$0", style={'color': '#e74c3c', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='cartera-card-2'),

            html.Div([
                html.H3("Sin Vencer", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}, id='cartera-card-3-title'),
                html.H2(id='cartera-total-sin-vencer', children="$0",
                        style={'color': '#27ae60', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='cartera-card-3'),

            html.Div([
                html.H3("Calidad Cartera", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}, id='cartera-card-4-title'),
                html.H2(id='cartera-calidad-cartera', children="0%",
                        style={'color': '#9b59b6', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='cartera-card-4')
        ], style={'marginBottom': '15px'}),

        # Segunda fila de cards
        html.Div([
            html.Div([
                html.H3("Clientes", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}, id='cartera-card-5-title'),
                html.H2(id='cartera-total-clientes', children="0",
                        style={'color': '#3498db', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='cartera-card-5'),

            html.Div([
                html.H3("Clientes con cartera vencida", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}, id='cartera-card-6-title'),
                html.H2(id='cartera-clientes-vencida', children="0",
                        style={'color': '#e67e22', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='cartera-card-6'),

            html.Div([
                html.H3("Facturas", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}, id='cartera-card-7-title'),
                html.H2(
                    id='cartera-num-facturas', children="0", style={'color': '#16a085', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='cartera-card-7'),

            html.Div([
                html.H3("% Vencida", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}, id='cartera-card-8-title'),
                html.H2(id='cartera-porcentaje-vencida', children="0%",
                        style={'color': '#f39c12', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='cartera-card-8')
        ])
    ], style={'marginBottom': '30px'}),

    # Fila 1: Distribución por Días Vencidos y Forma de Pago
    html.Div([
        html.Div([
            html.H3("Distribución por Días Vencidos", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
            dcc.Graph(id='cartera-grafico-rangos')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'}),

        html.Div([
            html.H3("Distribución por Forma de Pago", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
            dcc.Graph(id='cartera-grafico-forma-pago')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'})
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'},
        id='cartera-row1-container'),

    # Fila 2: Treemap Cartera Total
    html.Div([
        html.H3("Mapa de Cartera Total por Cliente", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
        dcc.Graph(id='cartera-treemap-cartera')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'},
        id='cartera-row2-container'),

    # Fila 2.5: Treemap Cartera Vencida
    html.Div([
        html.H3("Mapa de Cartera Vencida por Cliente", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
        dcc.Graph(id='cartera-treemap-cartera-vencida')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'},
        id='cartera-row2-5-container'),

    # Nueva sección: Detalle por Cliente
    html.Div([
        html.H3("Detalle de Cartera por Cliente", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),

        # Dropdown para seleccionar cliente
        html.Div([
            html.Label("Seleccionar Cliente:", style={
                'fontWeight': 'bold',
                'marginBottom': '8px',
                'fontFamily': 'Inter',
                'fontSize': '14px'
            }),
            dcc.Dropdown(
                id='cartera-dropdown-cliente',
                placeholder="Seleccione un cliente...",
                style={'fontFamily': 'Inter'},
                className='custom-dropdown'
            )
        ], style={'marginBottom': '20px'}),

        # Contenedor para la tabla del cliente
        html.Div(id='cartera-tabla-cliente-detalle')

    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'},
        id='cartera-cliente-detalle-container'),

    # Fila 3: Top 10
    html.Div([
        html.Div([
            html.H3("Top 10 - Cartera Vencida",
                    style={'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
            dcc.Graph(id='cartera-top-vencida')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'}),

        html.Div([
            html.H3("Top 10 - Cartera Sin Vencer",
                    style={'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
            dcc.Graph(id='cartera-top-sin-vencer')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'})
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'},
        id='cartera-row3-container'),

    # Fila 4: Análisis de Vencimientos - Configuración
    html.Div([
        html.H3("Análisis de Vencimientos Próximos", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
        html.Div([
            html.Label("Días para análisis:", style={
                       'marginBottom': '10px', 'fontWeight': 'bold', 'fontFamily': 'Inter'}),
            dcc.Slider(
                id='cartera-slider-dias',
                min=1, max=90, step=1, value=5,
                marks={i: str(i) for i in range(0, 91, 15)},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], style={'marginBottom': '20px'})
    ], style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '8px',
              'margin': '10px 0'}, id='cartera-config-container'),

    # Fila 5: Gráfico de Vencimientos Próximos
    html.Div([
        html.H3("Documentos Próximos a Vencer", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
        dcc.Graph(id='cartera-grafico-proximos-vencer')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'},
        id='cartera-row5-container'),

    # Fila 6: Tabla Detallada de Vencimientos
    html.Div([
        html.H3("Detalle de Documentos por Vencer", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
        html.Div(id='cartera-tabla-proximos-vencer')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'},
        id='cartera-row6-container'),

    # Botón actualizar
    html.Div([
        html.Button([
            html.Span("🔄", style={'marginRight': '8px'}),
            'Actualizar Datos'
        ], id='cartera-btn-actualizar', n_clicks=0,
            style={
            'backgroundColor': '#3498db',
            'color': 'white',
            'border': 'none',
            'padding': '12px 24px',
            'borderRadius': '6px',
            'cursor': 'pointer',
            'fontFamily': 'Inter',
            'fontSize': '14px',
            'fontWeight': 'bold',
            'transition': 'all 0.3s ease',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
        })
    ], style={'textAlign': 'center', 'margin': '20px 0'})

], style={'fontFamily': 'Inter', 'backgroundColor': '#f5f5f5', 'padding': '20px'}, id='cartera-main-container')


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


@callback(
    Output('cartera-data-store', 'data'),
    [Input('cartera-btn-actualizar', 'n_clicks')],
    prevent_initial_call=True
)
def update_cartera_data(n_clicks):
    """
    Callback central para recargar TODOS los datos cuando se presiona actualizar.
    """
    if n_clicks > 0:
        try:
            start_time = time.time()

            result = analyzer.reload_data()

            load_time = time.time() - start_time

            return {
                'last_update': n_clicks,
                'timestamp': datetime.now().isoformat(),
                'success': True,
                'load_time': load_time,
                'records_count': len(result)
            }

        except Exception as e:
            print(f"❌ [CarteraPage] Error en actualización #{n_clicks}: {e}")
            return {
                'last_update': n_clicks,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'success': False
            }

    return dash.no_update


@callback(
    Output('cartera-notification-area', 'children'),
    [Input('cartera-data-store', 'data')],
    prevent_initial_call=True
)
def show_update_notification(data_store):
    """
    Mostrar notificación cuando se actualicen los datos.
    """
    if data_store and data_store.get('last_update', 0) > 0:
        if data_store.get('error'):
            return html.Div([
                html.Div([
                    html.Span("❌", style={'marginRight': '8px'}),
                    html.Span("Error al actualizar datos"),
                    html.Br(),
                    html.Small(str(data_store.get('error', ''))[:100] + "...",
                               style={'fontSize': '10px', 'opacity': '0.8'})
                ], style={
                    'backgroundColor': '#e74c3c',
                    'color': 'white',
                    'padding': '12px 16px',
                    'borderRadius': '6px',
                    'marginBottom': '10px',
                    'boxShadow': '0 4px 8px rgba(0,0,0,0.2)',
                    'animation': 'slideIn 0.3s ease-out',
                    'fontSize': '12px'
                })
            ])
        else:
            # Notificación de éxito
            load_time = data_store.get('load_time', 0)
            records_count = data_store.get('records_count', 0)

            return html.Div([
                html.Div([
                    html.Span("✅", style={'marginRight': '8px'}),
                    html.Span("Datos actualizados correctamente"),
                    html.Br(),
                    html.Small(f"{records_count} registros en {load_time:.1f}s",
                               style={'fontSize': '10px', 'opacity': '0.8'})
                ], style={
                    'backgroundColor': '#27ae60',
                    'color': 'white',
                    'padding': '12px 16px',
                    'borderRadius': '6px',
                    'marginBottom': '10px',
                    'boxShadow': '0 4px 8px rgba(0,0,0,0.2)',
                    'animation': 'slideIn 0.3s ease-out',
                    'fontSize': '12px'
                }, id='cartera-success-notification')
            ])

    return []


@callback(
    [Output('cartera-btn-actualizar', 'children'),
     Output('cartera-btn-actualizar', 'disabled')],
    [Input('cartera-data-store', 'data')],
    prevent_initial_call=True
)
def update_button_state(data_store):
    """
    Actualizar estado del botón durante y después de la carga.
    """
    if data_store and data_store.get('last_update', 0) > 0:
        if data_store.get('success', True):
            # Actualización exitosa - botón normal
            return [
                html.Span("🔄", style={'marginRight': '8px'}),
                'Actualizar Datos'
            ], False
        else:
            # Error - botón con indicador de error
            return [
                html.Span("⚠️", style={'marginRight': '8px'}),
                'Reintentar'
            ], False

    # Estado normal
    return [
        html.Span("🔄", style={'marginRight': '8px'}),
        'Actualizar Datos'
    ], False


@callback(
    [Output('cartera-card-1-title', 'style'),
     Output('cartera-card-2-title', 'style'),
     Output('cartera-card-3-title', 'style'),
     Output('cartera-card-4-title', 'style'),
     Output('cartera-card-5-title', 'style'),
     Output('cartera-card-6-title', 'style'),
     Output('cartera-card-7-title', 'style'),
     Output('cartera-card-8-title', 'style')],
    [Input('cartera-theme-store', 'data')]
)
def update_card_title_colors(theme):
    title_color = '#ffffff' if theme == 'dark' else '#34495e'
    title_style = {
        'color': title_color,
        'fontSize': '14px',
        'margin': '0 0 10px 0',
        'fontFamily': 'Inter'
    }
    return [title_style] * 8


@callback(
    [Output('cartera-dropdown-container', 'style'),
     Output('cartera-dropdown-label', 'style')],
    [Input('session-store', 'data')]
)
def update_dropdown_visibility(session_data):
    """
    Mostrar/ocultar dropdown según permisos del usuario.
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
                'marginLeft': '5%'
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
    [Output('cartera-theme-store', 'data'),
     Output('cartera-theme-icon', 'children'),
     Output('cartera-theme-text', 'children'),
     Output('cartera-theme-toggle', 'style'),
     Output('cartera-main-container', 'style'),
     Output('cartera-header-container', 'style'),
     Output('cartera-titulo-dashboard', 'style')],
    [Input('cartera-theme-toggle', 'n_clicks')],
    [State('cartera-theme-store', 'data')]
)
def toggle_theme(n_clicks, current_theme):
    """
    Toggle between light and dark themes with improved styling.
    """
    if n_clicks % 2 == 1:
        new_theme = 'dark'
        icon = '☀️'
        text = 'Claro'
        button_style = {
            'backgroundColor': '#495057',
            'border': '2px solid #6c757d',
            'borderRadius': '12px',
            'padding': '10px 16px',
            'cursor': 'pointer',
            'fontFamily': 'Inter',
            'fontSize': '13px',
            'fontWeight': '500',
            'transition': 'all 0.3s ease',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.3)',
            'height': '40px',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'color': '#ffffff',
            'outline': 'none'
        }
        title_style = {
            'textAlign': 'center',
            'fontSize': '2.5rem',
            'fontWeight': '700',
            'fontFamily': 'Inter',
            'webkitBackgroundClip': 'text',
            'backgroundClip': 'text',
            'margin': '0 0 20px 0',
            'letterSpacing': '-0.02em',
            'textShadow': '0 2px 4px rgba(255,255,255,0.1)'
        }
    else:
        new_theme = 'light'
        icon = '🌙'
        text = 'Oscuro'
        button_style = {
            'backgroundColor': '#f8f9fa',
            'border': '2px solid #e9ecef',
            'borderRadius': '12px',
            'padding': '10px 16px',
            'cursor': 'pointer',
            'fontFamily': 'Inter',
            'fontSize': '13px',
            'fontWeight': '500',
            'transition': 'all 0.3s ease',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
            'height': '40px',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'color': '#212529',
            'outline': 'none'
        }
        title_style = {
            'textAlign': 'center',
            'fontSize': '2.5rem',
            'fontWeight': '700',
            'fontFamily': 'Inter',
            'webkitBackgroundClip': 'text',
            'backgroundClip': 'text',
            'margin': '0 0 20px 0',
            'letterSpacing': '-0.02em',
            'textShadow': '0 2px 4px rgba(0,0,0,0.1)'
        }

    theme_styles = get_theme_styles(new_theme)

    main_style = {
        'fontFamily': 'Inter',
        'backgroundColor': theme_styles['bg_color'],
        'padding': '20px',
        'color': theme_styles['text_color']
    }

    header_style = {
        'marginBottom': '35px',
        'padding': '25px',
        'backgroundColor': theme_styles['paper_color'],
        'borderRadius': '16px',
        'boxShadow': theme_styles['card_shadow']
    }

    return new_theme, icon, text, button_style, main_style, header_style, title_style


@callback(
    [Output('cartera-dropdown-vendedor', 'style'),
     Output('cartera-dropdown-vendedor', 'className'),
     Output('cartera-dropdown-cliente', 'style'),
     Output('cartera-dropdown-cliente', 'className')],
    [Input('cartera-theme-store', 'data'),
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
    else:
        vendedor_style = dropdown_style.copy()

    # Cliente dropdown always visible
    cliente_style = dropdown_style.copy()

    # CSS class for dark theme
    css_class = 'dash-dropdown dark-theme' if theme == 'dark' else 'dash-dropdown'

    return vendedor_style, css_class, cliente_style, css_class


# Card styles callback
@callback(
    [Output('cartera-card-1', 'style'),
     Output('cartera-card-2', 'style'),
     Output('cartera-card-3', 'style'),
     Output('cartera-card-4', 'style'),
     Output('cartera-card-5', 'style'),
     Output('cartera-card-6', 'style'),
     Output('cartera-card-7', 'style'),
     Output('cartera-card-8', 'style')],
    [Input('cartera-theme-store', 'data')]
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
    [Output('cartera-row1-container', 'style'),
     Output('cartera-row2-container', 'style'),
     Output('cartera-row2-5-container', 'style'),
     Output('cartera-cliente-detalle-container', 'style'),
     Output('cartera-row3-container', 'style'),
     Output('cartera-row5-container', 'style'),
     Output('cartera-row6-container', 'style'),
     Output('cartera-config-container', 'style')],
    [Input('cartera-theme-store', 'data')]
)
def update_container_styles(theme):
    """
    Update styles for chart containers based on theme.
    """
    theme_styles = get_theme_styles(theme)

    chart_style = {
        'backgroundColor': theme_styles['paper_color'],
        'padding': '20px',
        'borderRadius': '8px',
        'boxShadow': theme_styles['card_shadow'],
        'margin': '10px 0',
        'color': theme_styles['text_color']
    }

    config_style = {
        'backgroundColor': theme_styles['paper_color'],
        'padding': '20px',
        'borderRadius': '8px',
        'margin': '10px 0',
        'color': theme_styles['text_color']
    }

    return chart_style, chart_style, chart_style, chart_style, chart_style, chart_style, chart_style, config_style


@callback(
    Output('cartera-titulo-dashboard', 'children'),
    [Input('session-store', 'data'),
     Input('cartera-dropdown-vendedor', 'value')]
)
def update_title(session_data, dropdown_value):
    """
    Update dashboard title based on user permissions and selection.
    """
    from utils import can_see_all_vendors, get_user_vendor_filter

    try:
        if not session_data:
            return "Dashboard de Cartera"

        if can_see_all_vendors(session_data):
            vendedor = dropdown_value if dropdown_value else 'Todos'
            if vendedor == 'Todos':
                return "Dashboard de Cartera - Todos los Vendedores"
            return f"Dashboard de Cartera - {vendedor}"
        else:
            vendor = get_user_vendor_filter(session_data)
            return f"Dashboard de Cartera - {vendor}"
    except Exception as e:
        print(f"Error en update_title: {e}")
        return "Dashboard de Cartera"


@callback(
    Output('cartera-dropdown-cliente', 'options'),
    [Input('session-store', 'data'),
     Input('cartera-dropdown-vendedor', 'value'),
     Input('cartera-data-store', 'data')]
)
def update_cliente_dropdown_options(session_data, dropdown_value, data_store):
    """
    Update client dropdown options based on selected vendor.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        clientes = analyzer.get_clientes_list(vendedor)

        return [{'label': cliente, 'value': cliente} for cliente in clientes]
    except Exception as e:
        print(f"Error en update_cliente_dropdown_options: {e}")
        return []


# @callback(
#     Output('cartera-tabla-cliente-detalle', 'children'),
#     [Input('cartera-dropdown-cliente', 'value'),
#      Input('session-store', 'data'),
#      Input('cartera-dropdown-vendedor', 'value'),
#      Input('cartera-theme-store', 'data')]
# )
# def update_cliente_detalle_table(cliente_seleccionado, session_data, dropdown_value, theme):
#     """
#     Update client detail table with current and overdue portfolio sections.
#     """
#     try:
#         if not cliente_seleccionado:
#             return html.Div([
#                 html.P("Seleccione un cliente para ver el detalle de su cartera.",
#                        style={'textAlign': 'center', 'color': 'gray', 'fontSize': '16px', 'fontFamily': 'Inter'})
#             ])

#         vendedor = get_selected_vendor(session_data, dropdown_value)
#         detalle = analyzer.get_cliente_detalle(cliente_seleccionado, vendedor)
#         theme_styles = get_theme_styles(theme)

#         if not detalle['sin_vencer'].empty or not detalle['vencida'].empty:
#             # Header con forma de pago
#             elementos = [
#                 html.Div([
#                     html.H4(f"Forma de Pago: {detalle['forma_pago']}", style={
#                         'backgroundColor': '#17a2b8',
#                         'color': 'white',
#                         'padding': '12px 20px',
#                         'margin': '0 0 20px 0',
#                         'borderRadius': '8px',
#                         'fontFamily': 'Inter',
#                         'textAlign': 'center',
#                         'fontSize': '16px',
#                         'fontWeight': 'bold'
#                     })
#                 ])
#             ]

#             # Sección Cartera Vencida (Rojo)
#             if not detalle['vencida'].empty:
#                 elementos.append(
#                     html.Div([
#                         html.H4("📕 Cartera Vencida", style={
#                             'backgroundColor': '#e74c3c',
#                             'color': 'white',
#                             'padding': '10px 15px',
#                             'margin': '10px 0 15px 0',
#                             'borderRadius': '6px',
#                             'fontFamily': 'Inter',
#                             'fontSize': '16px',
#                             'fontWeight': 'bold'
#                         }),
#                         crear_tabla_documentos(
#                             detalle['vencida'],
#                             theme_styles,
#                             'vencida',
#                             theme
#                         )
#                     ])
#                 )

#             # Sección Cartera Sin Vencer (Verde)
#             if not detalle['sin_vencer'].empty:
#                 elementos.append(
#                     html.Div([
#                         html.H4("📗 Cartera Sin Vencer", style={
#                             'backgroundColor': '#27ae60',
#                             'color': 'white',
#                             'padding': '10px 15px',
#                             'margin': '10px 0 15px 0',
#                             'borderRadius': '6px',
#                             'fontFamily': 'Inter',
#                             'fontSize': '16px',
#                             'fontWeight': 'bold'
#                         }),
#                         crear_tabla_documentos(
#                             detalle['sin_vencer'],
#                             theme_styles,
#                             'sin_vencer',
#                             theme
#                         )
#                     ])
#                 )

#             return html.Div(elementos)
#         else:
#             return html.Div([
#                 html.P("No se encontraron documentos para este cliente.",
#                        style={'textAlign': 'center', 'color': 'gray', 'fontSize': '16px', 'fontFamily': 'Inter'})
#             ])

#     except Exception as e:
#         print(f"Error en update_cliente_detalle_table: {e}")
#         return html.Div([
#             html.P("Error al cargar los datos del cliente.",
#                    style={'textAlign': 'center', 'color': '#e74c3c', 'fontSize': '16px', 'fontFamily': 'Inter'})
#         ])
@callback(
    Output('cartera-tabla-cliente-detalle', 'children'),
    [Input('cartera-dropdown-cliente', 'value'),
     Input('session-store', 'data'),
     Input('cartera-dropdown-vendedor', 'value'),
     Input('cartera-theme-store', 'data')]
)
def update_cliente_detalle_table(cliente_seleccionado, session_data, dropdown_value, theme):
    """
    Update client detail table with unified current and overdue portfolio.
    """
    try:
        if not cliente_seleccionado:
            return html.Div([
                html.P("Seleccione un cliente para ver el detalle de su cartera.",
                       style={'textAlign': 'center', 'color': 'gray', 'fontSize': '16px', 'fontFamily': 'Inter'})
            ])

        vendedor = get_selected_vendor(session_data, dropdown_value)
        detalle = analyzer.get_cliente_detalle(cliente_seleccionado, vendedor)
        theme_styles = get_theme_styles(theme)

        if not detalle['documentos'].empty:
            # Header con forma de pago
            elementos = [
                html.Div([
                    html.H4(f"Forma de Pago: {detalle['forma_pago']}", style={
                        'backgroundColor': '#17a2b8',
                        'color': 'white',
                        'padding': '12px 20px',
                        'margin': '0 0 20px 0',
                        'borderRadius': '8px',
                        'fontFamily': 'Inter',
                        'textAlign': 'center',
                        'fontSize': '16px',
                        'fontWeight': 'bold'
                    })
                ])
            ]

            # Crear tabla unificada
            elementos.append(
                crear_tabla_unificada(
                    detalle['documentos'], theme_styles, theme)
            )

            return html.Div(elementos)
        else:
            return html.Div([
                html.P("No se encontraron documentos para este cliente.",
                       style={'textAlign': 'center', 'color': 'gray', 'fontSize': '16px', 'fontFamily': 'Inter'})
            ])

    except Exception as e:
        print(f"Error en update_cliente_detalle_table: {e}")
        return html.Div([
            html.P("Error al cargar los datos del cliente.",
                   style={'textAlign': 'center', 'color': '#e74c3c', 'fontSize': '16px', 'fontFamily': 'Inter'})
        ])


def crear_tabla_unificada(df, theme_styles, theme):
    """
    Create a unified table for both overdue and current documents.
    """
    if df.empty:
        return html.P("No hay documentos para este cliente.")

    # Header row
    header_style = {
        'backgroundColor': '#2c3e50',
        'color': 'white',
        'padding': '12px 8px',
        'fontWeight': 'bold',
        'fontSize': '13px',
        'fontFamily': 'Inter',
        'textAlign': 'center',
        'border': '1px solid #34495e',
        'position': 'sticky',
        'top': '0',
        'zIndex': '10'
    }

    # Base cell style
    cell_style_base = {
        'padding': '10px 8px',
        'fontSize': '12px',
        'fontFamily': 'Inter',
        'textAlign': 'center',
        'border': '1px solid #dee2e6'
    }

    # Create table rows
    table_rows = [
        html.Tr([
            html.Th("Estado", style={**header_style, 'width': '80px'}),
            html.Th("Documento", style={**header_style, 'width': '80px'}),
            html.Th("Valor", style={**header_style, 'width': '90px'}),
            html.Th("Aplicado", style={**header_style, 'width': '90px'}),
            html.Th("Saldo", style={**header_style, 'width': '90px'}),
            html.Th("Fecha", style={**header_style, 'width': '90px'}),
            html.Th("Vencimiento", style={**header_style, 'width': '90px'}),
            html.Th("Días", style={**header_style, 'width': '100px'}),
            html.Th("Notas", style={**header_style,
                    'width': '190px', 'maxWidth': '190px'})
        ])
    ]

    for i, (_, row) in enumerate(df.iterrows()):
        # Determine document status based on dias_vencidos
        dias_vencidos = int(row['dias_vencidos']) if pd.notna(
            row['dias_vencidos']) else None

        # Determine status and colors
        if dias_vencidos is not None and dias_vencidos == 0:
            estado_text = 'VENCE HOY'
            estado_bg = '#FF8C42'

            if theme == 'dark':
                row_bg = '#4a3520' if i % 2 == 0 else '#5a4028'  # Dark orange
            else:
                row_bg = '#fff3e0' if i % 2 == 0 else '#ffe0b2'  # Light orange

        elif row['tipo'] == 'vencida' or (dias_vencidos is not None and dias_vencidos > 0):
            estado_text = 'VENCIDA'
            estado_bg = '#e74c3c'

            if theme == 'dark':
                row_bg = '#4a2d2d' if i % 2 == 0 else '#5a3535'  # Dark red
            else:
                row_bg = '#f8e8e8' if i % 2 == 0 else '#f5c6cb'  # Light red

        else:
            if abs(dias_vencidos) >= 2:
                estado_text = 'SIN VENCER'
                estado_bg = '#27ae60'

                if theme == 'dark':
                    row_bg = '#2d4a35' if i % 2 == 0 else '#35553d'  # Dark green
                else:
                    row_bg = '#e8f5e8' if i % 2 == 0 else '#d4edda'  # Light green
            else:
                estado_text = 'PRÓXIMO A VENCER'
                estado_bg = '#FFB74D'

                if theme == 'dark':
                    row_bg = '#4a3520' if i % 2 == 0 else '#5a4028'  # Dark orange
                else:
                    row_bg = '#fff3e0' if i % 2 == 0 else '#ffe0b2'  # Light orange

        cell_style = cell_style_base.copy()
        cell_style['backgroundColor'] = row_bg

        # Estado cell with special styling
        estado_style = {
            **cell_style_base,
            'backgroundColor': estado_bg,
            'color': 'white',
            'fontWeight': 'bold',
            'fontSize': '10px',
            'border': '1px solid #dee2e6',
            'textAlign': 'center'
        }

        # Format dates
        fecha_str = row['fecha'].strftime(
            '%Y-%m-%d') if pd.notna(row['fecha']) else 'N/A'
        vencimiento_str = row['vencimiento'].strftime(
            '%Y-%m-%d') if pd.notna(row['vencimiento']) else 'N/A'

        # Format days overdue with colors
        if isinstance(dias_vencidos, int):
            if dias_vencidos > 0:
                dias_display = f"{dias_vencidos} días (vencidos)"
                dias_color = '#e74c3c'
            elif dias_vencidos < 0:
                abs_dias_vencidos = abs(dias_vencidos)

                if abs_dias_vencidos > 1:
                    dias_display = f"{abs(dias_vencidos)} días (por vencer)"
                    dias_color = '#27ae60'
                else:
                    dias_display = f"Vence mañana"
                    dias_color = '#FFB74D'
            else:
                dias_display = "Vence hoy"
                dias_color = '#FF8C42'  # Mismo color que VENCE HOY
        else:
            dias_display = 'N/A'
            dias_color = '#95a5a6'

        # Handle notas column intelligently
        notas_text = str(row.get('notas', 'Sin notas'))
        if len(notas_text) > 40:
            notas_display = notas_text[:37] + "..."
            notas_title = notas_text  # Full text in title for hover
        else:
            notas_display = notas_text
            notas_title = notas_text

        notas_style = {
            **cell_style,
            'maxWidth': '190px',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'whiteSpace': 'nowrap',
            'textAlign': 'left',
            'cursor': 'help' if len(notas_text) > 30 else 'default'
        }

        table_rows.append(
            html.Tr([
                html.Td(estado_text, style=estado_style),
                html.Td(row['documento_id'], style=cell_style),
                html.Td(format_currency_int(row['valor']), style=cell_style),
                html.Td(format_currency_int(
                    row['aplicado']), style=cell_style),
                html.Td(format_currency_int(row['saldo']), style=cell_style),
                html.Td(fecha_str, style=cell_style),
                html.Td(vencimiento_str, style=cell_style),
                html.Td(dias_display, style={
                        **cell_style, 'color': dias_color, 'fontWeight': 'bold'}),
                html.Td(notas_display, style=notas_style, title=notas_title)
            ])
        )

    # Container with scroll
    return html.Div([
        html.Div([
            html.Table(
                table_rows,
                style={
                    'width': '100%',
                    'borderCollapse': 'collapse',
                    'fontSize': '12px',
                    'fontFamily': 'Inter'
                }
            )
        ], style={
            'maxHeight': '600px',
            'maxWidth': '100%',
            'overflowY': 'auto',
            'overflowX': 'auto',
            'border': f'2px solid {theme_styles["line_color"]}',
            'borderRadius': '8px',
            'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'
        }),

        # Updated Legend with three states
        html.Div([
            html.Div([
                html.Span("●", style={'color': '#e74c3c',
                          'marginRight': '5px', 'fontSize': '16px'}),
                html.Span("Vencida", style={
                          'marginRight': '15px', 'fontSize': '12px'}),
                html.Span("●", style={'color': '#FF8C42',
                          'marginRight': '5px', 'fontSize': '16px'}),
                html.Span("Vence Hoy", style={
                          'marginRight': '15px', 'fontSize': '12px'}),
                html.Span("●", style={'color': '#FFB74D',
                          'marginRight': '5px', 'fontSize': '16px'}),
                html.Span("Vence mañana", style={
                          'marginRight': '15px', 'fontSize': '12px'}),
                html.Span("●", style={'color': '#27ae60',
                          'marginRight': '5px', 'fontSize': '16px'}),
                html.Span("Sin Vencer", style={'fontSize': '12px'})
            ], style={
                'textAlign': 'center',
                'marginTop': '10px',
                'fontFamily': 'Inter',
                'color': theme_styles['text_color']
            })
        ])
    ])
# def crear_tabla_unificada(df, theme_styles, theme):
#     """
#     Create a unified table for both overdue and current documents.
#     """
#     if df.empty:
#         return html.P("No hay documentos para este cliente.")

#     # Header row
#     header_style = {
#         'backgroundColor': '#2c3e50',
#         'color': 'white',
#         'padding': '12px 8px',
#         'fontWeight': 'bold',
#         'fontSize': '13px',
#         'fontFamily': 'Inter',
#         'textAlign': 'center',
#         'border': '1px solid #34495e',
#         'position': 'sticky',
#         'top': '0',
#         'zIndex': '10'
#     }

#     # Base cell style
#     cell_style_base = {
#         'padding': '10px 8px',
#         'fontSize': '12px',
#         'fontFamily': 'Inter',
#         'textAlign': 'center',
#         'border': '1px solid #dee2e6'
#     }

#     # Create table rows
#     table_rows = [
#         html.Tr([
#             html.Th("Estado", style={**header_style, 'width': '80px'}),
#             html.Th("Documento", style={**header_style, 'width': '100px'}),
#             html.Th("Valor", style={**header_style, 'width': '120px'}),
#             html.Th("Aplicado", style={**header_style, 'width': '120px'}),
#             html.Th("Saldo", style={**header_style, 'width': '120px'}),
#             html.Th("Fecha", style={**header_style, 'width': '100px'}),
#             html.Th("Vencimiento", style={**header_style, 'width': '100px'}),
#             html.Th("Días", style={**header_style, 'width': '80px'}),
#             html.Th("Notas", style={**header_style,
#                     'width': '150px', 'maxWidth': '150px'})
#         ])
#     ]

#     for i, (_, row) in enumerate(df.iterrows()):
#         # Determine row colors based on type and theme
#         if theme == 'dark':
#             if row['tipo'] == 'vencida':
#                 row_bg = '#4a2d2d' if i % 2 == 0 else '#5a3535'  # Dark red
#                 estado_bg = '#e74c3c'
#                 estado_text = 'VENCIDA'
#             else:
#                 row_bg = '#2d4a35' if i % 2 == 0 else '#35553d'  # Dark green
#                 estado_bg = '#27ae60'
#                 estado_text = 'AL DÍA'
#         else:
#             if row['tipo'] == 'vencida':
#                 row_bg = '#f8e8e8' if i % 2 == 0 else '#f5c6cb'  # Light red
#                 estado_bg = '#e74c3c'
#                 estado_text = 'VENCIDA'
#             else:
#                 row_bg = '#e8f5e8' if i % 2 == 0 else '#d4edda'  # Light green
#                 estado_bg = '#27ae60'
#                 estado_text = 'AL DÍA'

#         cell_style = cell_style_base.copy()
#         cell_style['backgroundColor'] = row_bg

#         # Estado cell with special styling
#         estado_style = {
#             **cell_style_base,
#             'backgroundColor': estado_bg,
#             'color': 'white',
#             'fontWeight': 'bold',
#             'fontSize': '10px',
#             'border': '1px solid #dee2e6'
#         }

#         # Format dates
#         fecha_str = row['fecha'].strftime(
#             '%Y-%m-%d') if pd.notna(row['fecha']) else 'N/A'
#         vencimiento_str = row['vencimiento'].strftime(
#             '%Y-%m-%d') if pd.notna(row['vencimiento']) else 'N/A'

#         # Format days overdue
#         dias_vencidos = int(row['dias_vencidos']) if pd.notna(
#             row['dias_vencidos']) else 'N/A'
#         if isinstance(dias_vencidos, int):
#             if dias_vencidos > 0:
#                 dias_display = f"{dias_vencidos}"
#                 dias_color = '#e74c3c'
#             elif dias_vencidos < 0:
#                 dias_display = f"{abs(dias_vencidos)}"
#                 dias_color = '#f39c12'
#             else:
#                 dias_display = "0"
#                 dias_color = '#e67e22'
#         else:
#             dias_display = 'N/A'
#             dias_color = '#95a5a6'

#         # Handle notas column intelligently
#         notas_text = str(row.get('notas', 'Sin notas'))
#         if len(notas_text) > 30:
#             notas_display = notas_text[:27] + "..."
#             notas_title = notas_text  # Full text in title for hover
#         else:
#             notas_display = notas_text
#             notas_title = notas_text

#         notas_style = {
#             **cell_style,
#             'maxWidth': '150px',
#             'overflow': 'hidden',
#             'textOverflow': 'ellipsis',
#             'whiteSpace': 'nowrap',
#             'textAlign': 'left',
#             'cursor': 'help' if len(notas_text) > 30 else 'default'
#         }

#         table_rows.append(
#             html.Tr([
#                 html.Td(estado_text, style=estado_style),
#                 html.Td(row['documento_id'], style=cell_style),
#                 html.Td(format_currency_int(row['valor']), style=cell_style),
#                 html.Td(format_currency_int(
#                     row['aplicado']), style=cell_style),
#                 html.Td(format_currency_int(row['saldo']), style=cell_style),
#                 html.Td(fecha_str, style=cell_style),
#                 html.Td(vencimiento_str, style=cell_style),
#                 html.Td(dias_display, style={
#                         **cell_style, 'color': dias_color, 'fontWeight': 'bold'}),
#                 html.Td(notas_display, style=notas_style, title=notas_title)
#             ])
#         )

#     # Container with scroll
#     return html.Div([
#         html.Div([
#             html.Table(
#                 table_rows,
#                 style={
#                     'width': '100%',
#                     'borderCollapse': 'collapse',
#                     'fontSize': '12px',
#                     'fontFamily': 'Inter'
#                 }
#             )
#         ], style={
#             'maxHeight': '600px',
#             'maxWidth': '100%',
#             'overflowY': 'auto',
#             'overflowX': 'auto',
#             'border': f'2px solid {theme_styles["line_color"]}',
#             'borderRadius': '8px',
#             'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'
#         }),

#         # Legend
#         html.Div([
#             html.Div([
#                 html.Span("●", style={'color': '#e74c3c',
#                           'marginRight': '5px', 'fontSize': '16px'}),
#                 html.Span("Cartera Vencida", style={
#                           'marginRight': '20px', 'fontSize': '12px'}),
#                 html.Span("●", style={'color': '#27ae60',
#                           'marginRight': '5px', 'fontSize': '16px'}),
#                 html.Span("Cartera al Día", style={'fontSize': '12px'})
#             ], style={
#                 'textAlign': 'center',
#                 'marginTop': '10px',
#                 'fontFamily': 'Inter',
#                 'color': theme_styles['text_color']
#             })
#         ])
#     ])


def crear_tabla_documentos(df, theme_styles, tipo, theme):
    """
    Create a formatted table for documents.
    """
    if df.empty:
        return html.P("No hay documentos en esta categoría.")

    # Header row
    header_style = {
        'backgroundColor': '#2c3e50',
        'color': 'white',
        'padding': '12px 8px',
        'fontWeight': 'bold',
        'fontSize': '13px',
        'fontFamily': 'Inter',
        'textAlign': 'center',
        'border': '1px solid #34495e'
    }

    # Data row style based on type
    if theme == 'dark':
        if tipo == 'sin_vencer':
            row_bg = '#1e3a28'      # Verde oscuro
            row_bg_alt = '#2d4a35'  # Verde más oscuro
        else:  # vencida
            row_bg = '#3a1e1e'      # Rojo oscuro
            row_bg_alt = '#4a2d2d'  # Rojo más oscuro
    else:  # light theme
        if tipo == 'sin_vencer':
            row_bg = '#e8f5e8'
            row_bg_alt = '#d4edda'
        else:  # vencida
            row_bg = '#f8e8e8'
            row_bg_alt = '#f5c6cb'

    cell_style_base = {
        'padding': '10px 8px',
        'fontSize': '12px',
        'fontFamily': 'Inter',
        'textAlign': 'center',
        'border': '1px solid #dee2e6'
    }

    # Create table rows
    table_rows = [
        html.Tr([
            html.Th("Documento", style=header_style),
            html.Th("Valor", style=header_style),
            html.Th("Aplicado", style=header_style),
            html.Th("Saldo", style=header_style),
            html.Th("Fecha", style=header_style),
            html.Th("Vencimiento", style=header_style),
            html.Th("Notas", style=header_style),
            html.Th("Días Vencidos", style=header_style)
        ])
    ]

    for i, (_, row) in enumerate(df.iterrows()):
        cell_style = cell_style_base.copy()
        cell_style['backgroundColor'] = row_bg if i % 2 == 0 else row_bg_alt

        # Format dates
        fecha_str = row['fecha'].strftime(
            '%Y-%m-%d') if pd.notna(row['fecha']) else 'N/A'
        vencimiento_str = row['vencimiento'].strftime(
            '%Y-%m-%d') if pd.notna(row['vencimiento']) else 'N/A'

        # Format days overdue
        dias_vencidos = int(row['dias_vencidos']) if pd.notna(
            row['dias_vencidos']) else 'N/A'
        if isinstance(dias_vencidos, int):
            if dias_vencidos > 0:
                dias_display = f"{dias_vencidos} días"
                dias_color = '#e74c3c'
            elif dias_vencidos < 0:
                dias_display = f"{abs(dias_vencidos)} días (por vencer)"
                dias_color = '#f39c12'
            else:
                dias_display = "Vence hoy"
                dias_color = '#e67e22'
        else:
            dias_display = 'N/A'
            dias_color = '#95a5a6'

        table_rows.append(
            html.Tr([
                html.Td(row['documento_id'], style=cell_style),
                html.Td(format_currency_int(row['valor']), style=cell_style),
                html.Td(format_currency_int(
                    row['aplicado']), style=cell_style),
                html.Td(format_currency_int(row['saldo']), style=cell_style),
                html.Td(fecha_str, style=cell_style),
                html.Td(vencimiento_str, style=cell_style),
                html.Td(row['notas'], style=cell_style),
                html.Td(dias_display, style={
                        **cell_style, 'color': dias_color, 'fontWeight': 'bold'})
            ])
        )

    return html.Table(
        table_rows,
        style={
            'width': '100%',
            'borderCollapse': 'collapse',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'borderRadius': '6px',
            'overflow': 'hidden'
        }
    )


@callback(
    [Output('cartera-total-cartera', 'children'),
     Output('cartera-total-vencida', 'children'),
     Output('cartera-total-sin-vencer', 'children'),
     Output('cartera-calidad-cartera', 'children'),
     Output('cartera-total-clientes', 'children'),
     Output('cartera-clientes-vencida', 'children'),
     Output('cartera-num-facturas', 'children'),
     Output('cartera-porcentaje-vencida', 'children')],
    [Input('session-store', 'data'),
     Input('cartera-dropdown-vendedor', 'value'),
     Input('cartera-data-store', 'data')]
)
def update_cards(session_data, dropdown_value, data_store):
    """
    Update summary cards with portfolio statistics.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        resumen = analyzer.get_resumen(vendedor)

        total_cartera = format_currency_int(resumen['total_cartera'])
        total_vencida = format_currency_int(resumen['total_vencida'])
        total_sin_vencer = format_currency_int(resumen['total_sin_vencer'])
        calidad_cartera = f"{resumen['porcentaje_al_dia']:.1f}%"
        total_clientes = f"{resumen['num_clientes']:,}"
        clientes_vencida = f"{resumen['clientes_vencida']:,}"
        num_facturas = f"{resumen['num_facturas']:,}"

        porcentaje = (resumen['total_vencida'] / resumen['total_cartera']
                      * 100) if resumen['total_cartera'] != 0 else 0
        porcentaje_vencida = f"{porcentaje:.1f}%"

        return total_cartera, total_vencida, total_sin_vencer, calidad_cartera, total_clientes, clientes_vencida, num_facturas, porcentaje_vencida
    except Exception as e:
        print(f"❌ [update_cards] Error: {e}")
        return "$0", "$0", "$0", "0%", "0", "0", "0", "0%"


@callback(
    Output('cartera-grafico-rangos', 'figure'),
    [Input('session-store', 'data'),
     Input('cartera-dropdown-vendedor', 'value'),
     Input('cartera-data-store', 'data'),
     Input('cartera-theme-store', 'data')]
)
def update_rangos(session_data, dropdown_value, n_clicks, theme):
    """
    Update overdue ranges chart with pastel colors.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_rangos_vencimiento(vendedor)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            fig = px.bar(title="No hay datos disponibles")
            return fig

        # Create modern chart with pastel colors
        fig = go.Figure()

        for i, row in data.iterrows():
            fig.add_trace(go.Bar(
                x=[row['rango']],
                y=[row['saldo']],
                name=row['rango'],
                marker_color=PALETA_PASTELES_BARRAS[i % len(
                    PALETA_PASTELES_BARRAS)],
                text=[format_currency_int(row['saldo'])],
                textposition='outside',
                opacity=0.6,
                hovertemplate=f"<b>{row['rango']}</b><br>" +
                             f"Valor: {format_currency_int(row['saldo'])}<br>" +
                             f"Documentos: {row['documento_id']}<extra></extra>"
            ))

        fig.update_layout(
            title="",
            xaxis_title="Rango de Vencimiento",
            yaxis_title="Valor ($)",
            height=450,
            showlegend=False,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=12,
                      color=theme_styles['text_color']),
            xaxis=dict(
                showgrid=False,
                tickangle=-45,
                linecolor=theme_styles['line_color']
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                linecolor=theme_styles['line_color'],
                tickformat='$,.0f',
                automargin=True
            ),
            margin=dict(t=60, b=120, l=100, r=60),
            autosize=True
        )

        return fig
    except Exception as e:
        print(f"Error en update_rangos: {e}")
        return px.bar(title="Error al cargar datos")


@callback(
    Output('cartera-grafico-forma-pago', 'figure'),
    [Input('session-store', 'data'),
     Input('cartera-dropdown-vendedor', 'value'),
     Input('cartera-data-store', 'data'),
     Input('cartera-theme-store', 'data')]
)
def update_forma_pago(session_data, dropdown_value, n_clicks, theme):
    """
    Update payment method distribution chart with pastel colors.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_forma_pago(vendedor)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            fig = px.pie(title="No hay datos disponibles")
            return fig

        # Modern donut chart with pastel colors
        fig = go.Figure(data=[go.Pie(
            labels=data['forma_pago'],
            values=data['saldo'],
            hole=.4,
            opacity=0.6,
            textinfo='percent',
            textposition='inside',
            marker=dict(
                colors=PALETA_PASTELES_DONA,
                line=dict(color='#FFFFFF', width=3)
            ),
            hovertemplate="<b>%{label}</b><br>" +
            "Valor: %{customdata}<br>" +
            "Porcentaje: %{percent}<extra></extra>",
            customdata=[format_currency_int(val) for val in data['saldo']]
        )])

        fig.update_layout(
            title="",
            height=350,
            font=dict(family="Inter", size=12,
                      color=theme_styles['text_color']),
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05
            ),
            margin=dict(t=0, b=0, l=0, r=150)
        )

        return fig
    except Exception as e:
        print(f"Error en update_forma_pago: {e}")
        return px.pie(title="Error al cargar datos")


@callback(
    Output('cartera-treemap-cartera', 'figure'),
    [Input('session-store', 'data'),
     Input('cartera-dropdown-vendedor', 'value'),
     Input('cartera-data-store', 'data'),
     Input('cartera-theme-store', 'data')]
)
def update_treemap(session_data, dropdown_value, n_clicks, theme):
    """
    Update portfolio treemap with combined client-company names.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_treemap_data(vendedor)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos disponibles",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=500, paper_bgcolor=theme_styles['plot_bg'])
            return fig

        # Prepare data for treemap without empty parent
        data_filtered = data[data['saldo'] > 0].copy()

        if len(data_filtered) == 0:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos con valores positivos",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=500, paper_bgcolor=theme_styles['plot_bg'])
            return fig

        fig = go.Figure(go.Treemap(
            labels=data_filtered['cliente_completo'],
            values=data_filtered['saldo'],
            parents=[""] * len(data_filtered),  # No parent
            texttemplate="<b>%{label}</b><br>%{customdata}",
            hovertemplate="<b>%{label}</b><br>" +
                         "Valor: %{customdata}<br>" +
                         "<extra></extra>",
            customdata=[format_currency_int(val)
                        for val in data_filtered['saldo']],
            marker=dict(
                colorscale='Aggrnyl_r',
                line=dict(width=2, color='white')
            ),
            textfont=dict(size=12, color='white')
        ))

        fig.update_layout(
            title="",
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
    Output('cartera-treemap-cartera-vencida', 'figure'),
    [Input('session-store', 'data'),
     Input('cartera-dropdown-vendedor', 'value'),
     Input('cartera-data-store', 'data'),
     Input('cartera-theme-store', 'data')]
)
def update_treemap_vencida(session_data, dropdown_value, n_clicks, theme):
    """
    Update overdue portfolio treemap with combined client-company names.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_treemap_data_vencida(vendedor)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay cartera vencida",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=500,
                plot_bgcolor=theme_styles['plot_bg'],
                paper_bgcolor=theme_styles['plot_bg'],
                font=dict(family="Inter", size=12,
                          color=theme_styles['text_color'])
            )
            return fig

        # Prepare data for treemap without empty parent
        data_filtered = data[data['vencida'] > 0].copy()

        if len(data_filtered) == 0:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay cartera vencida con valores positivos",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=500,
                plot_bgcolor=theme_styles['plot_bg'],
                paper_bgcolor=theme_styles['plot_bg'],
                font=dict(family="Inter", size=12,
                          color=theme_styles['text_color'])
            )
            return fig

        fig = go.Figure(go.Treemap(
            labels=data_filtered['cliente_completo'],
            values=data_filtered['vencida'],
            parents=[""] * len(data_filtered),  # No parent
            texttemplate="<b>%{label}</b><br>%{customdata}",
            hovertemplate="<b>%{label}</b><br>" +
                         "Cartera Vencida: %{customdata}<br>" +
                         "<extra></extra>",
            customdata=[format_currency_int(val)
                        for val in data_filtered['vencida']],
            marker=dict(
                colorscale='Agsunset_r',
                line=dict(width=2, color='white')
            ),
            textfont=dict(size=12, color='white')
        ))

        fig.update_layout(
            title="",
            height=500,
            font=dict(family="Inter", size=12,
                      color=theme_styles['text_color']),
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            margin=dict(t=0, b=0, l=0, r=0)
        )

        return fig
    except Exception as e:
        print(f"Error en update_treemap_vencida: {e}")
        return go.Figure()


@callback(
    Output('cartera-top-vencida', 'figure'),
    [Input('session-store', 'data'),
     Input('cartera-dropdown-vendedor', 'value'),
     Input('cartera-data-store', 'data'),
     Input('cartera-theme-store', 'data')]
)
def update_top_vencida(session_data, dropdown_value, n_clicks, theme):
    """
    Update top overdue customers chart with transparency and no color scale.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_top_clientes('vencida', vendedor)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            fig = px.bar(title="No hay cartera vencida")
            fig.update_layout(
                height=400, paper_bgcolor=theme_styles['plot_bg'])
            return fig

        # Create shorter labels for y-axis (just numbers)
        data_sorted = data.sort_values('vencida', ascending=True)
        data_sorted['rank'] = sorted(
            range(1, len(data_sorted) + 1), reverse=True)
        data_sorted['short_label'] = [f"#{i}" for i in data_sorted['rank']]

        fig = px.bar(data_sorted, x='vencida', y='short_label', orientation='h',
                     labels={
                         'vencida': 'Cartera Vencida ($)', 'short_label': 'Top'})

        # Update format with client names inside bars and transparency
        fig.update_traces(
            text=[
                name[:70] + "..." if len(name) > 70 else name for name in data_sorted['cliente_completo']],
            textposition='inside',
            textfont=dict(color='white', size=10),
            marker=dict(
                color='rgba(231, 76, 60, 0.7)',  # Red with transparency
                line=dict(color='rgba(231, 76, 60, 1)', width=1),
                opacity=0.7
            ),
            hovertemplate="<b>%{customdata[0]}</b><br>" +
            "Cartera Vencida: %{customdata[1]}<br>" +
            "<extra></extra>",
            customdata=[[cliente, format_currency_int(val)] for cliente, val in zip(
                data_sorted['cliente_completo'], data_sorted['vencida'])]
        )

        fig.update_layout(
            height=450,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=12,
                      color=theme_styles['text_color']),
            xaxis=dict(
                tickformat='$,.0f',
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                automargin=True
            ),
            yaxis=dict(
                title="Ranking",
                categoryorder='array',
                categoryarray=data_sorted['short_label'],
                automargin=True
            ),
            showlegend=False,
            margin=dict(t=40, b=40, l=80, r=80)
        )
        return fig
    except Exception as e:
        print(f"Error en update_top_vencida: {e}")
        return px.bar(title="Error al cargar datos")


@callback(
    Output('cartera-top-sin-vencer', 'figure'),
    [Input('session-store', 'data'),
     Input('cartera-dropdown-vendedor', 'value'),
     Input('cartera-data-store', 'data'),
     Input('cartera-theme-store', 'data')]
)
def update_top_sin_vencer(session_data, dropdown_value, n_clicks, theme):
    """
    Update top current customers chart with transparency and no color scale.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_top_clientes('sin_vencer', vendedor)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            fig = px.bar(title="No hay cartera sin vencer")
            fig.update_layout(
                height=400, paper_bgcolor=theme_styles['plot_bg'])
            return fig

        # Create shorter labels for y-axis (just numbers)
        data_sorted = data.sort_values('sin_vencer', ascending=True)
        data_sorted['rank'] = sorted(
            range(1, len(data_sorted) + 1), reverse=True)
        data_sorted['short_label'] = [f"#{i}" for i in data_sorted['rank']]

        fig = px.bar(data_sorted, x='sin_vencer', y='short_label', orientation='h',
                     labels={
                         'sin_vencer': 'Cartera Sin Vencer ($)', 'short_label': 'Top'})

        # Update format with client names inside bars and transparency
        fig.update_traces(
            text=[
                name[:70] + "..." if len(name) > 70 else name for name in data_sorted['cliente_completo']],
            textposition='inside',
            textfont=dict(color='white', size=10),
            marker=dict(
                color='rgba(39, 174, 96, 0.7)',  # Green with transparency
                line=dict(color='rgba(39, 174, 96, 1)', width=1),
                opacity=0.7
            ),
            hovertemplate="<b>%{customdata[0]}</b><br>" +
            "Cartera Sin Vencer: %{customdata[1]}<br>" +
            "<extra></extra>",
            customdata=[[cliente, format_currency_int(val)] for cliente, val in zip(
                data_sorted['cliente_completo'], data_sorted['sin_vencer'])]
        )

        fig.update_layout(
            height=450,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=12,
                      color=theme_styles['text_color']),
            xaxis=dict(
                tickformat='$,.0f',
                showgrid=True,
                gridcolor=theme_styles['grid_color']
            ),
            yaxis=dict(
                title="Ranking",
                categoryorder='array',
                categoryarray=data_sorted['short_label'],
                automargin=True
            ),
            showlegend=False,
            margin=dict(t=40, b=40, l=80, r=80)
        )
        return fig
    except Exception as e:
        print(f"Error en update_top_sin_vencer: {e}")
        return px.bar(title="Error al cargar datos")


@callback(
    [Output('cartera-grafico-proximos-vencer', 'figure'),
     Output('cartera-tabla-proximos-vencer', 'children')],
    [Input('cartera-slider-dias', 'value'),
     Input('session-store', 'data'),
     Input('cartera-dropdown-vendedor', 'value'),
     Input('cartera-theme-store', 'data')]
)
def update_proximos_vencer(dias, session_data, dropdown_value, theme):
    """
    Update upcoming expiration chart with urgency-based colors and proper sorting.
    """
    try:
        vendedor = \
            get_selected_vendor(session_data, dropdown_value)
        data_agrupados = \
            analyzer.get_documentos_agrupados_por_dias(
                dias,
                vendedor
            )
        data_documentos_table = \
            analyzer.get_documentos_proximos_vencer(
                dias,
                vendedor
            )
        theme_styles = get_theme_styles(theme)

        # Chart with urgency-based colors and proper stacking
        if data_agrupados.empty:
            fig = go.Figure()
            fig.add_annotation(
                text=f"No hay documentos que venzan en {dias} días",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=450,
                plot_bgcolor=theme_styles['plot_bg'],
                paper_bgcolor=theme_styles['plot_bg'],
                font=dict(family="Inter", size=12,
                          color=theme_styles['text_color'])
            )
        else:
            fig = go.Figure()

            # Create a continuous color scale based on urgency (days)
            max_dias = data_agrupados['dias_hasta_vencimiento'].max()
            min_dias = data_agrupados['dias_hasta_vencimiento'].min()

            def get_urgency_color(dias_hasta_vencimiento):
                """Get color based on urgency (red=urgent, green=less urgent)."""
                if max_dias == min_dias:  # Avoid division by zero
                    normalized = 0.5
                else:
                    # Normalize to 0-1 (0=most urgent=red, 1=least urgent=green)
                    normalized = (dias_hasta_vencimiento -
                                  min_dias) / (max_dias - min_dias)

                # Color transition: Red (urgent) -> Yellow -> Green (less urgent)
                if normalized <= 0.5:
                    # Red to Yellow
                    r = 255
                    g = int(255 * (normalized * 2))
                    b = 0
                else:
                    # Yellow to Green
                    r = int(255 * (2 - normalized * 2))
                    g = 255
                    b = 0

                return f'rgb({r},{g},{b})'

            # Get all unique days to ensure consistent x-axis
            all_days = sorted(
                data_agrupados['dias_hasta_vencimiento'].unique())

            # Process each unique combination in the correct order (already sorted by get_documentos_agrupados_por_dias)
            for _, row in data_agrupados.iterrows():
                cliente_display = row['cliente_completo'][:100] + "..." if len(
                    row['cliente_completo']) > 100 else row['cliente_completo']

                # Create hover info
                docs_info = f"Documentos: {row['documentos_lista']}<br>{row['num_documentos']} doc(s)<br>{format_currency_int(row['sin_vencer'])}"

                # Show text for larger values
                text_display = format_currency_int(
                    row['sin_vencer']) if row['sin_vencer'] > 50000 else ""

                # Create arrays for all days (fill with 0 for missing days)
                x_values = all_days
                y_values = []
                colors = []
                hover_data = []
                text_data = []

                for day in all_days:
                    if day == row['dias_hasta_vencimiento']:
                        y_values.append(row['sin_vencer'])
                        colors.append(get_urgency_color(
                            row['dias_hasta_vencimiento']))
                        hover_data.append(docs_info)
                        text_data.append(text_display)
                    else:
                        y_values.append(0)
                        # Transparent for zero values
                        colors.append('rgba(0,0,0,0)')
                        hover_data.append("")
                        text_data.append("")

                # Add bar trace for this client-day combination
                fig.add_trace(go.Bar(
                    x=x_values,
                    y=y_values,
                    name=cliente_display,
                    marker=dict(
                        color=colors,
                        line=dict(color='white', width=1),
                        opacity=0.6
                    ),
                    hovertemplate="<b>%{fullData.name}</b><br>" +
                    "Días hasta vencimiento: %{x}<br>" +
                    "%{customdata}<br>" +
                    "<extra></extra>",
                    customdata=hover_data,
                    text=text_data,
                    textposition='inside',
                    textfont=dict(size=9, color='white', family='Inter'),
                    showlegend=False
                ))

            fig.update_layout(
                title="",
                xaxis_title="Días para vencimiento",
                yaxis_title="Valor ($)",
                barmode='stack',
                height=450,
                plot_bgcolor=theme_styles['plot_bg'],
                paper_bgcolor=theme_styles['plot_bg'],
                font=dict(family="Inter", size=12,
                          color=theme_styles['text_color']),
                xaxis=dict(
                    showgrid=True,
                    gridcolor=theme_styles['grid_color'],
                    linecolor=theme_styles['line_color'],
                    dtick=1,  # Show every day on x-axis
                    type='linear',  # Ensure linear spacing
                    title=dict(
                        font=dict(size=14, color=theme_styles['text_color']))
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor=theme_styles['grid_color'],
                    linecolor=theme_styles['line_color'],
                    tickformat='$,.0f'
                ),
                margin=dict(t=40, b=60, l=80, r=40)
            )

            # Add urgency indicator annotation
            fig.add_annotation(
                text="🔴 Más Urgente ← → Menos Urgente 🟢",
                xref="paper", yref="paper",
                x=0.5, y=1.02,
                xanchor='center', yanchor='bottom',
                showarrow=False,
                font=dict(
                    size=11, color=theme_styles['text_color'], family='Inter'),
                bgcolor=theme_styles['paper_color'],
                bordercolor=theme_styles['line_color'],
                borderwidth=1
            )

        # Detailed table grouped by customer
        if data_documentos_table.empty:
            tabla = html.Div([
                html.P("No hay documentos próximos a vencer en este período.",
                       style={'textAlign': 'center', 'color': 'gray', 'fontSize': '16px', 'fontFamily': 'Inter'})
            ])
        else:
            # Group by customer
            clientes_grupos = []
            current_cliente = None

            for _, row in data_documentos_table.iterrows():
                if current_cliente != row['cliente_completo']:
                    current_cliente = row['cliente_completo']
                    # Add customer header with urgency color - FIXED: Red only for 1 day or less
                    urgency_color = '#e74c3c' if row['dias_hasta_vencimiento'] <= 1 else '#f39c12' if row[
                        'dias_hasta_vencimiento'] <= 7 else '#27ae60'
                    clientes_grupos.append(
                        html.Div([
                            html.H5(current_cliente,
                                    style={'backgroundColor': urgency_color, 'color': 'white',
                                           'padding': '10px', 'margin': '10px 0 0 0', 'borderRadius': '5px',
                                           'fontFamily': 'Inter'})
                        ])
                    )

                # Add document with urgency indicator - FIXED: Red only for 1 day or less
                urgency_emoji = "🔴" if row['dias_hasta_vencimiento'] <= 1 else "🟡" if row['dias_hasta_vencimiento'] <= 7 else "🟢"
                clientes_grupos.append(
                    html.Div([
                        html.Div([
                            html.Span(f"{urgency_emoji} Documento: {row['documento_id']}",
                                      style={'fontWeight': 'bold', 'marginRight': '20px', 'fontFamily': 'Inter'}),
                            html.Span(f"Valor: {format_currency_int(row['sin_vencer'])}",
                                      style={'color': '#27AE60', 'marginRight': '20px', 'fontFamily': 'Inter'}),
                            html.Span(f"Vence en: {int(row['dias_hasta_vencimiento'])} días",
                                      style={'color': '#E74C3C', 'fontFamily': 'Inter'}),
                            html.Span(f"Fecha: {row['vencimiento'].strftime('%Y-%m-%d')}",
                                      style={'color': '#7F8C8D', 'marginLeft': '20px', 'fontFamily': 'Inter'})
                        ], style={'padding': '8px 15px', 'backgroundColor': theme_styles['paper_color'] if theme == 'dark' else '#F8F9FA',
                                  'margin': '2px 0', 'borderRadius': '3px', 'borderLeft': '3px solid #3498DB',
                                  'color': theme_styles['text_color']})
                    ])
                )

            tabla = html.Div([
                html.Div(clientes_grupos,
                         style={'maxHeight': '500px', 'overflowY': 'auto', 'border': f'1px solid {theme_styles["line_color"]}',
                                'borderRadius': '5px', 'padding': '10px', 'backgroundColor': theme_styles['paper_color']})
            ])

        return fig, tabla
    except Exception as e:
        print(f"Error en update_proximos_vencer: {e}")
        return go.Figure(), html.Div([html.P("Error al cargar datos")])

import time
from datetime import datetime

import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from analyzers import TransferenciasAnalyzer
from utils import format_currency_int, get_theme_styles


analyzer = TransferenciasAnalyzer()

# Carga inicial opcional (se recarga on-demand)
try:
    df = analyzer.load_data_from_firebase()
except Exception as e:
    print(
        f"⚠️ [transferenciasPage] Carga inicial falló (se recargará on-demand): {e}")
    df = pd.DataFrame()


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
            return dropdown_value if dropdown_value else 'Todos'
        else:
            return get_user_vendor_filter(session_data)
    except Exception as e:
        print(f"Error en get_selected_vendor: {e}")
        return 'Todos'


layout = html.Div([
    # Store for theme
    dcc.Store(id='transferencias-theme-store', data='light'),
    dcc.Store(id='transferencias-data-store', data={'last_update': 0}),

    # Notification area
    html.Div(id='transferencias-notification-area', children=[], style={
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
                id='transferencias-titulo-dashboard',
                children="Dashboard de Transferencias",
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
                html.Label("Transferencista:", style={
                    'fontWeight': 'bold',
                    'marginBottom': '8px',
                    'fontFamily': 'Inter',
                    'fontSize': '14px'
                }, id='transferencias-dropdown-vendedor-label'),
                dcc.Dropdown(
                    id='transferencias-dropdown-vendedor',
                    options=[{'label': v, 'value': v}
                             for v in analyzer.vendedores_list],
                    value='Todos',
                    style={'fontFamily': 'Inter'},
                    className='custom-dropdown'
                )
            ], style={
                'flex': '0 0 40%'
            }, id='transferencias-dropdown-vendedor-container'),

            # Dropdown de mes
            html.Div([
                html.Label("Mes:", style={
                    'fontWeight': 'bold',
                    'marginBottom': '8px',
                    'fontFamily': 'Inter',
                    'fontSize': '14px'
                }),
                dcc.Dropdown(
                    id='transferencias-dropdown-mes',
                    options=[{'label': m, 'value': m}
                             for m in analyzer.meses_list],
                    value='Todos',
                    style={'fontFamily': 'Inter'},
                    className='custom-dropdown'
                )
            ], style={
                'flex': '0 0 25%',
                'marginLeft': '2%'
            }),

            # Espacio flexible para empujar el botón a la derecha
            html.Div(style={'flex': '1'}),

            # Botón de tema alineado correctamente
            html.Div([
                html.Button(
                    html.Div([
                        html.Span('🌙', id='transferencias-theme-icon',
                                  style={'fontSize': '18px'}),
                        html.Span('Oscuro', id='transferencias-theme-text', style={
                            'marginLeft': '8px',
                            'fontSize': '13px',
                            'fontWeight': '500'
                        })
                    ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}),
                    id='transferencias-theme-toggle',
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
    ], style={'marginBottom': '35px', 'padding': '25px'}, id='transferencias-header-container'),

    # Cards de resumen - 8 cards en 2 filas
    html.Div([
        # Primera fila de cards
        html.Div([
            html.Div([
                html.H3("Ventas Totales", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}, id='transferencias-card-1-title'),
                html.H2(id='transferencias-transferencias-totales', children="$0", style={'color': '#2ecc71',
                        'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='transferencias-card-1'),

            html.Div([
                html.H3("Ventas Netas", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}, id='transferencias-card-2-title'),
                html.H2(id='transferencias-transferencias-netas', children="$0", style={'color': '#2ecc71',
                        'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='transferencias-card-2'),

            html.Div([
                html.H3("Devoluciones", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}, id='transferencias-card-3-title'),
                html.H2(id='transferencias-total-devoluciones', children="$0", style={
                        'color': '#e74c3c', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='transferencias-card-3'),

            html.Div([
                html.H3("Descuentos", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}, id='transferencias-card-4-title'),
                html.H2(id='transferencias-total-descuentos', children="$0", style={
                        'color': '#f39c12', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='transferencias-card-4'),

        ], style={'marginBottom': '15px'}),

        # Segunda fila de cards
        html.Div([
            html.Div([
                html.H3("Valor Promedio", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}, id='transferencias-card-5-title'),
                html.H2(id='transferencias-valor-promedio', children="$0", style={
                        'color': '#9b59b6', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='transferencias-card-5'),

            html.Div([
                html.H3("# Facturas", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}, id='transferencias-card-6-title'),
                html.H2(id='transferencias-num-facturas', children="0", style={'color': '#3498db',
                        'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='transferencias-card-6'),

            html.Div([
                html.H3("# Devoluciones", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}, id='transferencias-card-7-title'),
                html.H2(id='transferencias-num-devoluciones', children="0", style={
                        'color': '#c0392b', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='transferencias-card-7'),

            html.Div([
                html.H3("Clientes", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Inter'}, id='transferencias-card-8-title'),
                html.H2(id='transferencias-num-clientes', children="0", style={'color': '#e67e22',
                        'fontSize': '20px', 'margin': '0', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='transferencias-card-8'),
        ])
    ], style={'marginBottom': '30px', 'marginLeft': '70px'}),

    # Fila 1: Evolución Mensual y Análisis de Estacionalidad
    html.Div([
        html.Div([
            html.H3("Evolución de Ventas por Mes", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
            dcc.Graph(id='transferencias-grafico-transferencias-mes')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'}),

        html.Div([
            html.H3("Estacionalidad por Día de la Semana", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
            dcc.Graph(id='transferencias-grafico-estacionalidad')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'})
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'}, id='transferencias-row1-container'),

    # Fila 1.5: Evolución de transferencias por Cliente Específico
    html.Div([
        html.H3("Evolución Diaria de Ventas por Cliente", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
        html.Div([
            html.Label("Seleccionar Cliente:", style={
                       'fontWeight': 'bold', 'marginBottom': '10px', 'fontFamily': 'Inter'}),
            dcc.Dropdown(
                id='transferencias-dropdown-cliente',
                options=[{'label': 'Seleccione un cliente',
                          'value': 'Seleccione un cliente'}],
                value='Seleccione un cliente',
                style={'fontFamily': 'Inter', 'marginBottom': '20px'},
                className='custom-dropdown'
            )
        ]),
        dcc.Graph(id='transferencias-grafico-evolucion-cliente')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0px'}, id='transferencias-row1-5-container'),

    # Fila 2: Distribución por Zona y Forma de Pago
    html.Div([
        html.Div([
            html.H3("Ventas por Zona", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
            dcc.Graph(id='transferencias-grafico-zona')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'}),

        html.Div([
            html.H3("Distribución por Forma de Pago", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
            dcc.Graph(id='transferencias-grafico-forma-pago')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'})
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'}, id='transferencias-row2-container'),

    # Fila 2.5: transferencias Acumuladas por Cliente (Treemap solo)
    html.Div([
        html.H3("Ventas Acumuladas por Cliente", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
        html.P("(Acumulado hasta el mes seleccionado)", style={
               'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '12px', 'margin': '0 0 20px 0'}),
        dcc.Graph(id='transferencias-treemap-acumuladas')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'}, id='transferencias-row2-5-container'),

    # Fila 3: Treemap de transferencias por Cliente del Período (Treemap solo)
    html.Div([
        html.H3("Mapa de Ventas por Cliente (Período Seleccionado)", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
        dcc.Graph(id='transferencias-treemap-transferencias')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'}, id='transferencias-row3-container'),

    html.Div([
        html.H3("Clientes por Días Sin Venta", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
        html.P("(Clientes que no han comprado en 7+ días - Tamaño por total de ventas históricas)", style={
               'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '12px', 'margin': '0 0 20px 0'}),
        dcc.Graph(id='transferencias-treemap-dias-sin-venta')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'}, id='transferencias-row-nueva-treemap'),

    # Fila 4: Top Clientes y Clientes Impactados
    html.Div([
        html.H3("Top 10 - Clientes", style={'textAlign': 'center',
                'marginBottom': '20px', 'fontFamily': 'Inter'}),
        dcc.Graph(id='transferencias-top-clientes')
    ], style={'width': '100%', 'display': 'inline-block', 'margin': '1%'}),

    # Botón actualizar MEJORADO
    html.Div([
        html.Button([
            html.Span("🔄", style={'marginRight': '8px'}),
            'Actualizar Datos'
        ], id='transferencias-btn-actualizar', n_clicks=0,
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

], style={'fontFamily': 'Inter', 'backgroundColor': '#f5f5f5', 'padding': '20px'}, id='transferencias-main-container')


@callback(
    Output('transferencias-data-store', 'data'),
    [Input('transferencias-btn-actualizar', 'n_clicks')],
    prevent_initial_call=True
)
def update_transferencias_data(n_clicks):
    """
    Callback central para recargar TODOS los datos cuando se presiona actualizar.
    """
    if n_clicks > 0:
        try:
            start_time = time.time()

            # ¡CLAVE! Usar reload_data() para forzar recarga completa
            result = analyzer.reload_data()

            load_time = time.time() - start_time

            # Debugging info
            if hasattr(analyzer, 'print_data_summary'):
                analyzer.print_data_summary()

            return {
                'last_update': n_clicks,
                'timestamp': datetime.now().isoformat(),
                'success': True,
                'load_time': load_time,
                'records_count': len(result)
            }

        except Exception as e:
            print(
                f"❌ [transferenciasPage] Error en actualización #{n_clicks}: {e}")
            return {
                'last_update': n_clicks,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'success': False
            }

    return dash.no_update


@callback(
    Output('transferencias-notification-area', 'children'),
    [Input('transferencias-data-store', 'data')],
    prevent_initial_call=True
)
def show_update_notification(data_store):
    """
    Mostrar notificación cuando se actualicen los datos.
    """
    if data_store and data_store.get('last_update', 0) > 0:
        if data_store.get('error'):
            # Notificación de error
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
                }, id='transferencias-success-notification')
            ])

    return []


@callback(
    [Output('transferencias-btn-actualizar', 'children'),
     Output('transferencias-btn-actualizar', 'disabled')],
    [Input('transferencias-data-store', 'data')],
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
    [Output('transferencias-card-1-title', 'style'),
     Output('transferencias-card-2-title', 'style'),
     Output('transferencias-card-3-title', 'style'),
     Output('transferencias-card-4-title', 'style'),
     Output('transferencias-card-5-title', 'style'),
     Output('transferencias-card-6-title', 'style'),
     Output('transferencias-card-7-title', 'style'),
     Output('transferencias-card-8-title', 'style')],
    [Input('transferencias-theme-store', 'data')]
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
    [Output('transferencias-transferencias-totales', 'children'),
     Output('transferencias-transferencias-netas', 'children'),
     Output('transferencias-total-devoluciones', 'children'),
     Output('transferencias-total-descuentos', 'children'),
     Output('transferencias-valor-promedio', 'children'),
     Output('transferencias-num-facturas', 'children'),
     Output('transferencias-num-devoluciones', 'children'),
     Output('transferencias-num-clientes', 'children')],
    [Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-dropdown-mes', 'value'),
     Input('transferencias-data-store', 'data')]  # ¡NUEVO!
)
def update_cards(session_data, dropdown_value, mes, data_store):
    """
    Update summary cards with sales statistics.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        resumen = analyzer.get_resumen_transferencias(vendedor, mes)

        return (
            format_currency_int(resumen['total_transferencias']),
            format_currency_int(resumen['transferencias_netas']),
            format_currency_int(resumen['total_devoluciones']),
            format_currency_int(resumen['total_descuentos']),
            format_currency_int(resumen['ticket_promedio']),
            f"{resumen['num_facturas']:,}",
            f"{resumen['num_devoluciones']:,}",
            f"{resumen['num_clientes']:,}",
        )
    except Exception as e:
        print(f"❌ [update_cards] Error: {e}")
        return "$0", "$0", "$0", "$0", "$0", "0", "0", "0"


@callback(
    Output('transferencias-grafico-transferencias-mes', 'figure'),
    [Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-data-store', 'data'),  # ¡NUEVO!
     Input('transferencias-theme-store', 'data')]
)
def update_transferencias_mes(session_data, dropdown_value, data_store, theme):
    """
    Update monthly sales evolution chart with area fill and smooth lines.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_transferencias_por_mes(vendedor)
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
            name='transferencias',
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
            hovertemplate="<b>%{x}</b><br>transferencias: %{customdata}<br>Facturas: %{text}<extra></extra>",
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
                title="transferencias ($)",
                tickfont=dict(color=theme_styles['text_color']),
                linecolor=theme_styles['line_color']
            ),
            showlegend=False,
            margin=dict(t=20, b=80, l=80, r=20),
            hovermode='x unified'
        )

        return fig
    except Exception as e:
        print(f"❌ [update_transferencias_mes] Error: {e}")
        return go.Figure()


@callback(
    Output('transferencias-grafico-estacionalidad', 'figure'),
    [Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-dropdown-mes', 'value'),
     Input('transferencias-data-store', 'data'),  # ¡NUEVO!
     Input('transferencias-theme-store', 'data')]
)
def update_estacionalidad(session_data, dropdown_value, mes, data_store, theme):
    """
    Update seasonality chart by day of week with pastel colors and transparency.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_transferencias_por_dia_semana(vendedor, mes)
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
                         "transferencias: %{customdata[0]}<br>" +
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
                title="transferencias ($)"
            ),
            showlegend=False,
            margin=dict(t=20, b=60, l=80, r=20)
        )

        return fig
    except Exception as e:
        print(f"❌ [update_estacionalidad] Error: {e}")
        return go.Figure()


@callback(
    Output('transferencias-grafico-zona', 'figure'),
    [Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-dropdown-mes', 'value'),
     Input('transferencias-data-store', 'data'),  # ¡NUEVO!
     Input('transferencias-theme-store', 'data')]
)
def update_zona(session_data, dropdown_value, mes, data_store, theme):
    """
    Update sales by zone chart with red-to-green color scale and transparency.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_transferencias_por_zona(vendedor, mes)
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
            hovertemplate="<b>%{x}</b><br>transferencias: %{customdata[0]}<br>Clientes: %{customdata[1]}<extra></extra>",
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
        print(f"❌ [update_zona] Error: {e}")
        return go.Figure()


@callback(
    Output('transferencias-grafico-forma-pago', 'figure'),
    [Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-dropdown-mes', 'value'),
     Input('transferencias-data-store', 'data'),  # ¡NUEVO!
     Input('transferencias-theme-store', 'data')]
)
def update_forma_pago(session_data, dropdown_value, mes, data_store, theme):
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
            hovertemplate="<b>%{label}</b><br>transferencias: %{customdata}<br>Porcentaje: %{percent}<extra></extra>",
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
        print(f"❌ [update_forma_pago] Error: {e}")
        return go.Figure()


@callback(
    Output('transferencias-treemap-transferencias', 'figure'),
    [Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-dropdown-mes', 'value'),
     Input('transferencias-data-store', 'data'),  # ¡NUEVO!
     Input('transferencias-theme-store', 'data')]
)
def update_treemap(session_data, dropdown_value, mes, data_store, theme):
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
            hovertemplate="<b>%{label}</b><br>transferencias: %{customdata}<br><extra></extra>",
            customdata=[format_currency_int(val)
                        for val in data['valor_neto']],
            marker=dict(
                colorscale='Bluyl',
                line=dict(width=2, color='white')),
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
        print(f"❌ [update_treemap] Error: {e}")
        return go.Figure()


@callback(
    Output('transferencias-treemap-acumuladas', 'figure'),
    [Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-dropdown-mes', 'value'),
     Input('transferencias-data-store', 'data'),  # ¡NUEVO!
     Input('transferencias-theme-store', 'data')]
)
def update_treemap_acumuladas(session_data, dropdown_value, mes, data_store, theme):
    """
    Update accumulated sales treemap.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_transferencias_acumuladas_mes(mes, vendedor)
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
            hovertemplate="<b>%{label}</b><br>transferencias Acumuladas: %{customdata}<br>Facturas: %{text}<extra></extra>",
            customdata=[format_currency_int(val)
                        for val in data['valor_neto']],
            text=data['documento_id'],
            marker=dict(
                colorscale='Bluyl',
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
        print(f"❌ [update_treemap_acumuladas] Error: {e}")
        return go.Figure()


@callback(
    Output('transferencias-treemap-dias-sin-venta', 'figure'),
    [Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-data-store', 'data'),  # ¡NUEVO!
     Input('transferencias-theme-store', 'data')]
)
def update_treemap_dias_sin_venta(session_data, dropdown_value, data_store, theme):
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
                text="No hay clientes sin transferencias recientes",
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
            texttemplate="<b>%{label}</b><br>transferencias: %{customdata}",
            hovertemplate="<b>%{text}</b><br>" +
                         # %{value} now shows days
                         "Días sin venta: %{value}<br>" +
                         "transferencias históricas: %{customdata[0]}<br>" +
                         "Última venta: %{customdata[1]}<br>" +
                         "<extra></extra>",
            text=[cliente[:80] + "..." if len(cliente) > 80 else cliente
                  for cliente in data['cliente_completo']],
            customdata=[[format_currency_int(transferencias), fecha_str]
                        for transferencias, fecha_str in zip(
                data['valor_neto'],
                fechas_formatted)],
            marker=dict(
                colors=data['dias_sin_venta'],  # Color by days without sales
                colorscale='RdYlBu_r',
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
        print(f"❌ [update_treemap_dias_sin_venta] Error: {e}")
        return go.Figure()


@callback(
    Output('transferencias-grafico-evolucion-cliente', 'figure'),
    [Input('transferencias-dropdown-cliente', 'value'),
     Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-dropdown-mes', 'value'),
     Input('transferencias-data-store', 'data'),  # ¡NUEVO!
     Input('transferencias-theme-store', 'data')]
)
def update_evolucion_cliente(cliente, session_data, dropdown_value, mes, data_store, theme):
    """
    Update client evolution chart - filtered by month using main DataFrame.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        theme_styles = get_theme_styles(theme)

        if cliente == 'Seleccione un cliente':
            fig = go.Figure()
            fig.add_annotation(
                text="Seleccione un cliente para ver su evolución diaria de transferencias",
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

        # Get client evolution data using analyzer method
        data = analyzer.get_evolucion_cliente(cliente, vendedor)

        # Apply month filter if specified
        if mes and mes != 'Todos' and not data.empty:
            try:
                # Assuming data has 'fecha_str' in YYYY-MM-DD format
                data = data[data['fecha_str'].str.startswith(mes)]
            except:
                pass  # If filtering fails, use all data

        if data.empty:
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

        # Calculate totals for title
        total_transferencias_periodo = data['valor_neto'].sum()
        num_dias = len(data)

        # Create bar chart
        fig = go.Figure()

        pastel_colors = [
            'rgba(144, 238, 144, 0.8)', 'rgba(173, 216, 230, 0.8)',
            'rgba(255, 218, 185, 0.8)', 'rgba(221, 160, 221, 0.8)',
            'rgba(175, 238, 238, 0.8)', 'rgba(255, 182, 193, 0.8)'
        ]

        bar_colors = [
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
                         "transferencias: %{customdata[0]}<br>" +
                         "Facturas: %{customdata[1]}<br>" +
                         "<extra></extra>",
            customdata=[[format_currency_int(val), facturas] for val, facturas in zip(
                data['valor_neto'], data['documento_id'])]
        ))

        # Título con información específica del período
        cliente_corto = cliente[:80] + '...' if len(cliente) > 80 else cliente

        if mes != 'Todos':
            titulo_completo = f"Total: {format_currency_int(total_transferencias_periodo)} ({num_dias} días)<br><sub>{cliente_corto} - {mes}</sub>"
        else:
            titulo_completo = f"Total: {format_currency_int(total_transferencias_periodo)} ({num_dias} días)<br><sub>{cliente_corto}</sub>"

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
                title="transferencias ($)",
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
        print(f"❌ [update_evolucion_cliente] Error: {e}")
        return go.Figure()


@callback(
    Output('transferencias-top-clientes', 'figure'),
    [Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-dropdown-mes', 'value'),
     Input('transferencias-data-store', 'data'),  # ¡NUEVO!
     Input('transferencias-theme-store', 'data')]
)
def update_top_clientes(session_data, dropdown_value, mes, data_store, theme):
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
                name[:100] + "..." if len(name) > 100 else name for name in data_sorted['cliente_completo']],
            textposition='inside',
            textfont=dict(color='white', size=10),
            hovertemplate="<b>%{customdata[0]}</b><br>transferencias: %{customdata[1]}<br>Facturas: %{customdata[2]}<extra></extra>",
            customdata=[[cliente, format_currency_int(transferencias), facturas] for cliente, transferencias, facturas in zip(
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
            xaxis_title="Ventas",
            showlegend=False,
            margin=dict(t=20, b=40, l=80, r=80)
        )

        return fig
    except Exception as e:
        print(f"❌ [update_top_clientes] Error: {e}")
        return go.Figure()


@callback(
    Output('transferencias-dropdown-cliente', 'options'),
    [Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-data-store', 'data')]  # ¡NUEVO!
)
def update_clientes_dropdown(session_data, dropdown_value, data_store):
    """
    Update client dropdown based on selected salesperson.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        clientes = analyzer.get_clientes_list(vendedor)
        return [{'label': cliente, 'value': cliente} for cliente in clientes]
    except Exception as e:
        print(f"❌ [update_clientes_dropdown] Error: {e}")
        return [{'label': 'Seleccione un cliente', 'value': 'Seleccione un cliente'}]


@callback(
    Output('transferencias-dropdown-cliente', 'value'),
    [Input('transferencias-dropdown-vendedor', 'value')]
)
def reset_cliente_selection(vendedor):
    """
    Reset client selection when salesperson changes.
    """
    return 'Seleccione un cliente'


@callback(
    [Output('transferencias-dropdown-vendedor-container', 'style'),
     Output('transferencias-dropdown-vendedor-label', 'style')],
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
            # Mostrar para administradores con más ancho
            base_style = {
                'flex': '0 0 45%',  # Cambiado a flexbox
                'marginRight': '3%'
            }
            label_style = {
                'fontWeight': 'bold',
                'marginBottom': '8px',
                'fontFamily': 'Inter',
                'fontSize': '14px'
            }
            return base_style, label_style
    except Exception as e:
        print(f"❌ [update_dropdown_visibility] Error: {e}")
        return {'display': 'none'}, {'display': 'none'}


@callback(
    Output('transferencias-titulo-dashboard', 'children'),
    [Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-dropdown-mes', 'value')]
)
def update_title(session_data, dropdown_value, mes):
    """
    Update dashboard title based on filters.
    """
    from utils import can_see_all_vendors, get_user_vendor_filter

    try:
        if not session_data:
            return "Dashboard de Transferencias"

        if can_see_all_vendors(session_data):
            vendedor = dropdown_value if dropdown_value else 'Todos'
            title = "Dashboard de Transferencias"
            if vendedor != 'Todos' and mes != 'Todos':
                title += f" - {vendedor} - {mes}"
            elif vendedor != 'Todos':
                title += f" - {vendedor}"
            elif mes != 'Todos':
                title += f" - {mes}"
            else:
                title += " - Todos los Transferencistas"
            return title
        else:
            vendor = get_user_vendor_filter(session_data)
            title = f"Dashboard de Transferencias - {vendor}"
            if mes != 'Todos':
                title += f" - {mes}"
            return title
    except Exception as e:
        print(f"❌ [update_title] Error: {e}")
        return "Dashboard de Transferencias"


@callback(
    [Output('transferencias-theme-store', 'data'),
     Output('transferencias-theme-icon', 'children'),
     Output('transferencias-theme-text', 'children'),
     Output('transferencias-theme-toggle', 'style'),
     Output('transferencias-main-container', 'style'),
     Output('transferencias-header-container', 'style'),
     Output('transferencias-titulo-dashboard', 'style')],
    [Input('transferencias-theme-toggle', 'n_clicks')],
    [State('transferencias-theme-store', 'data')]
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
    [Output('transferencias-dropdown-vendedor', 'style'),
     Output('transferencias-dropdown-mes', 'style'),
     Output('transferencias-dropdown-cliente', 'style'),
     Output('transferencias-dropdown-vendedor', 'className'),
     Output('transferencias-dropdown-mes', 'className'),
     Output('transferencias-dropdown-cliente', 'className')],
    [Input('transferencias-theme-store', 'data'),
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

    return vendedor_style, dropdown_style, dropdown_style, css_class, css_class, css_class


@callback(
    [Output('transferencias-card-1', 'style'),
     Output('transferencias-card-2', 'style'),
     Output('transferencias-card-3', 'style'),
     Output('transferencias-card-4', 'style'),
     Output('transferencias-card-5', 'style'),
     Output('transferencias-card-6', 'style'),
     Output('transferencias-card-7', 'style'),
     Output('transferencias-card-8', 'style')],
    [Input('transferencias-theme-store', 'data')]
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


@callback(
    [Output('transferencias-row1-container', 'style'),
     Output('transferencias-row1-5-container', 'style'),
     Output('transferencias-row-nueva-treemap', 'style'),
     Output('transferencias-row2-container', 'style'),
     Output('transferencias-row2-5-container', 'style'),
     Output('transferencias-row3-container', 'style')],
    [Input('transferencias-theme-store', 'data')]
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

    return [chart_style] * 6

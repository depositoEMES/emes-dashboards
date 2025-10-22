import time
import pandas as pd
from datetime import datetime

import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.express as px
import plotly.graph_objects as go

from components import (
    create_metrics_grid,
    create_empty_metrics,
    METRIC_COLORS,
)
from analyzers import CarteraAnalyzer
from utils import (
    format_currency_int,
    get_theme_styles,
    get_dropdown_style
)

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


layout = html.Div([
    # Store for theme
    dcc.Store(id='cartera-theme-store', data='light'),
    dcc.Store(id='cartera-data-store', data={'last_update': 0}),
    dcc.Store(id='cartera-filtros-tabla-store', data={
        'vencida': True,
        'vence_hoy': True,
        'proximos': True,
        'sin_vencer': True
    }),

    # Notification area
    html.Div(id='cartera-notification-area', children=[], style={
        'position': 'fixed',
        'top': '20px',
        'right': '20px',
        'zIndex': '1000',
        'maxWidth': '300px'
    }),

    html.Div([
        html.Div([
            html.Div([
                html.Img(
                    src='/assets/logo.png',
                    className="top-left-logo",
                    alt="Logo de la empresa",
                    style={
                        'maxWidth': '160px',
                        'height': 'auto',
                        'filter': 'drop-shadow(0 8px 16px rgba(30, 58, 138, 0.3))',
                        'transition': 'all 0.3s ease'
                    }
                )
            ], className="logo-left-container", style={
                'display': 'flex',
                'alignItems': 'center'
            }),

            html.Div([
                html.H1(
                    id='cartera-titulo-principal',
                    children="Cartera",
                    className="main-title"
                ),
                html.P(
                    id='cartera-subtitulo',
                    children="Gestión y análisis de cartera de clientes",
                    className="main-subtitle",
                )
            ], className="center-title-section", style={
                'flex': '1',
                'display': 'flex',
                'flexDirection': 'column',
                'justifyContent': 'center',
                'alignItems': 'center'
            }),

            html.Div([
                html.Button(
                    "🌙",
                    id="cartera-theme-toggle",
                    title="Cambiar tema",
                    n_clicks=0,
                    style={
                        'background': 'transparent',
                        'border': '2px solid rgba(255, 255, 255, 0.3)',
                        'borderRadius': '50%',
                        'width': '44px',
                        'height': '44px',
                        'fontSize': '18px',
                        'cursor': 'pointer',
                        'transition': 'all 0.3s ease',
                        'display': 'flex',
                        'alignItems': 'center',
                        'justifyContent': 'center'
                    }
                )
            ], className="logout-right-container", style={
                'display': 'flex',
                'alignItems': 'center'
            })
        ], className="top-header", id='cartera-header-container', style={
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'space-between',
            'borderRadius': '20px',
            'padding': '32px 40px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'position': 'relative',
            'minHeight': '120px'
        }),

        html.Div([
            html.Div([
                html.Label("Vendedor:",
                           id='cartera-dropdown-vendedor-label',
                           style={
                               'fontWeight': '600',
                               'fontSize': '14px',
                               'marginBottom': '8px',
                               'display': 'block'
                           }),
                dcc.Dropdown(
                    id='cartera-dropdown-vendedor',
                    options=[{'label': v, 'value': v}
                             for v in analyzer.vendedores_list],
                    value='Todos',
                    placeholder="Seleccionar vendedor...",
                    clearable=True,
                    style={
                        'height': '44px',
                        'borderRadius': '12px',
                        'fontSize': '14px'
                    }
                )
            ], style={
                'display': 'flex',
                'flexDirection': 'column',
                'flex': '1',
                'minWidth': '250px'
            }, id='cartera-dropdown-vendedor-container'),

            html.Div([
                html.Button(
                    "🔄 Actualizar Datos",
                    id="cartera-btn-actualizar",
                    n_clicks=0,
                    style={
                        'background': 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
                        'color': '#ffffff',
                        'border': 'none',
                        'padding': '12px 24px',
                        'borderRadius': '25px',
                        'fontWeight': '600',
                        'fontSize': '14px',
                        'cursor': 'pointer',
                        'boxShadow': '0 4px 12px rgba(59, 130, 246, 0.3)',
                        'transition': 'all 0.3s ease',
                        'height': '44px',
                        'minWidth': '160px'
                    }
                )
            ], style={
                'display': 'flex',
                'alignItems': 'flex-end',
                'justifyContent': 'flex-end'
            })
        ], id='cartera-controls-container', style={
            'display': 'flex',
            'gap': '24px',
            'alignItems': 'stretch',
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'flexWrap': 'wrap'
        }),

        html.Div(id="cartera-metrics-cards", children=[],
                 style={'marginBottom': '24px'}),

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
        ], id='cartera-row1-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

        # Fila 2: Distribución de Cartera por Cliente
        html.Div([
            html.H3("Distribución de Cartera por Cliente", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
            html.Div([
                html.Label("Filtrar por % de Cartera Vencida:", style={
                    'fontWeight': 'bold',
                    'marginBottom': '10px',
                    'fontFamily': 'Inter',
                    'fontSize': '14px'
                }),
                html.Div([
                    dcc.RangeSlider(
                        id='cartera-filtro-porcentaje-vencida',
                        min=0,
                        max=100,
                        step=10,
                        value=[0, 100],  # Por defecto muestra todos
                        marks={i: f'{i}%' for i in range(0, 101, 20)},
                        tooltip={"placement": "bottom",
                                 "always_visible": True},
                        allowCross=False
                    )
                ], style={'margin': '10px 0 20px 0'})
            ], style={
                'marginBottom': '20px',
                'padding': '15px',
                'borderRadius': '8px',
                'border': '1px solid #e5e7eb'
            }),
            dcc.Graph(id='cartera-treemap-unificado',
                      style={'height': '600px'})
        ], id='cartera-row2-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

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
                    className='modern-dropdown'
                )
            ], style={'marginBottom': '20px'}),

            # Contenedor para la tabla del cliente
            html.Div(id='cartera-tabla-cliente-detalle')

        ], id='cartera-cliente-detalle-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

        # Fila 3: Top 10
        html.Div([
            html.H3("Top 10 Clientes - Composición de Cartera", style={
                    'textAlign': 'center', 'marginBottom': '25px', 'fontFamily': 'Inter', 'fontSize': '24px'}),
            dcc.Graph(id='cartera-top-unificado', style={'height': '500px'})
        ], id='cartera-row3-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

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
        ], id='cartera-config-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

        # Fila 5: Gráfico de Vencimientos Próximos
        html.Div([
            html.H3("Documentos Próximos a Vencer", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
            dcc.Graph(id='cartera-grafico-proximos-vencer')
        ], id='cartera-row5-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

        # Fila 6: Tabla Detallada de Vencimientos
        html.Div([
            html.H3("Detalle de Documentos por Vencer", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
            html.Div(id='cartera-tabla-proximos-vencer')
        ], id='cartera-row6-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

        # Nueva sección: Indicador de Desempeño de Cartera
        html.Div([
            html.H3("Indicador de Desempeño de Cartera", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),

            # Contenedor para el indicador (tabla para admin, gráfico para vendedor)
            html.Div(id='cartera-indicador-container')

        ], id='cartera-indicador-section', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        })

    ], style={
        'margin': '0 auto',
        'padding': '0 40px',
    }),

], id='cartera-main-container', style={
    'width': '100%',
    'minHeight': '100vh',
    'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
    'transition': 'all 0.3s ease',
    'padding': '20px 0',
    'background': 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 25%, #f8fafc 50%, #f1f5f9 100%)',
    'backgroundSize': '400% 400%',
    'animation': 'gradientShift 15s ease infinite'
})


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
    Output('cartera-metrics-cards', 'children'),
    [Input('session-store', 'data'),
     Input('cartera-dropdown-vendedor', 'value'),
     Input('cartera-data-store', 'data'),
     Input('cartera-theme-store', 'data')]
)
def update_metric_cards(session_data, dropdown_value, data_store, theme):
    """
    Actualizar las metric cards con los datos de cartera
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        is_dark = theme == 'dark'

        # Obtener resumen de datos
        resumen = analyzer.get_resumen(vendedor)

        # Calcular porcentaje vencida
        porcentaje = (resumen['total_vencida'] / resumen['total_cartera']
                      * 100) if resumen['total_cartera'] != 0 else 0

        # Preparar datos para las cards
        metrics_data = [
            {
                'title': 'Cartera Total',
                'value': format_currency_int(resumen['total_cartera']),
                'color': METRIC_COLORS['primary'],
                'card_id': 'cartera-card-total-cartera'
            },
            {
                'title': 'Vencida',
                'value': format_currency_int(resumen['total_vencida']),
                'color': METRIC_COLORS['danger'],
                'card_id': 'cartera-card-total-vencida'
            },
            {
                'title': 'Sin Vencer',
                'value': format_currency_int(resumen['total_sin_vencer']),
                'color': METRIC_COLORS['success'],
                'card_id': 'cartera-card-total-sin-vencer'
            },
            {
                'title': 'Calidad Cartera',
                'value': f"{resumen['porcentaje_al_dia']:.1f}%",
                'color': METRIC_COLORS['purple'],
                'card_id': 'cartera-card-calidad-cartera'
            },
            {
                'title': 'Clientes',
                'value': f"{resumen['num_clientes']:,}",
                'color': METRIC_COLORS['indigo'],
                'card_id': 'cartera-card-total-clientes'
            },
            {
                'title': 'Clientes con Cartera Vencida',
                'value': f"{resumen['clientes_vencida']:,}",
                'color': METRIC_COLORS['orange'],
                'card_id': 'cartera-card-clientes-vencida'
            },
            {
                'title': 'Facturas',
                'value': f"{resumen['num_facturas']:,}",
                'color': METRIC_COLORS['teal'],
                'card_id': 'cartera-card-num-facturas'
            },
            {
                'title': '% Vencida',
                'value': f"{porcentaje:.1f}%",
                'color': METRIC_COLORS['warning'],
                'card_id': 'cartera-card-porcentaje-vencida'
            }
        ]

        # Crear grid de métricas con 4 columnas
        return create_metrics_grid(
            metrics=metrics_data,
            is_dark=is_dark,
            columns=4,
            gap="20px"
        )

    except Exception as e:
        print(f"❌ Error actualizando metric cards de cartera: {e}")
        # Retornar cards vacías en caso de error
        return create_empty_metrics(is_dark=theme == 'dark', count=8)


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
    [Output('cartera-dropdown-vendedor-container', 'style'),
     Output('cartera-dropdown-vendedor-label', 'style')],
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
                'display': 'flex',
                'flexDirection': 'column',
                'flex': '1',
                'minWidth': '250px'
            }
            label_style = {
                'fontWeight': '600',
                'fontSize': '14px',
                'marginBottom': '8px',
                'display': 'block'
            }
            return base_style, label_style
    except Exception as e:
        print(f"❌ [update_dropdown_visibility] Error: {e}")
        return {'display': 'none'}, {'display': 'none'}


@callback(
    Output('cartera-filtros-tabla-store', 'data'),
    [Input('cartera-filtro-vencida', 'n_clicks'),
     Input('cartera-filtro-vence-hoy', 'n_clicks'),
     Input('cartera-filtro-proximos', 'n_clicks'),
     Input('cartera-filtro-sin-vencer', 'n_clicks'),
     Input('cartera-filtro-todos', 'n_clicks')],
    [State('cartera-filtros-tabla-store', 'data')],
    prevent_initial_call=True
)
def update_filtros_tabla(vencida_clicks, vence_hoy_clicks, proximos_clicks,
                         sin_vencer_clicks, todos_clicks, current_filters):
    """
    Manejar clicks en los filtros de la tabla - Versión mejorada.
    """
    ctx = dash.callback_context

    if not ctx.triggered or not current_filters:
        return {
            'vencida': True,
            'vence_hoy': True,
            'proximos': True,
            'sin_vencer': True
        }

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    # print("BUTTON ID >>>>>>>>>>>>>>>: ", button_id)

    # Crear una copia profunda para evitar problemas de mutación
    import copy
    new_filters = copy.deepcopy(current_filters)

    if button_id == 'cartera-filtro-todos':
        all_selected = all(current_filters.values())
        new_state = not all_selected
        new_filters = \
            {
                'vencida': new_state,
                'vence_hoy': new_state,
                'proximos': new_state,
                'sin_vencer': new_state
            }
    elif button_id == 'cartera-filtro-vencida':
        new_filters['vencida'] = not new_filters.get('vencida', True)
    elif button_id == 'cartera-filtro-vence-hoy':
        new_filters['vence_hoy'] = not new_filters.get('vence_hoy', True)
    elif button_id == 'cartera-filtro-proximos':
        new_filters['proximos'] = not new_filters.get('proximos', True)
    elif button_id == 'cartera-filtro-sin-vencer':
        new_filters['sin_vencer'] = not new_filters.get('sin_vencer', True)

    return new_filters


@callback(
    [Output('cartera-theme-store', 'data'),
     Output('cartera-theme-toggle', 'children'),
     Output('cartera-main-container', 'style')],
    [Input('cartera-theme-toggle', 'n_clicks')],
    [State('cartera-theme-store', 'data')]
)
def toggle_theme(n_clicks, current_theme):
    """
    Toggle between light and dark theme.
    """
    if not n_clicks:
        # Tema claro por defecto
        return (
            'light',
            "🌙",
            {
                'width': '100%', 'minHeight': '100vh',
                'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
                'background': 'linear-gradient(135deg, #f9fafb 0%, #eff6ff 100%)',
                'color': '#111827', 'transition': 'all 0.3s ease', 'padding': '20px 0'
            }
        )

    is_dark = current_theme != 'dark'
    icon = "☀️" if is_dark else "🌙"
    new_theme = 'dark' if is_dark else 'light'

    if is_dark:
        # Estilos dark theme
        return (
            new_theme,
            icon,
            {
                'width': '100%', 'minHeight': '100vh',
                'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
                'background': 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)',
                'color': '#f8fafc', 'transition': 'all 0.3s ease', 'padding': '20px 0'
            }
        )
    else:
        # Estilos light theme
        return (
            new_theme,
            icon,
            {
                'width': '100%', 'minHeight': '100vh',
                'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
                'background': 'linear-gradient(135deg, #f9fafb 0%, #eff6ff 100%)',
                'color': '#111827', 'transition': 'all 0.3s ease', 'padding': '20px 0'
            }
        )


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
    Update styles for summary cards with glass effect.
    """
    base_card_style = {
        'padding': '20px',
        'borderRadius': '16px',
        'textAlign': 'center',
        'width': '20%',
        'display': 'inline-block',
        'margin': '1.5%',
        'transition': 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        'position': 'relative',
        'overflow': 'hidden'
    }

    if theme == 'dark':
        glass_style = {
            **base_card_style,
            'background': 'linear-gradient(135deg, rgba(0, 0, 0, 0.2), rgba(0, 0, 0, 0.1))',
            'backdropFilter': 'blur(20px)',
            'webkitBackdropFilter': 'blur(20px)',
            'border': '1px solid rgba(255, 255, 255, 0.1)',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.3)',
            'color': '#ffffff'
        }
    else:
        glass_style = {
            **base_card_style,
            'background': 'linear-gradient(135deg, rgba(255, 255, 255, 0.25), rgba(255, 255, 255, 0.1))',
            'backdropFilter': 'blur(20px)',
            'webkitBackdropFilter': 'blur(20px)',
            'border': '1px solid rgba(255, 255, 255, 0.2)',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'color': '#2c3e50'
        }

    return [glass_style] * 8


# Container styles callback
@callback(
    [Output('cartera-row1-container', 'style'),
     Output('cartera-row2-container', 'style'),
     Output('cartera-cliente-detalle-container', 'style'),
     Output('cartera-row3-container', 'style'),
     Output('cartera-config-container', 'style'),
     Output('cartera-row5-container', 'style'),
     Output('cartera-row6-container', 'style')],
    [Input('cartera-theme-store', 'data')]
)
def update_container_styles(theme):
    """
    Update styles for chart containers based on theme.
    """
    theme_styles = get_theme_styles(theme)

    # Estilo base para contenedores
    base_style = {
        'backgroundColor': theme_styles['paper_color'],
        'padding': '24px',
        'borderRadius': '16px',
        'boxShadow': theme_styles['card_shadow'],
        'marginBottom': '24px',
        'color': theme_styles['text_color'],
        'transition': 'all 0.3s ease',
        'width': '100%'
    }

    return [base_style] * 7


@callback(
    Output('cartera-titulo-principal', 'children'),
    [Input('session-store', 'data'),
     Input('cartera-dropdown-vendedor', 'value')]
)
def update_title(session_data, dropdown_value):
    """
    Update dashboard title based on filters.
    """
    from utils import can_see_all_vendors, get_user_vendor_filter

    try:
        if not session_data:
            return "Cartera"

        if can_see_all_vendors(session_data):
            vendedor = dropdown_value if dropdown_value else 'Todos'
            return "Cartera"
        else:
            vendor = get_user_vendor_filter(session_data)
            return "Cartera"
    except Exception as e:
        print(f"❌ [update_title] Error: {e}")
        return "Cartera"


@callback(
    Output('cartera-subtitulo', 'children'),
    [Input('session-store', 'data'),
     Input('cartera-dropdown-vendedor', 'value')]
)
def update_subtitle(session_data, dropdown_value):
    """
    Update dynamic subtitle based on filters.
    """
    from utils import can_see_all_vendors, get_user_vendor_filter

    try:
        if not session_data:
            return "Selecciona filtros para comenzar"

        if can_see_all_vendors(session_data):
            vendedor = dropdown_value if dropdown_value else 'Todos'
        else:
            vendedor = get_user_vendor_filter(session_data)

        # Construir subtítulo
        if vendedor and vendedor != 'Todos':
            return f"Análisis de cartera • {vendedor.title()}"
        else:
            return "Análisis de cartera • Todos los vendedores"

    except Exception as e:
        print(f"❌ [update_subtitle] Error: {e}")
        return "Gestión y análisis de cartera de clientes"


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


@callback(
    Output('cartera-tabla-cliente-detalle', 'children'),
    [Input('cartera-dropdown-cliente', 'value'),
     Input('session-store', 'data'),
     Input('cartera-dropdown-vendedor', 'value'),
     Input('cartera-theme-store', 'data'),
     Input('cartera-filtros-tabla-store', 'data')]
)
def update_cliente_detalle_table(cliente_seleccionado, session_data, dropdown_value, theme, filtros):
    """
    Update client detail table with unified current and overdue portfolio.
    MODIFICADO para manejar la vista "Todos" con columna de cliente.
    """
    try:
        if not cliente_seleccionado:
            return html.Div([
                html.P("Seleccione un cliente para ver el detalle de su cartera.",
                       style={'textAlign': 'center', 'color': 'gray', 'fontSize': '16px', 'fontFamily': 'Inter'})
            ])

        vendedor = get_selected_vendor(session_data, dropdown_value)
        theme_styles = get_theme_styles(theme)

        # Determinar si mostrar columna de cliente
        mostrar_cliente = (cliente_seleccionado == "Todos")

        if mostrar_cliente:
            # Para "Todos", obtener datos de todos los clientes
            detalle = analyzer.get_todos_clientes_detalle(vendedor)

            if not detalle['documentos'].empty:
                elementos = [
                    html.Div([
                        html.H4("Vista General - Todos los Clientes", style={
                            'backgroundColor': 'rgba(52, 152, 219, 0.4)',
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

                # Crear tabla unificada CON columna de cliente
                elementos.append(
                    crear_tabla_unificada(
                        detalle['documentos'],
                        theme_styles,
                        theme,
                        filtros,
                        mostrar_cliente=True  # ← AQUÍ está la clave
                    )
                )

                return html.Div(elementos)
            else:
                return html.Div([
                    html.P("No se encontraron documentos.",
                           style={'textAlign': 'center', 'color': 'gray', 'fontSize': '16px', 'fontFamily': 'Inter'})
                ])
        else:
            # Para cliente específico, usar la lógica original
            detalle = analyzer.get_cliente_detalle(
                cliente_seleccionado, vendedor)

            if not detalle['documentos'].empty:
                elementos = [
                    html.Div([
                        html.H4(f"Forma de Pago: {detalle['forma_pago']}", style={
                            'backgroundColor': 'rgba(23, 162, 184, 0.4)',
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

                # Crear tabla unificada SIN columna de cliente
                elementos.append(
                    crear_tabla_unificada(
                        detalle['documentos'],
                        theme_styles,
                        theme,
                        filtros,
                        mostrar_cliente=False  # ← NO mostrar cliente para un cliente específico
                    )
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


def crear_tabla_unificada(df, theme_styles, theme, filtros=None, mostrar_cliente=False):
    """
    Create a unified table for both overdue and current documents with filtering.

    Args:
        df: DataFrame con los documentos
        theme_styles: Estilos del tema
        theme: Tema actual ('light' o 'dark')
        filtros: Filtros aplicados
        mostrar_cliente: Si True, muestra columna de cliente
    """
    if df.empty:
        return html.P("No hay documentos para este cliente.")

    # Default filters if none provided
    if filtros is None:
        filtros = \
            {
                'vencida': True,
                'vence_hoy': True,
                'proximos': True,
                'sin_vencer': True
            }

    # Create filtering conditions using pandas operations - MÉTODO MEJORADO
    df_work = df.copy()

    # Ensure dias_vencidos is numeric
    df_work['dias_vencidos_num'] = pd.to_numeric(
        df_work['dias_vencidos'], errors='coerce')

    # Create boolean masks for each category
    mask_vencida = \
        (df_work['dias_vencidos_num'] > 0) & filtros.get('vencida', True)
    mask_vence_hoy = \
        (df_work['dias_vencidos_num'] == 0) & filtros.get('vence_hoy', True)
    mask_proximos = \
        (df_work['dias_vencidos_num'] == -1) & filtros.get('proximos', True)
    mask_sin_vencer = \
        (df_work['dias_vencidos_num'] < -1) & filtros.get('sin_vencer', True)

    # Combine all masks
    final_mask = mask_vencida | mask_vence_hoy | mask_proximos | mask_sin_vencer

    # Apply filter
    df_filtered = df_work[final_mask]

    # Drop the helper column
    if 'dias_vencidos_num' in df_filtered.columns:
        df_filtered = df_filtered.drop('dias_vencidos_num', axis=1)

    # Header row
    header_style = \
        {
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
    cell_style_base = \
        {
            'padding': '10px 8px',
            'fontSize': '12px',
            'fontFamily': 'Inter',
            'textAlign': 'center',
            'border': '1px solid #dee2e6'
        }

    # Create table rows - MODIFICADO para incluir columna de cliente
    table_headers = [
        html.Th("Estado", style={**header_style, 'width': '80px'}),
        html.Th("Documento", style={**header_style, 'width': '80px'})
    ]

    # Agregar columna de cliente si mostrar_cliente es True
    if mostrar_cliente:
        table_headers.append(
            html.Th("Cliente", style={**header_style, 'width': '200px'})
        )

    # Continuar con las demás columnas
    table_headers.extend([
        html.Th("Valor", style={**header_style, 'width': '90px'}),
        html.Th("Aplicado", style={**header_style, 'width': '90px'}),
        html.Th("Saldo", style={**header_style, 'width': '90px'}),
        html.Th("Fecha", style={**header_style, 'width': '90px'}),
        html.Th("Vencimiento", style={**header_style, 'width': '90px'}),
        html.Th("Días", style={**header_style, 'width': '120px'}),
        html.Th("Notas", style={**header_style,
                'width': '190px', 'maxWidth': '190px'})
    ])

    table_rows = [html.Tr(table_headers)]

    # Process filtered rows
    for i, (_, row) in enumerate(df_filtered.iterrows()):
        # Determine document status based on dias_vencidos
        dias_vencidos = \
            int(row['dias_vencidos']) if pd.notna(
                row['dias_vencidos']) else None

        # Determine status and colors
        if dias_vencidos is not None and dias_vencidos == 0:
            estado_text = 'VENCE HOY'
            estado_bg = '#FF8C42'

            if theme == 'dark':
                row_bg = '#4a3520' if i % 2 == 0 else '#5a4028'  # Dark orange
            else:
                row_bg = '#fff3e0' if i % 2 == 0 else '#ffe0b2'  # Light orange

        elif dias_vencidos is not None and dias_vencidos > 0:
            estado_text = 'VENCIDA'
            estado_bg = '#e74c3c'

            if theme == 'dark':
                row_bg = '#4a2d2d' if i % 2 == 0 else '#5a3535'  # Dark red
            else:
                row_bg = '#f8e8e8' if i % 2 == 0 else '#f5c6cb'  # Light red

        elif dias_vencidos is not None and dias_vencidos == -1:
            estado_text = 'PRÓXIMO A VENCER'
            estado_bg = '#FFB74D'

            if theme == 'dark':
                row_bg = '#4a3520' if i % 2 == 0 else '#5a4028'  # Dark orange
            else:
                row_bg = '#fff3e0' if i % 2 == 0 else '#ffe0b2'  # Light orange
        else:
            estado_text = 'SIN VENCER'
            estado_bg = '#27ae60'

            if theme == 'dark':
                row_bg = '#2d4a35' if i % 2 == 0 else '#35553d'  # Dark green
            else:
                row_bg = '#e8f5e8' if i % 2 == 0 else '#d4edda'  # Light green

        cell_style = cell_style_base.copy()
        cell_style['backgroundColor'] = row_bg

        # Estado cell with special styling
        estado_style = \
            {
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

        # Format days
        if isinstance(dias_vencidos, int):
            if dias_vencidos > 0:
                dias_display = f"{dias_vencidos} días (vencidos)"
                dias_color = '#e74c3c'
            elif dias_vencidos == 0:
                dias_display = "Vence hoy"
                dias_color = '#FF8C42'
            elif dias_vencidos == -1:  # ✅ Falta exactamente 1 día
                dias_display = "Vence mañana"
                dias_color = '#FFB74D'
            else:  # dias_vencidos < -1
                dias_display = f"{abs(dias_vencidos)} días (por vencer)"
                dias_color = '#27ae60'
        else:
            dias_display = 'N/A'
            dias_color = '#95a5a6'

        # Handle notas
        notas_text = str(row.get('notas', 'Sin notas'))

        if len(notas_text) > 40:
            notas_display = notas_text[:37] + "..."
            notas_title = notas_text
        else:
            notas_display = notas_text
            notas_title = notas_text

        notas_style = \
            {
                **cell_style,
                'maxWidth': '150px',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
                'whiteSpace': 'nowrap',
                'textAlign': 'left',
                'cursor': 'help' if len(notas_text) > 40 else 'default'
            }

        # Crear las celdas de la fila
        row_cells = [
            html.Td(estado_text, style=estado_style),
            html.Td(row['documento_id'], style=cell_style)
        ]

        # Agregar celda de cliente si mostrar_cliente es True
        if mostrar_cliente:
            # Obtener nombre del cliente de forma segura
            cliente_nombre = row.get(
                'razon_social', row.get('cliente_nombre', 'N/A'))

            # Truncar nombre si es muy largo
            if len(cliente_nombre) > 50:
                cliente_display = cliente_nombre[:47] + "..."
                cliente_title = cliente_nombre
            else:
                cliente_display = cliente_nombre
                cliente_title = cliente_nombre

            cliente_style = {
                **cell_style,
                'maxWidth': '200px',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
                'whiteSpace': 'nowrap',
                'textAlign': 'left',
                'cursor': 'help' if len(cliente_nombre) > 30 else 'default'
            }

            row_cells.append(
                html.Td(cliente_display, style=cliente_style,
                        title=cliente_title)
            )

        # Agregar las demás celdas
        row_cells.extend([
            html.Td(format_currency_int(row['valor']), style=cell_style),
            html.Td(format_currency_int(row['aplicado']), style=cell_style),
            html.Td(format_currency_int(row['saldo']), style=cell_style),
            html.Td(fecha_str, style=cell_style),
            html.Td(vencimiento_str, style=cell_style),
            html.Td(dias_display, style={
                    **cell_style, 'color': dias_color, 'fontWeight': 'bold'}),
            html.Td(notas_display, style=notas_style, title=notas_title)
        ])

        table_rows.append(html.Tr(row_cells))

    # Create clickable filter legend
    def create_filter_button(filter_key, label, color, is_active):
        return \
            html.Div([
                html.Span("●", style={
                    'color': color if is_active else '#ccc',
                    'marginRight': '5px',
                    'fontSize': '16px',
                    'transition': 'color 0.3s ease'
                }),
                html.Span(label, style={
                    'fontSize': '12px',
                    'color': theme_styles['text_color'] if is_active else '#ccc',
                    'fontWeight': 'bold' if is_active else 'normal',
                    'transition': 'all 0.3s ease'
                })
            ],
                id=f'cartera-filtro-{filter_key}',
                style={
                'display': 'inline-flex',
                'alignItems': 'center',
                'marginRight': '15px',
                'cursor': 'pointer',
                'padding': '5px 8px',
                'borderRadius': '15px',
                'backgroundColor': 'rgba(0,0,0,0.05)' if is_active else 'transparent',
                'border': f'1px solid {color}' if is_active else '1px solid transparent',
                'transition': 'all 0.3s ease',
                'userSelect': 'none'
            }
            )

    # Count documents by category using the original dataframe
    vencida_count = len(
        df[pd.to_numeric(df['dias_vencidos'], errors='coerce') > 0])
    vence_hoy_count = len(
        df[pd.to_numeric(df['dias_vencidos'], errors='coerce') == 0])
    proximos_count = len(
        df[pd.to_numeric(df['dias_vencidos'], errors='coerce') == -1])
    sin_vencer_count = len(
        df[pd.to_numeric(df['dias_vencidos'], errors='coerce') < -1])

    return html.Div([
        # Filters section
        html.Div([
            html.Div([
                html.Span("Filtros: ", style={
                    'fontSize': '14px',
                    'fontWeight': 'bold',
                    'marginRight': '15px',
                    'color': theme_styles['text_color']
                }),
                create_filter_button(
                    'vencida', f'Vencida ({vencida_count})', '#e74c3c', filtros.get('vencida', True)),
                create_filter_button(
                    'vence-hoy', f'Vence Hoy ({vence_hoy_count})', '#FF8C42', filtros.get('vence_hoy', True)),
                create_filter_button(
                    'proximos', f'Próximos ({proximos_count})', '#FFB74D', filtros.get('proximos', True)),
                create_filter_button(
                    'sin-vencer', f'Al Día ({sin_vencer_count})', '#27ae60', filtros.get('sin_vencer', True)),

                # Botón "Todos"
                html.Div([
                    html.Span("Todos", style={
                        'fontSize': '12px',
                        'fontWeight': 'bold',
                        'color': 'white'
                    })
                ], id='cartera-filtro-todos', style={
                    'display': 'inline-flex',
                    'alignItems': 'center',
                    'marginLeft': '10px',
                    'cursor': 'pointer',
                    'padding': '5px 12px',
                    'borderRadius': '15px',
                    'backgroundColor': '#6c757d',
                    'transition': 'all 0.3s ease',
                    'userSelect': 'none'
                })

            ], style={
                'textAlign': 'center',
                'marginBottom': '15px',
                'padding': '10px',
                'backgroundColor': theme_styles['paper_color'],
                'borderRadius': '8px',
                'border': f'1px solid {theme_styles["line_color"]}'
            })
        ]),

        # Table container
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

        # Results counter
        html.Div([
            html.Span(f"Mostrando {len(df_filtered)} de {len(df)} documentos", style={
                'fontSize': '12px',
                'color': theme_styles['text_color'],
                'fontStyle': 'italic'
            })
        ], style={
            'textAlign': 'center',
            'marginTop': '10px'
        })
    ])


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

        bg_colors = [
            "rgba(0, 119, 182, 0.4)",    # Azul medio
            "rgba(0, 180, 216, 0.4)",    # Cian brillante
            "rgba(144, 224, 239, 0.4)",  # Celeste pastel
            "rgba(202, 240, 248, 0.4)",  # Azul muy claro
            "rgba(2, 62, 138, 0.4)",     # Azul oscuro intenso
            "rgba(3, 4, 94, 0.4)",       # Azul profundo
            "rgba(0, 150, 199, 0.4)",    # Azul cielo saturado
            "rgba(72, 202, 228, 0.4)",   # Celeste vívido
            "rgba(173, 232, 244, 0.4)",  # Azul cielo suave
            "rgba(97, 165, 194, 0.4)",   # Azul acero claro
            "rgba(1, 79, 134, 0.4)",     # Azul marino medio
            "rgba(0, 126, 167, 0.4)",    # Azul con un toque más verdoso
            "rgba(5, 102, 141, 0.4)",    # Azul petróleo apagado
            "rgba(95, 168, 211, 0.4)",   # Azul claro más saturado
            "rgba(137, 194, 217, 0.4)",  # Celeste desaturado
        ]

        border_colors = [
            "#0077B6",  # Azul medio
            "#00B4D8",  # Cian brillante
            "#90E0EF",  # Celeste pastel
            "#CAF0F8",  # Azul muy claro
            "#023E8A",  # Azul oscuro intenso
            "#03045E",  # Azul profundo
            "#0096C7",  # Azul cielo saturado
            "#48CAE4",  # Celeste vívido
            "#ADE8F4",  # Azul cielo suave
            "#61A5C2",  # Azul acero claro
            "#014F86",  # Azul marino medio
            "#007EA7",  # Azul con un toque más verdoso
            "#05668D",  # Azul petróleo apagado
            "#5FA8D3",  # Azul claro más saturado
            "#89C2D9",  # Celeste desaturado
        ]

        # Create modern chart with pastel colors
        fig = go.Figure()

        for i, row in data.iterrows():
            color_index = i % len(bg_colors)

            fig.add_trace(go.Bar(
                x=[row['rango']],
                y=[row['saldo']],
                name=row['rango'],
                marker=dict(
                    color=bg_colors[color_index],
                    line=dict(color=border_colors[color_index], width=1.5),
                    opacity=0.6
                ),
                text=[format_currency_int(row['saldo'])],
                textposition='outside',
                hovertemplate=f"<b>{row['rango']}</b><br>" +
                             f"Valor: {format_currency_int(row['saldo'])}<br>" +
                             f"Documentos: {row['documento_id']}<extra></extra>"
            ))

        fig.update_layout(
            title="",
            xaxis_title="Rango de Vencimiento",
            yaxis_title="Valor ($)",
            height=500,
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

        bg_colors = [
            "#0077B680",
            "#00B4D880",
            "#90E0EF80",
            "#CAF0F880",
            "#023E8A80",
            "#03045E80",
            "#0096C780",
            "#48CAE480",
            "#ADE8F480",
            "#61A5C280",
            "#014F8680",
            "#007EA780",
            "#05668D80",
            "#5FA8D380",
            "#89C2D980",
        ]

        border_colors = [
            "#0077B6",  # Azul medio
            "#00B4D8",  # Cian brillante
            "#90E0EF",  # Celeste pastel
            "#CAF0F8",  # Azul muy claro
            "#023E8A",  # Azul oscuro intenso
            "#03045E",  # Azul profundo
            "#0096C7",  # Azul cielo saturado
            "#48CAE4",  # Celeste vívido
            "#ADE8F4",  # Azul cielo suave
            "#61A5C2",  # Azul acero claro
            "#014F86",  # Azul marino medio
            "#007EA7",  # Azul con un toque más verdoso
            "#05668D",  # Azul petróleo apagado
            "#5FA8D3",  # Azul claro más saturado
            "#89C2D9",  # Celeste desaturado
        ]

        # Modern donut chart with pastel colors
        fig = go.Figure(data=[go.Pie(
            labels=data['forma_pago'],
            values=data['saldo'],
            hole=.4,
            opacity=0.8,
            textinfo='percent',
            textposition='inside',
            textfont=dict(color=theme_styles['text_color'], size=11),
            marker=dict(
                colors=bg_colors,
                line=dict(color=border_colors, width=1.5)
            ),
            hovertemplate="<b>%{label}</b><br>" +
            "Valor: %{customdata}<br>" +
            "Porcentaje: %{percent}<extra></extra>",
            customdata=[format_currency_int(val) for val in data['saldo']]
        )])

        fig.update_layout(
            title="",
            height=410,
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
    Output('cartera-top-unificado', 'figure'),
    [Input('session-store', 'data'),
     Input('cartera-dropdown-vendedor', 'value'),
     Input('cartera-data-store', 'data'),
     Input('cartera-theme-store', 'data')]
)
def update_top_unificado(session_data, dropdown_value, n_clicks, theme):
    """
    Top 10 corregido para manejar valores negativos correctamente
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        df = analyzer.filter_by_vendedor(vendedor)
        theme_styles = get_theme_styles(theme)

        if df.empty:
            fig = px.bar(title="No hay datos disponibles")
            fig.update_layout(
                height=500, paper_bgcolor=theme_styles['plot_bg'])
            return fig

        # Agrupar por cliente y obtener top 10
        data = df.groupby(['cliente_id', 'cliente_completo']).agg({
            'vencida': 'sum',
            'sin_vencer': 'sum',
            'saldo': 'sum'
        }).reset_index()

        # Filtrar y ordenar top 10
        data = data[data['saldo'] > 0].nlargest(10, 'saldo')
        data = data.sort_values('saldo', ascending=True)

        if data.empty:
            fig = px.bar(title="No hay datos con valores positivos")
            fig.update_layout(
                height=500, paper_bgcolor=theme_styles['plot_bg'])
            return fig

        # Crear etiquetas cortas para el eje Y
        data['short_label'] = [f"#{i}" for i in range(len(data), 0, -1)]

        # Manejar valores negativos en vencida
        data['vencida_display'] = data['vencida'].clip(
            lower=0)  # No valores negativos
        data['sin_vencer_display'] = data['sin_vencer'].clip(
            lower=0)  # No valores negativos

        # Recalcular saldo para visualización
        data['saldo_display'] = data['vencida_display'] + \
            data['sin_vencer_display']

        fig = go.Figure()

        # Barra de cartera sin vencer (verde) - PRIMERO para que esté en el fondo
        fig.add_trace(go.Bar(
            name='Cartera Al Día',
            y=data['short_label'],
            x=data['sin_vencer_display'],
            orientation='h',
            marker=dict(
                color='rgba(39, 174, 96, 0.6)',
                line=dict(color='rgba(39, 174, 96, 0.9)', width=1.5)
                # opacity=0.6
            ),
            text=[f"{format_currency_int(val)}" if val >
                  0 else "" for val in data['sin_vencer_display']],
            textposition='inside',
            textfont=dict(color='white', size=10,
                          family='Inter', weight='bold'),
            hovertemplate="<b>%{customdata[0]}</b><br>" +
                         "Cartera Al Día: %{customdata[1]}<br>" +
                         "Porcentaje: %{customdata[2]:.1f}%<extra></extra>",
            customdata=[[cliente, format_currency_int(sin_vencer), (sin_vencer/saldo*100) if saldo > 0 else 0]
                        for cliente, sin_vencer, saldo in zip(data['cliente_completo'], data['sin_vencer_display'], data['saldo_display'])]
        ))

        # Barra de cartera vencida (roja) - SEGUNDO para que se apile correctamente
        fig.add_trace(go.Bar(
            name='Cartera Vencida',
            y=data['short_label'],
            x=data['vencida_display'],
            orientation='h',
            marker=dict(
                color='rgba(231, 76, 60, 0.6)',
                line=dict(color='rgba(231, 76, 60, 0.9)', width=1.5)
                # opacity=0.6
            ),
            text=[f"{format_currency_int(val)}" if val >
                  0 else "" for val in data['vencida_display']],
            textposition='inside',
            textfont=dict(color='white', size=10,
                          family='Inter', weight='bold'),
            hovertemplate="<b>%{customdata[0]}</b><br>" +
                         "Cartera Vencida: %{customdata[1]}<br>" +
                         "Porcentaje: %{customdata[2]:.1f}%<extra></extra>",
            customdata=[[cliente, format_currency_int(vencida), (vencida/saldo*100) if saldo > 0 else 0]
                        for cliente, vencida, saldo in zip(data['cliente_completo'], data['vencida_display'], data['saldo_display'])]
        ))

        # Añadir anotaciones con nombres de clientes
        for i, (idx, row) in enumerate(data.iterrows()):
            cliente_display = row['cliente_completo'][:50] + "..." if len(
                row['cliente_completo']) > 50 else row['cliente_completo']
            fig.add_annotation(
                x=row['saldo_display'] + (row['saldo_display'] * 0.02),
                y=i,
                text=f"<b>{cliente_display}</b><br>{format_currency_int(row['saldo_display'])}",
                showarrow=False,
                xanchor='left',
                yanchor='middle',
                font=dict(
                    size=10, color=theme_styles['text_color'], family='Inter', weight='bold'),
                bgcolor='rgba(255, 255, 255, 0.95)' if theme == 'light' else 'rgba(0, 0, 0, 0.8)',
                bordercolor=theme_styles['line_color'],
                borderwidth=1,
                borderpad=4
            )

        fig.update_layout(
            barmode='stack',  # Importante para apilar correctamente
            height=500,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=12,
                      color=theme_styles['text_color']),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom", y=1.02,
                xanchor="center", x=0.5,
                bgcolor='rgba(255, 255, 255, 0.95)' if theme == 'light' else 'rgba(0, 0, 0, 0.8)',
                bordercolor=theme_styles['line_color'],
                borderwidth=1
            ),
            xaxis=dict(
                title="Valor de Cartera ($)",
                tickformat='$,.0f',
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.15)',
                linecolor=theme_styles['line_color'],
                zeroline=False
            ),
            yaxis=dict(
                title="Ranking",
                showgrid=False,
                linecolor=theme_styles['line_color'],
                categoryorder='array',
                categoryarray=data['short_label']
            ),
            margin=dict(t=60, b=60, l=80, r=180)
        )

        return fig

    except Exception as e:
        print(f"Error en update_top_unificado: {e}")
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

                return f'rgba({r},{g},{b},0.4)'

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
                        line=dict(color=colors, width=1.5),
                        opacity=0.9
                    ),
                    hovertemplate="<b>%{fullData.name}</b><br>" +
                    "Días hasta vencimiento: %{x}<br>" +
                    "%{customdata}<br>" +
                    "<extra></extra>",
                    customdata=hover_data,
                    text=text_data,
                    textposition='inside',
                    textfont=dict(
                        size=9, color=theme_styles['text_color'], family='Inter'),
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


@callback(
    Output('cartera-treemap-unificado', 'figure'),
    [Input('session-store', 'data'),
     Input('cartera-dropdown-vendedor', 'value'),
     Input('cartera-data-store', 'data'),
     Input('cartera-theme-store', 'data'),
     Input('cartera-filtro-porcentaje-vencida', 'value')]
)
def update_treemap_unificado(session_data, dropdown_value, n_clicks, theme, filtro_porcentaje):
    """
    Treemap elegante con gradiente verde-rojo para clientes y colores sólidos para subdivisiones
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        df = analyzer.filter_by_vendedor(vendedor)
        theme_styles = get_theme_styles(theme)

        # Validar datos
        if df.empty:
            return create_empty_figure("No hay datos disponibles", theme_styles)

        # Procesar y agrupar datos por cliente
        resultado = df.groupby(['cliente_completo']).agg({
            'vencida': 'sum',
            'sin_vencer': 'sum',
            'saldo': 'sum'
        }).reset_index()

        # Filtrar solo clientes con saldo positivo
        resultado = resultado[resultado['saldo'] > 0].copy()

        if resultado.empty:
            return create_empty_figure("No hay datos con saldo positivo", theme_styles)

        # Calcular porcentaje de cartera vencida
        resultado['pct_vencida'] = (
            resultado['vencida'] / resultado['saldo'] * 100).fillna(0)

        if filtro_porcentaje and len(filtro_porcentaje) == 2:
            min_pct, max_pct = filtro_porcentaje
            resultado = resultado[
                (resultado['pct_vencida'] >= min_pct) &
                (resultado['pct_vencida'] <= max_pct)
            ]

            if resultado.empty:
                return create_empty_figure(
                    f"No hay clientes con cartera vencida entre {min_pct}% y {max_pct}%",
                    theme_styles
                )

        # Ordenar por porcentaje vencido (mejores primero) y luego por saldo
        resultado = resultado.sort_values(
            ['pct_vencida', 'saldo'], ascending=[True, False])

        # Generar estructura del treemap
        treemap_data = build_treemap_structure(resultado, theme == 'dark')

        # Crear y configurar el gráfico
        fig = create_treemap_figure(treemap_data, theme_styles, theme)

        return fig

    except Exception as e:
        print(f"❌ Error en treemap_unificado: {e}")
        import traceback
        traceback.print_exc()
        return create_error_figure(str(e), theme_styles if 'theme_styles' in locals() else None)


def create_empty_figure(message, theme_styles):
    """Crear figura vacía con mensaje"""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        xanchor='center', yanchor='middle',
        showarrow=False,
        font=dict(size=18, color=theme_styles['text_color'], family='Inter')
    )
    fig.update_layout(
        height=600,
        paper_bgcolor=theme_styles['plot_bg'],
        plot_bgcolor=theme_styles['plot_bg']
    )
    return fig


def create_error_figure(error_msg, theme_styles):
    """Crear figura de error"""
    bg_color = theme_styles['plot_bg'] if theme_styles else 'white'

    fig = go.Figure()
    fig.add_annotation(
        text=f"⚠️ Error cargando visualización<br><span style='font-size:12px; opacity:0.7'>{error_msg[:60]}...</span>",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        xanchor='center', yanchor='middle',
        showarrow=False,
        font=dict(size=16, color='#ef4444', family='Inter')
    )
    fig.update_layout(
        height=600,
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color
    )
    return fig


def get_gradient_color(pct_vencida, is_dark=False, alpha=0.4):
    """
    Generar color gradiente de verde a rojo según porcentaje de cartera vencida
    Con soporte para transparencia configurable
    """
    # Asegurar que el porcentaje esté entre 0 y 100
    ratio = min(max(pct_vencida, 0) / 100.0, 1.0)

    if is_dark:
        # Colores más vibrantes para tema oscuro
        green = [34, 197, 94]    # Verde más oscuro y saturado
        red = [220, 38, 38]      # Rojo más oscuro y saturado
    else:
        # Colores más oscuros para tema claro - MAYOR CONTRASTE
        green = [22, 163, 74]    # Verde esmeralda oscuro
        red = [220, 38, 38]      # Rojo oscuro

    # Interpolación lineal RGB
    r = int(green[0] + (red[0] - green[0]) * ratio)
    g = int(green[1] + (red[1] - green[1]) * ratio)
    b = int(green[2] + (red[2] - green[2]) * ratio)

    if alpha is not None:
        return f'rgba({r},{g},{b},{alpha})'
    else:
        return f'rgb({r},{g},{b})'


def get_child_colors(is_dark=False):
    """
    Obtener colores para elementos hijos (vencida/sin vencer) con MÁS TRANSPARENCIA
    """
    if is_dark:
        return {
            'vencida': 'rgba(248, 113, 113, 0.5)',      # Reducido a 0.3
            'sin_vencer': 'rgba(52, 211, 153, 0.5)',    # Reducido a 0.3
            'vencida_border': 'rgba(248, 113, 113, 1)',  # Borde sólido
            'sin_vencer_border': 'rgba(52, 211, 153, 1)'  # Borde sólido
        }
    else:
        return {
            'vencida': 'rgba(239, 68, 68, 0.5)',        # Reducido a 0.3
            'sin_vencer': 'rgba(16, 185, 129, 0.5)',    # Reducido a 0.3
            'vencida_border': 'rgba(239, 68, 68, 1)',    # Borde sólido
            'sin_vencer_border': 'rgba(16, 185, 129, 1)'  # Borde sólido
        }


def format_currency_complete(value):
    """
    Formatear moneda completa sin abreviar
    """
    try:
        return f"${value:,.0f}".replace(',', '.')
    except:
        return f"${value}"


def truncate_client_name(cliente_name, max_length=85):
    """
    Truncar nombre de cliente de forma inteligente
    """
    if len(cliente_name) <= max_length:
        return cliente_name

    # Buscar el último espacio antes del límite
    punto_corte = cliente_name[:max_length-3].rfind(' ')
    if punto_corte > max_length * 0.7:  # Si encontramos un buen punto de corte
        return cliente_name[:punto_corte] + "..."
    else:
        return cliente_name[:max_length-3] + "..."


def build_treemap_structure(resultado, is_dark):
    """
    Construir la estructura de datos para el treemap con transparencias mejoradas
    """
    ids = []
    labels = []
    parents = []
    values = []
    colors = []
    border_colors = []
    customdata = []
    text_labels = []

    child_colors = get_child_colors(is_dark)

    for idx, (_, row) in enumerate(resultado.iterrows()):
        cliente_completo = str(row['cliente_completo'])
        vencida = max(0, float(row['vencida']))
        sin_vencer = max(0, float(row['sin_vencer']))
        total = vencida + sin_vencer
        pct_vencida = row['pct_vencida']

        if total <= 0:
            continue

        # Truncar nombre del cliente
        cliente_display = truncate_client_name(cliente_completo)

        # Color gradiente para el cliente padre CON TRANSPARENCIA
        cliente_color = get_gradient_color(pct_vencida, is_dark, alpha=0.4)
        cliente_border = get_gradient_color(
            pct_vencida, is_dark, alpha=None)  # SIN transparencia para borde
        cliente_id = f"C{idx}"

        # === CLIENTE PADRE ===
        ids.append(cliente_id)
        labels.append(cliente_display)
        parents.append("")
        values.append(total)
        colors.append(cliente_color)
        border_colors.append(cliente_border)  # ← AGREGAR BORDE

        customdata.append({
            'tipo': 'cliente',
            'cliente_completo': cliente_completo,
            'total': total,
            'vencida': vencida,
            'sin_vencer': sin_vencer,
            'pct_vencida': pct_vencida
        })

        # Texto para cliente padre
        text_labels.append(
            f"<b style='font-size:13px'>{cliente_display}</b><br>" +
            f"<span style='font-size:15px; font-weight:bold'>{format_currency_complete(total)}</span><br>" +
            f"<span style='font-size:11px; opacity:0.9'>{pct_vencida:.1f}% vencida</span>"
        )

        if vencida > total * 0.02:  # Solo mostrar si es significativo (>2%)
            vencida_id = f"C{idx}V"

            ids.append(vencida_id)
            labels.append("Vencida")
            parents.append(cliente_id)
            values.append(vencida)
            # CON transparencia
            colors.append(child_colors['vencida'])
            # SIN transparencia
            border_colors.append(child_colors['vencida_border'])

            customdata.append({
                'tipo': 'vencida',
                'valor': vencida,
                'porcentaje': (vencida/total*100),
                'cliente': cliente_completo
            })

            text_labels.append(
                f"<b style='font-size:11px'>🔴 Vencida</b><br>" +
                f"<span style='font-size:12px; font-weight:bold'>{format_currency_complete(vencida)}</span><br>" +
                f"<span style='font-size:10px; opacity:0.8'>{(vencida/total*100):.1f}%</span>"
            )

        if sin_vencer > total * 0.02:  # Solo mostrar si es significativo (>2%)
            sin_vencer_id = f"C{idx}S"

            ids.append(sin_vencer_id)
            labels.append("Al Día")
            parents.append(cliente_id)
            values.append(sin_vencer)
            # CON transparencia
            colors.append(child_colors['sin_vencer'])
            # SIN transparencia
            border_colors.append(child_colors['sin_vencer_border'])

            customdata.append({
                'tipo': 'sin_vencer',
                'valor': sin_vencer,
                'porcentaje': (sin_vencer/total*100),
                'cliente': cliente_completo
            })

            text_labels.append(
                f"<b style='font-size:11px'>🟢 Sin Vencer</b><br>" +
                f"<span style='font-size:12px; font-weight:bold'>{format_currency_complete(sin_vencer)}</span><br>" +
                f"<span style='font-size:10px; opacity:0.8'>{(sin_vencer/total*100):.1f}%</span>"
            )

    return {
        'ids': ids,
        'labels': labels,
        'parents': parents,
        'values': values,
        'colors': colors,
        'border_colors': border_colors,  # ← NUEVA PROPIEDAD
        'customdata': customdata,
        'text_labels': text_labels
    }


def create_treemap_figure(treemap_data, theme_styles, theme):
    """
    Crear y configurar la figura del treemap con bordes mejorados
    """
    if not treemap_data['ids']:
        return create_empty_figure("No hay datos suficientes para mostrar", theme_styles)

    # Crear el treemap con bordes del mismo color pero sólidos
    fig = go.Figure(go.Treemap(
        ids=treemap_data['ids'],
        labels=treemap_data['labels'],
        parents=treemap_data['parents'],
        values=treemap_data['values'],
        text=treemap_data['text_labels'],
        texttemplate="%{text}",
        textposition="middle center",
        textfont=dict(
            size=12,
            color=theme_styles['text_color'],
            family='Inter',
            weight='bold'
        ),
        marker=dict(
            colors=treemap_data['colors'],
            line=dict(
                width=1.5,  # Borde más grueso para mejor definición
                # ← USAR BORDES PERSONALIZADOS
                color=treemap_data['border_colors']
            ),
            showscale=False
        ),
        hovertemplate="%{text}<br><extra></extra>",
        hoverlabel=dict(
            bgcolor="rgba(0,0,0,0.8)",
            bordercolor="white",
            font=dict(color="white", family="Inter", size=12)
        ),
        branchvalues="total",
        pathbar=dict(visible=False),
        sort=True,  # ← ORDENAR POR TAMAÑO
        tiling=dict(
            packing="squarify",
            pad=3
        )
    ))

    # Configurar layout
    fig.update_layout(
        # Dimensiones
        height=600,
        margin=dict(t=20, b=60, l=10, r=10),

        # Colores y tema
        plot_bgcolor=theme_styles['plot_bg'],
        paper_bgcolor=theme_styles['plot_bg'],

        # Tipografía
        font=dict(
            family="Inter, -apple-system, BlinkMacSystemFont, sans-serif",
            size=12,
            color=theme_styles['text_color']
        ),

        # Interactividad
        showlegend=False,
        dragmode=False,
        hovermode='closest',

        # Transiciones
        transition=dict(duration=300, easing="cubic-in-out")
    )

    return fig


@callback(
    Output('cartera-filtro-porcentaje-vencida', 'className'),
    [Input('cartera-theme-store', 'data')]
)
def update_slider_theme(theme):
    """
    Actualizar el estilo del slider según el tema
    """
    return 'range-slider-dark' if theme == 'dark' else 'range-slider-light'


# @callback(
#     [Output('cartera-indicador-container', 'children'),
#      Output('cartera-indicador-section', 'style')],
#     [Input('session-store', 'data'),
#      Input('cartera-dropdown-vendedor', 'value'),
#      Input('cartera-data-store', 'data'),
#      Input('cartera-theme-store', 'data')]
# )
# def update_indicador_section(session_data, dropdown_value, data_store, theme):
#     """
#     Update portfolio indicator section based on user permissions
#     """
#     from utils import can_see_all_vendors, get_user_vendor_filter

#     theme_styles = get_theme_styles(theme)

#     # Base style for the section
#     section_style = {
#         'borderRadius': '16px',
#         'padding': '24px',
#         'marginBottom': '24px',
#         'boxShadow': theme_styles['card_shadow'],
#         'width': '100%',
#         'backgroundColor': theme_styles['paper_color'],
#         'color': theme_styles['text_color']
#     }

#     try:
#         if not session_data:
#             return html.Div("No hay sesión activa"), section_style

#         is_admin = can_see_all_vendors(session_data)

#         if is_admin:
#             # Para administradores: mostrar tabla con todos los vendedores
#             indicators = analyzer.calculate_portfolio_indicator('Todos')

#             if not indicators:
#                 return html.Div("No hay datos de indicadores disponibles"), section_style

#             # Crear tabla de indicadores
#             table_content = create_indicators_table(
#                 indicators, theme_styles, theme)
#             return table_content, section_style

#         else:
#             # Para vendedores: mostrar su propio indicador con gráfico
#             vendor = get_user_vendor_filter(session_data)
#             indicator_data = analyzer.calculate_portfolio_indicator(vendor)

#             if not indicator_data:
#                 return html.Div("No hay datos de indicador disponibles"), section_style

#             # Crear visualización del indicador individual
#             vendor_content = create_vendor_indicator_view(
#                 indicator_data, theme_styles, theme)
#             return vendor_content, section_style

#     except Exception as e:
#         print(f"Error en update_indicador_section: {e}")
#         return html.Div(f"Error cargando indicadores"), section_style


# def create_indicators_table(indicators, theme_styles, theme):
#     """
#     Create a table showing all vendors' indicators for admin view
#     """
#     if not indicators:
#         return html.Div("No hay datos disponibles")

#     # Header row
#     header_style = {
#         'backgroundColor': '#2c3e50' if theme == 'light' else '#1a1a1a',
#         'color': 'white',
#         'padding': '12px 8px',
#         'fontWeight': 'bold',
#         'fontSize': '12px',
#         'fontFamily': 'Inter',
#         'textAlign': 'center',
#         'border': '1px solid #34495e'
#     }

#     cell_style = {
#         'padding': '10px 8px',
#         'fontSize': '11px',
#         'fontFamily': 'Inter',
#         'textAlign': 'center',
#         'border': '1px solid #dee2e6'
#     }

#     # Create table headers
#     headers = [
#         html.Th("#", style={**header_style, 'width': '40px'}),
#         html.Th("Vendedor", style={**header_style, 'width': '180px'}),
#         html.Th("Indicador de Riesgo", style={
#                 **header_style, 'width': '120px'}),
#         html.Th("Cartera Total", style={**header_style, 'width': '100px'}),
#         html.Th("Cartera Vencida", style={**header_style, 'width': '100px'}),
#         html.Th("Tasa Mora %", style={**header_style, 'width': '80px'}),
#         html.Th("WOF (días)", style={**header_style, 'width': '80px'}),
#         html.Th("DSO", style={**header_style, 'width': '60px'}),
#         html.Th("Efic. Recaudo %", style={**header_style, 'width': '90px'}),
#         html.Th("Conc. Riesgo %", style={**header_style, 'width': '90px'}),
#         html.Th("Clientes", style={**header_style, 'width': '70px'})
#     ]

#     rows = [html.Tr(headers)]

#     # Add data rows
#     for idx, vendor in enumerate(indicators[:20], 1):  # Limit to top 20
#         # Determine risk level and color
#         risk = vendor['risk_indicator']
#         if risk >= 0.7:
#             risk_color = '#e74c3c'
#             risk_level = 'ALTO'
#         elif risk >= 0.4:
#             risk_color = '#f39c12'
#             risk_level = 'MEDIO'
#         else:
#             risk_color = '#27ae60'
#             risk_level = 'BAJO'

#         # Determine row background based on risk
#         if risk >= 0.7:
#             row_bg = '#ffebee' if theme == 'light' else '#4a2d2d'
#         elif risk >= 0.4:
#             row_bg = '#fff3e0' if theme == 'light' else '#4a3520'
#         else:
#             row_bg = '#e8f5e9' if theme == 'light' else '#2d4a35'

#         row_style = {**cell_style, 'backgroundColor': row_bg}

#         # Create risk indicator cell with visual bar
#         risk_indicator_cell = html.Td([
#             html.Div([
#                 # Risk value
#                 html.Span(f"{risk:.3f}", style={
#                     'fontWeight': 'bold',
#                     'color': risk_color,
#                     'marginRight': '8px'
#                 }),
#                 # Risk level badge
#                 html.Span(risk_level, style={
#                     'fontSize': '10px',
#                     'backgroundColor': risk_color,
#                     'color': 'white',
#                     'padding': '2px 6px',
#                     'borderRadius': '10px',
#                     'fontWeight': 'bold'
#                 })
#             ]),
#             # Progress bar
#             html.Div([
#                 html.Div(style={
#                     'width': f'{risk * 100}%',
#                     'height': '4px',
#                     'backgroundColor': risk_color,
#                     'borderRadius': '2px',
#                     'marginTop': '4px'
#                 })
#             ], style={
#                 'width': '100%',
#                 'height': '4px',
#                 'backgroundColor': '#ecf0f1',
#                 'borderRadius': '2px',
#                 'marginTop': '4px'
#             })
#         ], style=row_style)

#         row = html.Tr([
#             html.Td(str(idx), style={**row_style, 'fontWeight': 'bold'}),
#             html.Td(vendor['vendor'][:30], style={
#                     **row_style, 'textAlign': 'left', 'fontWeight': '600'}),
#             risk_indicator_cell,
#             html.Td(format_currency_int(
#                 vendor['total_portfolio']), style=row_style),
#             html.Td(format_currency_int(
#                 vendor['overdue_portfolio']), style=row_style),
#             html.Td(f"{vendor['overdue_rate']:.1f}%", style=row_style),
#             html.Td(f"{vendor['wof']:.0f}", style=row_style),
#             html.Td(f"{vendor['dso']:.0f}", style=row_style),
#             html.Td(f"{vendor['collection_efficiency']:.1f}%",
#                     style=row_style),
#             html.Td(f"{vendor['risk_concentration']:.1f}%", style=row_style),
#             html.Td(str(vendor['client_count']), style=row_style)
#         ])

#         rows.append(row)

#     return html.Div([
#         # Summary statistics
#         html.Div([
#             html.Div([
#                 html.Span("Total Vendedores: ", style={'fontWeight': 'bold'}),
#                 html.Span(f"{len(indicators)}")
#             ], style={'display': 'inline-block', 'marginRight': '30px'}),
#             html.Div([
#                 html.Span("Riesgo Promedio: ", style={'fontWeight': 'bold'}),
#                 html.Span(
#                     f"{sum(v['risk_indicator'] for v in indicators) / len(indicators):.3f}")
#             ], style={'display': 'inline-block', 'marginRight': '30px'}),
#             html.Div([
#                 html.Span("Alto Riesgo: ", style={
#                           'fontWeight': 'bold', 'color': '#e74c3c'}),
#                 html.Span(
#                     f"{len([v for v in indicators if v['risk_indicator'] >= 0.7])}")
#             ], style={'display': 'inline-block'})
#         ], style={
#             'marginBottom': '20px',
#             'padding': '15px',
#             'backgroundColor': theme_styles['paper_color'],
#             'borderRadius': '8px',
#             'border': f'1px solid {theme_styles["line_color"]}'
#         }),

#         # Table
#         html.Div([
#             html.Table(rows, style={
#                 'width': '100%',
#                 'borderCollapse': 'collapse',
#                 'fontSize': '12px',
#                 'fontFamily': 'Inter'
#             })
#         ], style={
#             'maxHeight': '600px',
#             'overflowY': 'auto',
#             'overflowX': 'auto',
#             'border': f'2px solid {theme_styles["line_color"]}',
#             'borderRadius': '8px',
#             'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'
#         })
#     ])


# def create_vendor_indicator_view(indicator_data, theme_styles, theme):
#     """
#     Create a visual representation of vendor's indicator with breakdown
#     """
#     if not indicator_data:
#         return html.Div("No hay datos disponibles")

#     risk = indicator_data['risk_indicator']

#     # Determine risk level
#     if risk >= 0.7:
#         risk_color = '#e74c3c'
#         risk_level = 'ALTO RIESGO'
#         risk_message = 'Requiere atención inmediata'
#     elif risk >= 0.4:
#         risk_color = '#f39c12'
#         risk_level = 'RIESGO MEDIO'
#         risk_message = 'Monitoreo constante recomendado'
#     else:
#         risk_color = '#27ae60'
#         risk_level = 'BAJO RIESGO'
#         risk_message = 'Desempeño satisfactorio'

#     # Create gauge chart for main indicator
#     fig_gauge = go.Figure(go.Indicator(
#         mode="gauge+number+delta",
#         value=risk,
#         domain={'x': [0, 1], 'y': [0, 1]},
#         title={'text': f"Indicador de Riesgo<br>{indicator_data['vendor']}",
#                'font': {'size': 16, 'family': 'Inter'}},
#         delta={'reference': 0.5, 'increasing': {
#             'color': "red"}, 'decreasing': {'color': "green"}},
#         gauge={
#             'axis': {'range': [None, 1], 'tickwidth': 1, 'tickcolor': theme_styles['text_color']},
#             'bar': {'color': risk_color},
#             'bgcolor': "white",
#             'borderwidth': 2,
#             'bordercolor': theme_styles['line_color'],
#             'steps': [
#                 {'range': [0, 0.4], 'color': 'rgba(39, 174, 96, 0.2)'},
#                 {'range': [0.4, 0.7], 'color': 'rgba(243, 156, 18, 0.2)'},
#                 {'range': [0.7, 1], 'color': 'rgba(231, 76, 60, 0.2)'}
#             ],
#             'threshold': {
#                 'line': {'color': "red", 'width': 4},
#                 'thickness': 0.75,
#                 'value': 0.7
#             }
#         }
#     ))

#     fig_gauge.update_layout(
#         height=300,
#         paper_bgcolor=theme_styles['plot_bg'],
#         font={'color': theme_styles['text_color'], 'family': 'Inter'},
#         margin=dict(t=50, b=50, l=50, r=50)
#     )

#     # Create breakdown chart for components
#     components = indicator_data.get('component_risks', {})

#     # Component names and weights for display
#     component_info = [
#         ('Tasa de Mora', 'overdue_rate_risk', 0.25,
#          indicator_data.get('overdue_rate', 0)),
#         ('WOF (días vencidos)', 'wof_risk', 0.25, indicator_data.get('wof', 0)),
#         ('Eficiencia Recaudo', 'collection_risk', 0.15,
#          indicator_data.get('collection_efficiency', 0)),
#         ('Rotación (DSO)', 'dso_risk', 0.20, indicator_data.get('dso', 0)),
#         ('Concentración Riesgo', 'concentration_risk',
#          0.15, indicator_data.get('risk_concentration', 0))
#     ]

#     # Prepare data for stacked bar chart
#     fig_components = go.Figure()

#     for name, key, weight, metric_value in component_info:
#         risk_value = components.get(key, 0)
#         weighted_contribution = risk_value * weight

#         color = '#e74c3c' if risk_value >= 0.7 else '#f39c12' if risk_value >= 0.4 else '#27ae60'

#         fig_components.add_trace(go.Bar(
#             name=f'{name} ({weight*100:.0f}%)',
#             x=[weighted_contribution],
#             y=['Contribución al Riesgo'],
#             orientation='h',
#             marker=dict(
#                 color=color,
#                 opacity=0.7,
#                 line=dict(color=color, width=2)
#             ),
#             text=f'{name}<br>Riesgo: {risk_value:.3f}<br>Métrica: {metric_value:.1f}',
#             textposition='inside',
#             hovertemplate=f'<b>{name}</b><br>' +
#                          f'Peso: {weight*100:.0f}%<br>' +
#                          f'Riesgo: {risk_value:.3f}<br>' +
#                          f'Contribución: {weighted_contribution:.3f}<br>' +
#                          f'Valor métrica: {metric_value:.1f}<extra></extra>'
#         ))

#     fig_components.update_layout(
#         barmode='stack',
#         title='Composición del Indicador de Riesgo',
#         xaxis_title='Contribución al Riesgo Total',
#         height=200,
#         showlegend=True,
#         legend=dict(orientation="v", yanchor="top",
#                     y=1, xanchor="left", x=1.05),
#         paper_bgcolor=theme_styles['plot_bg'],
#         plot_bgcolor=theme_styles['plot_bg'],
#         font={'color': theme_styles['text_color'],
#               'family': 'Inter', 'size': 11},
#         margin=dict(t=50, b=30, l=100, r=200),
#         xaxis=dict(range=[0, 1], tickformat='.2f')
#     )

#     return html.Div([
#         # Risk level badge
#         html.Div([
#             html.Div([
#                 html.H2(risk_level, style={
#                     'color': risk_color,
#                     'margin': '0',
#                     'fontWeight': 'bold'
#                 }),
#                 html.P(risk_message, style={
#                     'color': theme_styles['text_color'],
#                     'margin': '5px 0 0 0',
#                     'fontSize': '14px',
#                     'opacity': '0.8'
#                 })
#             ], style={'textAlign': 'center'})
#         ], style={
#             'backgroundColor': theme_styles['paper_color'],
#             'padding': '20px',
#             'borderRadius': '10px',
#             'marginBottom': '20px',
#             'border': f'3px solid {risk_color}'
#         }),

#         # Main gauge
#         dcc.Graph(figure=fig_gauge, style={'marginBottom': '20px'}),

#         # Components breakdown
#         dcc.Graph(figure=fig_components, style={'marginBottom': '20px'}),

#         # Key metrics table
#         html.Div([
#             html.H4("Métricas Clave", style={'marginBottom': '15px'}),
#             html.Div([
#                 create_metric_card("Cartera Total", format_currency_int(
#                     indicator_data['total_portfolio']), theme_styles),
#                 create_metric_card("Cartera Vencida", format_currency_int(
#                     indicator_data['overdue_portfolio']), theme_styles),
#                 create_metric_card(
#                     "Tasa de Mora", f"{indicator_data['overdue_rate']:.1f}%", theme_styles),
#                 create_metric_card(
#                     "Días Promedio Mora", f"{indicator_data['avg_days_overdue']:.0f}", theme_styles),
#                 create_metric_card(
#                     "Eficiencia Recaudo", f"{indicator_data['collection_efficiency']:.1f}%", theme_styles),
#                 create_metric_card(
#                     "DSO", f"{indicator_data['dso']:.0f} días", theme_styles),
#                 create_metric_card("Clientes", str(
#                     indicator_data['client_count']), theme_styles),
#                 create_metric_card(
#                     "Concentración", f"{indicator_data['risk_concentration']:.1f}%", theme_styles)
#             ], style={
#                 'display': 'grid',
#                 'gridTemplateColumns': 'repeat(4, 1fr)',
#                 'gap': '15px'
#             })
#         ])
#     ])


# def create_metric_card(title, value, theme_styles):
#     """
#     Helper function to create a small metric card
#     """
#     return html.Div([
#         html.P(title, style={
#             'margin': '0 0 5px 0',
#             'fontSize': '12px',
#             'color': theme_styles['text_color'],
#             'opacity': '0.7'
#         }),
#         html.H4(value, style={
#             'margin': '0',
#             'fontSize': '18px',
#             'fontWeight': 'bold',
#             'color': theme_styles['text_color']
#         })
#     ], style={
#         'backgroundColor': theme_styles['paper_color'],
#         'padding': '15px',
#         'borderRadius': '8px',
#         'border': f'1px solid {theme_styles["line_color"]}',
#         'textAlign': 'center'
#     })

# Agregar estos callbacks al final de cartera.py (página)

@callback(
    [Output('cartera-indicador-container', 'children'),
     Output('cartera-indicador-section', 'style')],
    [Input('session-store', 'data'),
     Input('cartera-dropdown-vendedor', 'value'),
     Input('cartera-data-store', 'data'),
     Input('cartera-theme-store', 'data')]
)
def update_indicador_section(session_data, dropdown_value, data_store, theme):
    """
    Update portfolio indicator section based on user permissions
    """
    from utils import can_see_all_vendors, get_user_vendor_filter

    theme_styles = get_theme_styles(theme)

    # Base style for the section
    section_style = {
        'borderRadius': '16px',
        'padding': '24px',
        'marginBottom': '24px',
        'boxShadow': theme_styles['card_shadow'],
        'width': '100%',
        'backgroundColor': theme_styles['paper_color'],
        'color': theme_styles['text_color']
    }

    try:
        if not session_data:
            return html.Div("No hay sesión activa"), section_style

        is_admin = can_see_all_vendors(session_data)

        if is_admin:
            # Para administradores: mostrar tabla con todos los vendedores
            indicators = analyzer.calculate_portfolio_indicator('Todos')

            if not indicators:
                return html.Div("No hay datos de indicadores disponibles"), section_style

            # Crear tabla de indicadores
            table_content = create_indicators_table(
                indicators, theme_styles, theme)
            return table_content, section_style

        else:
            # Para vendedores: mostrar su propio indicador con gráfico
            vendor = get_user_vendor_filter(session_data)
            indicator_data = analyzer.calculate_portfolio_indicator(vendor)

            if not indicator_data:
                return html.Div("No hay datos de indicador disponibles"), section_style

            # Crear visualización del indicador individual
            vendor_content = create_vendor_indicator_view(
                indicator_data, theme_styles, theme)
            return vendor_content, section_style

    except Exception as e:
        print(f"Error en update_indicador_section: {e}")
        return html.Div(f"Error cargando indicadores"), section_style


def create_indicators_table(indicators, theme_styles, theme):
    """
    Create a table showing all vendors' indicators for admin view with percentile-based categorization
    """
    if not indicators:
        return html.Div("No hay datos disponibles")

    # Header row
    header_style = {
        'backgroundColor': '#2c3e50' if theme == 'light' else '#1a1a1a',
        'color': 'white',
        'padding': '12px 8px',
        'fontWeight': 'bold',
        'fontSize': '12px',
        'fontFamily': 'Inter',
        'textAlign': 'center',
        'border': '1px solid #34495e'
    }

    cell_style = {
        'padding': '10px 8px',
        'fontSize': '11px',
        'fontFamily': 'Inter',
        'textAlign': 'center',
        'border': '1px solid #dee2e6'
    }

    # Create table headers
    headers = [
        html.Th("#", style={**header_style, 'width': '40px'}),
        html.Th("Vendedor", style={**header_style, 'width': '180px'}),
        html.Th("Indicador Ajustado", style={
                **header_style, 'width': '130px'}),
        html.Th("Categoría", style={**header_style, 'width': '90px'}),
        html.Th("Percentil", style={**header_style, 'width': '70px'}),
        html.Th("Cartera Total", style={**header_style, 'width': '100px'}),
        html.Th("% Mora", style={**header_style, 'width': '70px'}),
        html.Th("WOF", style={**header_style, 'width': '60px'}),
        html.Th("DSO", style={**header_style, 'width': '60px'}),
        html.Th("Efic. %", style={**header_style, 'width': '70px'}),
        html.Th("Conc. %", style={**header_style, 'width': '70px'})
    ]

    rows = [html.Tr(headers)]

    # Color mapping for categories
    category_colors = {
        'CRÍTICO': {'bg': '#ffebee' if theme == 'light' else '#4a2020', 'text': '#8b0000'},
        'ALTO': {'bg': '#ffebee' if theme == 'light' else '#4a2d2d', 'text': '#e74c3c'},
        'MEDIO': {'bg': '#fff3e0' if theme == 'light' else '#4a3520', 'text': '#f39c12'},
        'MODERADO': {'bg': '#fffbeb' if theme == 'light' else '#3d3a28', 'text': '#f1c40f'},
        'BAJO': {'bg': '#e8f5e9' if theme == 'light' else '#2d4a35', 'text': '#27ae60'}
    }

    # Statistics for summary
    stats = {
        'CRÍTICO': 0,
        'ALTO': 0,
        'MEDIO': 0,
        'MODERADO': 0,
        'BAJO': 0
    }

    # Add data rows
    for idx, vendor in enumerate(indicators[:25], 1):  # Limit to top 25
        # Get risk values
        adjusted_risk = vendor.get('adjusted_risk', vendor['risk_indicator'])
        original_risk = vendor['risk_indicator']
        category = vendor.get('risk_category', 'SIN CATEGORÍA')
        percentile = vendor.get('percentile', None)

        # Update statistics
        if category in stats:
            stats[category] += 1

        # Get colors for category
        colors = category_colors.get(
            category, {'bg': '#f5f5f5', 'text': '#333333'})

        row_style = {**cell_style, 'backgroundColor': colors['bg']}

        # Create risk indicator cell with visual elements
        risk_indicator_cell = html.Td([
            html.Div([
                # Adjusted risk value
                html.Span(f"{adjusted_risk:.3f}", style={
                    'fontWeight': 'bold',
                    'color': colors['text'],
                    'fontSize': '13px'
                }),
                # Original risk in smaller text
                html.Span(f" ({original_risk:.3f})", style={
                    'fontSize': '10px',
                    'opacity': '0.7',
                    'marginLeft': '4px'
                })
            ]),
            # Progress bar for visual representation
            html.Div([
                html.Div(style={
                    'width': f'{adjusted_risk * 100}%',
                    'height': '4px',
                    'backgroundColor': colors['text'],
                    'borderRadius': '2px',
                    'marginTop': '4px'
                })
            ], style={
                'width': '100%',
                'height': '4px',
                'backgroundColor': '#ecf0f1',
                'borderRadius': '2px',
                'marginTop': '4px'
            })
        ], style=row_style)

        # Category badge cell
        category_cell = html.Td(
            html.Span(category, style={
                'fontSize': '10px',
                'backgroundColor': colors['text'],
                'color': 'white',
                'padding': '3px 8px',
                'borderRadius': '12px',
                'fontWeight': 'bold'
            }),
            style=row_style
        )

        # Percentile cell
        percentile_text = f"P{percentile}" if percentile is not None else "-"
        percentile_cell = html.Td(percentile_text, style={
            **row_style,
            'fontWeight': 'bold',
            'color': colors['text']
        })

        row = html.Tr([
            html.Td(str(idx), style={**row_style, 'fontWeight': 'bold'}),
            html.Td(vendor['vendor'][:30], style={
                    **row_style, 'textAlign': 'left', 'fontWeight': '600'}),
            risk_indicator_cell,
            category_cell,
            percentile_cell,
            html.Td(format_currency_int(
                vendor['total_portfolio']), style=row_style),
            html.Td(f"{vendor['overdue_rate']:.1f}%", style={
                **row_style,
                'color': '#e74c3c' if vendor['overdue_rate'] > 50 else theme_styles['text_color']
            }),
            html.Td(f"{vendor['wof']:.0f}", style=row_style),
            html.Td(f"{vendor['dso']:.0f}", style=row_style),
            html.Td(f"{vendor['collection_efficiency']:.1f}%", style={
                **row_style,
                'color': '#27ae60' if vendor['collection_efficiency'] > 70 else '#e74c3c'
            }),
            html.Td(f"{vendor['risk_concentration']:.1f}%", style={
                **row_style,
                'color': '#e74c3c' if vendor['risk_concentration'] > 60 else theme_styles['text_color']
            })
        ])

        rows.append(row)

    # Calculate average adjusted risk
    avg_adjusted = sum(v.get('adjusted_risk', v['risk_indicator'])
                       for v in indicators) / len(indicators) if indicators else 0
    avg_original = sum(v['risk_indicator']
                       for v in indicators) / len(indicators) if indicators else 0

    # Get percentile thresholds if available
    percentile_info = None
    if indicators and indicators[0].get('percentile_thresholds'):
        thresholds = indicators[0]['percentile_thresholds']
        percentile_info = html.Div([
            html.H5("Umbrales de Percentiles", style={'marginBottom': '10px'}),
            html.Div([
                html.Span(f"P25: {thresholds.get('p25', 0):.3f}", style={
                    'margin': '0 15px',
                    'padding': '5px 10px',
                    'backgroundColor': '#27ae60',
                    'color': 'white',
                    'borderRadius': '15px',
                    'fontSize': '12px'
                }),
                html.Span(f"P50: {thresholds.get('p50', 0):.3f}", style={
                    'margin': '0 15px',
                    'padding': '5px 10px',
                    'backgroundColor': '#f1c40f',
                    'color': 'white',
                    'borderRadius': '15px',
                    'fontSize': '12px'
                }),
                html.Span(f"P75: {thresholds.get('p75', 0):.3f}", style={
                    'margin': '0 15px',
                    'padding': '5px 10px',
                    'backgroundColor': '#f39c12',
                    'color': 'white',
                    'borderRadius': '15px',
                    'fontSize': '12px'
                }),
                html.Span(f"P90: {thresholds.get('p90', 0):.3f}", style={
                    'margin': '0 15px',
                    'padding': '5px 10px',
                    'backgroundColor': '#e74c3c',
                    'color': 'white',
                    'borderRadius': '15px',
                    'fontSize': '12px'
                })
            ])
        ], style={
            'marginBottom': '20px',
            'padding': '15px',
            'backgroundColor': theme_styles['paper_color'],
            'borderRadius': '8px',
            'border': f'1px solid {theme_styles["line_color"]}',
            'textAlign': 'center'
        })

    return html.Div([
        # Summary statistics with categories
        html.Div([
            html.Div([
                html.H4("Resumen de Indicadores",
                        style={'marginBottom': '15px'}),
                html.Div([
                    html.Div([
                        html.Span("Total Vendedores: ", style={
                                  'fontWeight': 'bold'}),
                        html.Span(f"{len(indicators)}")
                    ], style={'display': 'inline-block', 'marginRight': '30px'}),
                    html.Div([
                        html.Span("Riesgo Promedio (Ajustado): ",
                                  style={'fontWeight': 'bold'}),
                        html.Span(
                            f"{avg_adjusted:.3f} (Original: {avg_original:.3f})")
                    ], style={'display': 'inline-block'})
                ], style={'marginBottom': '15px'}),

                # Category distribution
                html.Div([
                    html.Span("Distribución: ", style={
                              'fontWeight': 'bold', 'marginRight': '15px'}),
                    *[html.Span(f"{cat}: {count}", style={
                        'margin': '0 10px',
                        'padding': '5px 10px',
                        'backgroundColor': category_colors[cat]['text'],
                        'color': 'white',
                        'borderRadius': '15px',
                        'fontSize': '12px',
                        'fontWeight': 'bold'
                    }) for cat, count in stats.items() if count > 0]
                ])
            ])
        ], style={
            'marginBottom': '20px',
            'padding': '20px',
            'backgroundColor': theme_styles['paper_color'],
            'borderRadius': '8px',
            'border': f'1px solid {theme_styles["line_color"]}'
        }),

        # Percentile thresholds if available
        percentile_info if percentile_info else html.Div(),

        # Table
        html.Div([
            html.Table(rows, style={
                'width': '100%',
                'borderCollapse': 'collapse',
                'fontSize': '12px',
                'fontFamily': 'Inter'
            })
        ], style={
            'maxHeight': '600px',
            'overflowY': 'auto',
            'overflowX': 'auto',
            'border': f'2px solid {theme_styles["line_color"]}',
            'borderRadius': '8px',
            'boxShadow': '0 4px 8px rgba(0,0,0,0.1)'
        })
    ])


def create_vendor_indicator_view(indicator_data, theme_styles, theme):
    """
    Create a visual representation of vendor's indicator with breakdown
    """
    if not indicator_data:
        return html.Div("No hay datos disponibles")

    # Use adjusted risk if available, otherwise use base risk
    risk = indicator_data.get(
        'adjusted_risk', indicator_data['risk_indicator'])
    category = indicator_data.get('risk_category', 'SIN CATEGORÍA')
    percentile = indicator_data.get('percentile', None)

    # Determine risk level and color based on category
    risk_colors = {
        'CRÍTICO': '#8b0000',  # Dark red
        'ALTO': '#e74c3c',     # Red
        'MEDIO': '#f39c12',    # Orange
        'MODERADO': '#f1c40f',  # Yellow
        'BAJO': '#27ae60'      # Green
    }

    risk_messages = {
        'CRÍTICO': 'Situación crítica - Acción inmediata requerida',
        'ALTO': 'Riesgo alto - Requiere atención urgente',
        'MEDIO': 'Riesgo medio - Monitoreo constante necesario',
        'MODERADO': 'Riesgo moderado - Seguimiento regular',
        'BAJO': 'Riesgo bajo - Desempeño satisfactorio'
    }

    risk_color = risk_colors.get(category, '#95a5a6')
    risk_message = risk_messages.get(category, 'Evaluando...')

    # Create gauge chart for main indicator
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=risk,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'suffix': f"<br><span style='font-size:12px'>{category}</span>"},
        title={'text': f"Indicador de Riesgo<br><span style='font-size:14px'>{indicator_data['vendor']}</span>",
               'font': {'size': 16, 'family': 'Inter'}},
        delta={'reference': 0.5, 'increasing': {
            'color': "red"}, 'decreasing': {'color': "green"}},
        gauge={
            'axis': {'range': [None, 1], 'tickwidth': 1, 'tickcolor': theme_styles['text_color']},
            'bar': {'color': risk_color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': theme_styles['line_color'],
            'steps': [
                {'range': [0, 0.25], 'color': 'rgba(39, 174, 96, 0.15)'},
                {'range': [0.25, 0.45], 'color': 'rgba(241, 196, 15, 0.15)'},
                {'range': [0.45, 0.70], 'color': 'rgba(243, 156, 18, 0.15)'},
                {'range': [0.70, 0.85], 'color': 'rgba(231, 76, 60, 0.15)'},
                {'range': [0.85, 1], 'color': 'rgba(139, 0, 0, 0.15)'}
            ],
            'threshold': {
                'line': {'color': "darkred", 'width': 4},
                'thickness': 0.75,
                'value': 0.85
            }
        }
    ))

    fig_gauge.update_layout(
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': theme_styles['text_color'], 'family': 'Inter'},
        margin=dict(t=50, b=30, l=30, r=30)
    )

    # Create breakdown chart for components (vertical bars)
    components = indicator_data.get('component_risks', {})

    # Component names and weights for display
    component_info = [
        ('Tasa de Mora', 'overdue_rate_risk', 0.25,
         indicator_data.get('overdue_rate', 0)),
        ('WOF', 'wof_risk', 0.25, indicator_data.get('wof', 0)),
        ('Efic. Recaudo', 'collection_risk', 0.15,
         indicator_data.get('collection_efficiency', 0)),
        ('DSO', 'dso_risk', 0.20, indicator_data.get('dso', 0)),
        ('Concentración', 'concentration_risk', 0.15,
         indicator_data.get('risk_concentration', 0))
    ]

    # Prepare data for vertical bar chart
    fig_components = go.Figure()

    x_labels = []
    y_values = []
    colors = []
    hover_texts = []
    text_labels = []

    for name, key, weight, metric_value in component_info:
        risk_value = components.get(key, 0)
        weighted_contribution = risk_value * weight

        # Determine color based on risk value
        if risk_value >= 0.7:
            color = 'rgba(231, 76, 60, 0.7)'
        elif risk_value >= 0.4:
            color = 'rgba(243, 156, 18, 0.7)'
        else:
            color = 'rgba(39, 174, 96, 0.7)'

        x_labels.append(f"{name}<br>{weight*100:.0f}%")
        y_values.append(weighted_contribution)
        colors.append(color)
        text_labels.append(f"{weighted_contribution:.3f}")

        hover_texts.append(
            f'<b>{name}</b><br>' +
            f'Peso: {weight*100:.0f}%<br>' +
            f'Riesgo: {risk_value:.3f}<br>' +
            f'Contribución: {weighted_contribution:.3f}<br>' +
            f'Valor métrica: {metric_value:.1f}'
        )

    fig_components.add_trace(go.Bar(
        x=x_labels,
        y=y_values,
        marker=dict(
            color=colors,
            line=dict(color='rgba(0,0,0,0.3)', width=1)
        ),
        text=text_labels,
        textposition='outside',
        hovertemplate='%{hovertext}<extra></extra>',
        hovertext=hover_texts
    ))

    fig_components.update_layout(
        title='Composición del Indicador',
        yaxis_title='Contribución al Riesgo',
        height=350,
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0.02)',
        font={'color': theme_styles['text_color'],
              'family': 'Inter', 'size': 11},
        margin=dict(t=50, b=60, l=60, r=30),
        yaxis=dict(range=[0, max(y_values) * 1.2]
                   if y_values else [0, 1], tickformat='.3f'),
        xaxis=dict(tickangle=0)
    )

    # Percentile information if available
    percentile_info = None
    if percentile is not None and indicator_data.get('percentile_thresholds'):
        thresholds = indicator_data['percentile_thresholds']
        percentile_info = html.Div([
            html.P(f"Percentil: {percentile}°", style={
                'fontSize': '14px',
                'fontWeight': 'bold',
                'margin': '0'
            }),
            html.P(f"P25: {thresholds.get('p25', 0):.3f} | P50: {thresholds.get('p50', 0):.3f} | P75: {thresholds.get('p75', 0):.3f} | P90: {thresholds.get('p90', 0):.3f}", style={
                'fontSize': '11px',
                'opacity': '0.7',
                'margin': '5px 0 0 0'
            })
        ], style={
            'textAlign': 'center',
            'padding': '10px',
            'backgroundColor': theme_styles['paper_color'],
            'borderRadius': '8px',
            'border': f'1px solid {theme_styles["line_color"]}',
            'marginBottom': '15px'
        })

    return html.Div([
        # Risk level badge
        html.Div([
            html.Div([
                html.H2(category, style={
                    'color': risk_color,
                    'margin': '0',
                    'fontWeight': 'bold'
                }),
                html.P(risk_message, style={
                    'color': theme_styles['text_color'],
                    'margin': '5px 0 0 0',
                    'fontSize': '14px',
                    'opacity': '0.8'
                })
            ], style={'textAlign': 'center'})
        ], style={
            'backgroundColor': theme_styles['paper_color'],
            'padding': '20px',
            'borderRadius': '10px',
            'marginBottom': '20px',
            'border': f'3px solid {risk_color}'
        }),

        # Percentile information if available
        percentile_info if percentile_info else html.Div(),

        # Charts side by side
        html.Div([
            html.Div([
                dcc.Graph(figure=fig_gauge, style={'height': '100%'})
            ], style={
                'width': '48%',
                'display': 'inline-block',
                'verticalAlign': 'top',
                'backgroundColor': theme_styles['paper_color'],
                'borderRadius': '8px',
                'padding': '10px'
            }),

            html.Div([
                dcc.Graph(figure=fig_components, style={'height': '100%'})
            ], style={
                'width': '48%',
                'display': 'inline-block',
                'verticalAlign': 'top',
                'marginLeft': '4%',
                'backgroundColor': theme_styles['paper_color'],
                'borderRadius': '8px',
                'padding': '10px'
            })
        ], style={'marginBottom': '20px'}),

        # Key metrics table below
        html.Div([
            html.H4("Métricas Detalladas", style={
                    'marginBottom': '15px', 'textAlign': 'center'}),
            html.Div([
                create_metric_card("Cartera Total", format_currency_int(
                    # , '#3498db'),
                    indicator_data['total_portfolio']), theme_styles),
                create_metric_card("Cartera Vencida", format_currency_int(
                    # , '#e74c3c'),
                    indicator_data['overdue_portfolio']), theme_styles),
                create_metric_card(
                    # , '#e67e22'),
                    "Tasa de Mora", f"{indicator_data['overdue_rate']:.1f}%", theme_styles),
                create_metric_card(
                    # , '#9b59b6'),
                    "WOF (días)", f"{indicator_data['wof']:.1f}", theme_styles),
                create_metric_card(
                    # , '#e74c3c'),
                    "Promedio Mora", f"{indicator_data['avg_days_overdue']:.0f} días", theme_styles),
                create_metric_card(
                    # , '#27ae60'),
                    "Efic. Recaudo", f"{indicator_data['collection_efficiency']:.1f}%", theme_styles),
                create_metric_card(
                    # , '#16a085'),
                    "DSO", f"{indicator_data['dso']:.0f} días", theme_styles),
                create_metric_card(
                    # , '#f39c12'),
                    "Concentración", f"{indicator_data['risk_concentration']:.1f}%", theme_styles),
                create_metric_card("Clientes", str(
                    # , '#34495e'),
                    indicator_data['client_count']), theme_styles),
                create_metric_card("Facturas", str(
                    # , '#7f8c8d'),
                    indicator_data['invoice_count']), theme_styles),
                create_metric_card("Ventas", format_currency_int(
                    # , '#2ecc71'),
                    indicator_data['total_sales']), theme_styles),
                create_metric_card("Recaudos", format_currency_int(
                    # , '#3498db')
                    indicator_data['total_collections']), theme_styles),
            ], style={
                'display': 'grid',
                'gridTemplateColumns': 'repeat(4, 1fr)',
                'gap': '15px'
            })
        ])
    ])


def create_metric_card(title, value, theme_styles, color='#3498db'):
    """
    Helper function to create a small metric card with color accent
    """
    return html.Div([
        html.Div(style={
            'height': '4px',
            'backgroundColor': color,
            'borderRadius': '4px 4px 0 0',
            'marginBottom': '10px'
        }),
        html.P(title, style={
            'margin': '0 0 5px 0',
            'fontSize': '11px',
            'color': theme_styles['text_color'],
            'opacity': '0.7',
            'fontWeight': '500'
        }),
        html.H4(value, style={
            'margin': '0',
            'fontSize': '16px',
            'fontWeight': 'bold',
            'color': theme_styles['text_color']
        })
    ], style={
        'backgroundColor': theme_styles['paper_color'],
        'padding': '0 15px 15px 15px',
        'borderRadius': '8px',
        'border': f'1px solid {theme_styles["line_color"]}',
        'textAlign': 'center',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'
    })


def create_metric_card(title, value, theme_styles):
    """
    Helper function to create a small metric card
    """
    return html.Div([
        html.P(title, style={
            'margin': '0 0 5px 0',
            'fontSize': '12px',
            'color': theme_styles['text_color'],
            'opacity': '0.7'
        }),
        html.H4(value, style={
            'margin': '0',
            'fontSize': '18px',
            'fontWeight': 'bold',
            'color': theme_styles['text_color']
        })
    ], style={
        'backgroundColor': theme_styles['paper_color'],
        'padding': '15px',
        'borderRadius': '8px',
        'border': f'1px solid {theme_styles["line_color"]}',
        'textAlign': 'center'
    })

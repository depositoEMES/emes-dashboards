import time
from datetime import datetime

import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.graph_objects as go
import pandas as pd

from components import (
    create_metrics_grid, 
    create_empty_metrics, 
    METRIC_COLORS
)
from analyzers import TransferenciasAnalyzer
from utils import (
    format_currency_int, 
    get_theme_styles, 
    get_dropdown_style,
    get_ultimos_3_meses
)

analyzer = TransferenciasAnalyzer()

# Carga inicial opcional (se recarga on-demand)
try:
    df = analyzer.load_data_from_firebase()
except Exception as e:
    print(
        f"⚠️ [TransferenciasPage] Carga inicial falló (se recargará on-demand): {e}")
    df = pd.DataFrame()
         
def get_user_display_name(session_data):
    """
    Obtener nombre del usuario para mostrar en el título
    """
    try:
        if not session_data:
            return None
        
        from utils import can_see_all_vendors, get_user_vendor_filter
        
        if can_see_all_vendors(session_data):
            return None  # Admin ve todos los vendedores
        else:
            vendor = get_user_vendor_filter(session_data)
            return vendor if vendor != 'Todos' else None
    except Exception as e:
        print(f"Error en get_user_display_name: {e}")
        return None


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
                    id='transferencias-titulo-principal',
                    className="main-title",
                    children="Transferencias"
                ),
                html.P(
                    id='transferencias-subtitulo',
                    className="main-subtitle",
                    children="Análisis completo de ventas y transferencias"
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
                    id="transferencias-theme-toggle",
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
        ], className="top-header", id='transferencias-header-container', style={
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'space-between',
            'borderRadius': '20px',
            'padding': '32px 40px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'position': 'relative',
            'minHeight': '80px'
        }),

        html.Div([
            html.Div([
                html.Label("Transferencista:",
                           id='transferencias-dropdown-vendedor-label',
                           style={
                               'fontWeight': '600',
                               'fontSize': '14px',
                               'marginBottom': '8px',
                               'display': 'block'
                           }),
                dcc.Dropdown(
                    id='transferencias-dropdown-vendedor',
                    options=[{'label': v, 'value': v} for v in analyzer.vendedores_list],
                    value='Todos',
                    placeholder="Seleccionar transferencista...",
                    clearable=True,
                    style={
                        'height': '44px',
                        'borderRadius': '12px',
                        'fontSize': '14px'
                    },
                    maxHeight=150
                )
            ], style={
                'display': 'flex',
                'flexDirection': 'column',
                'flex': '1',
                'minWidth': '250px'
            }, id='transferencias-dropdown-vendedor-container'),

            html.Div([
                html.Label("Período:",
                           style={
                               'fontWeight': '600',
                               'fontSize': '14px',
                               'marginBottom': '8px',
                               'display': 'block'
                           }),
                dcc.Dropdown(
                    id='transferencias-dropdown-mes',
                    options=[{'label': m, 'value': m} for m in analyzer.meses_list],
                    value=datetime.now().strftime("%Y-%m"),
                    placeholder="Seleccionar período...",
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
                'minWidth': '200px'
            }),

            html.Div([
                html.Button(
                    "🔄 Actualizar Datos",
                    id="transferencias-btn-actualizar",
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
                'alignItems': 'flex-end'
            })
        ], id='transferencias-controls-container', style={
            'display': 'flex',
            'gap': '24px',
            'alignItems': 'stretch',
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'flexWrap': 'wrap'
        }),

        html.Div(id="transferencias-metrics-cards", children=[], style={'marginBottom': '24px'}),

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
        ], id='transferencias-row1-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

        html.Div([
            html.H3("Evolución Ventas por Cliente", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
            html.Div([
                # Dropdown de cliente
                html.Div([
                    html.Label("Cliente:", style={
                            'fontWeight': 'bold', 'marginBottom': '8px', 'fontFamily': 'Inter', 'fontSize': '14px'}),
                    dcc.Dropdown(
                        id='transferencias-dropdown-cliente',
                        options=[{'label': 'Seleccione un cliente',
                                'value': 'Seleccione un cliente'}],
                        value='Seleccione un cliente',
                        style={'fontFamily': 'Inter', 'height': '44px'},
                        className='custom-dropdown'
                    )
                ], style={
                    'width': '70%',
                    'display': 'inline-block',
                    'marginRight': '3%',
                    'verticalAlign': 'top'
                }),
                
                # Dropdown de tipo de evolución
                html.Div([
                    html.Label("Tipo:", style={
                            'fontWeight': 'bold', 'marginBottom': '8px', 'fontFamily': 'Inter', 'fontSize': '14px'}),
                    dcc.Dropdown(
                        id='transferencias-dropdown-tipo-evolucion',
                        options=[
                            {'label': 'Diario', 'value': 'diario'},
                            {'label': 'Mensual', 'value': 'mensual'}
                        ],
                        value='diario',
                        style={'fontFamily': 'Inter', 'height': '44px'},
                        className='custom-dropdown'
                    )
                ], style={
                    'width': '25%',
                    'display': 'inline-block',
                    'verticalAlign': 'top'
                })
            ], style={'marginBottom': '20px'}),
            
            dcc.Graph(id='transferencias-grafico-evolucion-cliente')
        ], id='transferencias-row1-5-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

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
        ], id='transferencias-row2-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

        html.Div([
            html.H3("Ventas por Cliente - Análisis Temporal", style={
                'textAlign': 'center', 
                'marginBottom': '25px', 
                'fontFamily': 'Inter'
            }),
            
            # Contenedor de filtros - AHORA CON DOS SLIDERS
            html.Div([
                # Filtro de meses (izquierda)
                html.Div([
                    html.Label("Filtrar por Meses:", style={
                        'fontWeight': 'bold',
                        'marginBottom': '10px',
                        'fontFamily': 'Inter',
                        'fontSize': '14px'
                    }),
                    dcc.RangeSlider(
                        id='transferencias-filtro-meses',
                        min=1,
                        max=datetime.now().month,
                        step=1,
                        value=get_ultimos_3_meses(),  # Por defecto últimos 3 meses
                        marks={
                            1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr',
                            5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago',
                            9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
                        },
                        tooltip={"placement": "bottom", "always_visible": True},
                        allowCross=False
                    )
                ], style={
                    'width': '48%',
                    'display': 'inline-block',
                    'marginRight': '4%'
                }),
                
                # Filtro de monto de ventas (derecha)
                html.Div([
                    html.Label("Filtrar por Monto de Ventas:", style={
                        'fontWeight': 'bold',
                        'marginBottom': '10px',
                        'fontFamily': 'Inter',
                        'fontSize': '14px'
                    }),
                    dcc.RangeSlider(
                        id='transferencias-filtro-monto-ventas',
                        # min, max y marks se configurarán dinámicamente en el callback
                        min=0,
                        max=1000000,  # Valor inicial, se actualizará
                        step=50000,
                        value=[0, 1000000],  # Por defecto muestra todos
                        marks={},  # Se configurará dinámicamente
                        allowCross=False,
                        tooltip={
                            "placement": "bottom", 
                            "always_visible": True,
                            "style": {"color": "white", "fontSize": "12px"},
                            "transform": "formatCurrency"
                        },
                    )
                ], style={
                    'width': '48%',
                    'display': 'inline-block'
                })
            ], style={
                'marginBottom': '20px',
                'padding': '15px',
                'borderRadius': '8px',
                'border': '1px solid #e5e7eb'
            }),
            
            dcc.Graph(id='transferencias-treemap-unificado', style={'height': '650px'})
            
        ], id='transferencias-row2-5-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

        html.Div([
            html.H3("Clientes por Días Sin Venta", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
            html.P("(Clientes que no han comprado en 7+ días - Tamaño por total de ventas históricas)", style={
                   'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '12px', 'margin': '0 0 20px 0'}),
            dcc.Graph(id='transferencias-treemap-dias-sin-venta')
        ], id='transferencias-row-nueva-treemap', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

        # Fila 4: Top Clientes
        html.Div([
            html.H3("Top 10 - Clientes", style={'textAlign': 'center',
                    'marginBottom': '20px', 'fontFamily': 'Inter'}),
            dcc.Graph(id='transferencias-top-clientes')
        ], id='transferencias-row-top-clientes', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),
        
        # NUEVA FILA: Heatmap de Variaciones Mensuales
        html.Div([
            html.H3("Variaciones Mensuales de Clientes", style={
                'textAlign': 'center', 
                'marginBottom': '25px', 
                'fontFamily': 'Inter'
            }),
            
            # Contenedor de filtros del heatmap
            html.Div([
                html.Div([
                    html.Label("Período de Análisis:", style={
                        'fontWeight': 'bold',
                        'marginBottom': '10px',
                        'fontFamily': 'Inter',
                        'fontSize': '14px'
                    }),
                    dcc.RangeSlider(
                        id='transferencias-heatmap-rango-meses',
                        min=1,
                        max=datetime.now().month,
                        step=1,
                        value=[1, datetime.now().month],
                        marks={
                            1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr',
                            5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago',
                            9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
                        },
                        tooltip={"placement": "bottom", "always_visible": True},
                        allowCross=False
                    )
                ], style={
                    'marginBottom': '20px',
                    'width': '100%'
                }),
                
                # Fila 2: Filtros de selección
                html.Div([
                    # Botones de ranking
                    html.Div([
                        html.Label("Ranking:", style={
                            'fontWeight': 'bold',
                            'marginBottom': '10px',
                            'fontFamily': 'Inter',
                            'fontSize': '14px',
                            'display': 'block'
                        }),
                        html.Div([
                            html.Button("📈 Primeros 10", id="transferencias-heatmap-top10", 
                                    className="heatmap-filter-btn active", n_clicks=0,
                                    style={'marginRight': '10px'}),
                            html.Button("📉 Últimos 10", id="transferencias-heatmap-bottom10", 
                                    className="heatmap-filter-btn", n_clicks=0)
                        ])
                    ], style={
                        'width': '48%',
                        'display': 'inline-block',
                        'verticalAlign': 'top',
                        'paddingRight': '2%'
                    }),
                    
                    # Selector de clientes específicos
                    html.Div([
                        html.Label("Comparar Clientes Específicos:", style={
                            'fontWeight': 'bold',
                            'marginBottom': '10px',
                            'fontFamily': 'Inter',
                            'fontSize': '14px',
                            'display': 'block'
                        }),
                        dcc.Dropdown(
                            id='transferencias-heatmap-clientes',
                            options=[],
                            value=[],
                            multi=True,
                            placeholder="Seleccionar hasta 10 clientes...",
                            style={
                                'fontFamily': 'Inter', 
                                'fontSize': '12px',
                                'height': 'auto',
                                'minHeight': '38px'
                            },
                            maxHeight=150
                        )
                    ], style={
                        'width': '50%',
                        'display': 'inline-block',
                        'verticalAlign': 'top'
                    })
                ], style={
                    'width': '100%',
                    'display': 'flex',
                    'alignItems': 'flex-start'
                })
            ], style={
                'marginBottom': '20px',
                'padding': '20px',
                'borderRadius': '8px',
                'border': '1px solid #e5e7eb'
            }),
            
            dcc.Graph(
                id='transferencias-heatmap-variaciones', 
                style={
                    'height': '600px',
                    'overflowY': 'auto',  # Scroll vertical
                    'overflowX': 'auto'   # Scroll horizontal si es necesario
                }
            )
            
        ], id='transferencias-row-heatmap', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),
    ], style={
        'margin': '0 auto',          
        'padding': '0 40px',        
    }),
    
], id='transferencias-main-container', style={
    'width': '100%',
    'minHeight': '100vh',
    'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
    'transition': 'all 0.3s ease',
    'padding': '20px 0',
    'background': 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 25%, #f8fafc 50%, #f1f5f9 100%)',
    'backgroundSize': '400% 400%',
    'animation': 'gradientShift 15s ease infinite'
})


@callback(
    Output('transferencias-data-store', 'data'),
    [Input('transferencias-btn-actualizar', 'n_clicks')],
    prevent_initial_call=True
)
def update_transferencias_data(n_clicks):
    """Callback central para recargar TODOS los datos cuando se presiona actualizar."""
    if n_clicks > 0:
        try:
            start_time = time.time()
            result = analyzer.reload_data()
            load_time = time.time() - start_time

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
            print(f"❌ [transferenciasPage] Error en actualización #{n_clicks}: {e}")
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
    Output('transferencias-metrics-cards', 'children'),
    [Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-dropdown-mes', 'value'),
     Input('transferencias-data-store', 'data'),
     Input('transferencias-theme-store', 'data')]
)
def update_metric_cards(session_data, dropdown_value, mes, data_store, theme):
    """
    Actualizar las metric cards con los datos de transferencias
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        is_dark = theme == 'dark'
        
        # Obtener resumen de datos
        resumen = analyzer.get_resumen_transferencias(vendedor, mes)
        
        # Preparar datos para las cards
        metrics_data = [
            {
                'title': 'Ventas Totales',
                'value': format_currency_int(resumen['total_transferencias']),
                # 'icon': METRIC_ICONS['money'],
                'color': METRIC_COLORS['success'],
                'card_id': 'transferencias-card-ventas-totales'
            },
            {
                'title': 'Ventas Netas',
                'value': format_currency_int(resumen['transferencias_netas']),
                # 'icon': METRIC_ICONS['sales'],
                'color': METRIC_COLORS['primary'],
                'card_id': 'transferencias-card-ventas-netas'
            },
            {
                'title': 'Devoluciones',
                'value': format_currency_int(resumen['total_devoluciones']),
                # 'icon': METRIC_ICONS['trend_down'],
                'color': METRIC_COLORS['danger'],
                'card_id': 'transferencias-card-devoluciones'
            },
            {
                'title': 'Descuentos',
                'value': format_currency_int(resumen['total_descuentos']),
                # 'icon': METRIC_ICONS['percent'],
                'color': METRIC_COLORS['warning'],
                'card_id': 'transferencias-card-descuentos'
            },
            {
                'title': 'Valor Promedio',
                'value': format_currency_int(resumen['ticket_promedio']),
                # 'icon': METRIC_ICONS['trend_up'],
                'color': METRIC_COLORS['purple'],
                'card_id': 'transferencias-card-valor-promedio'
            },
            {
                'title': '# Facturas',
                'value': f"{resumen['num_facturas']:,}",
                # 'icon': METRIC_ICONS['invoice'],
                'color': METRIC_COLORS['indigo'],
                'card_id': 'transferencias-card-num-facturas'
            },
            {
                'title': '# Devoluciones',
                'value': f"{resumen['num_devoluciones']:,}",
                # 'icon': METRIC_ICONS['warning'],
                'color': METRIC_COLORS['orange'],
                'card_id': 'transferencias-card-num-devoluciones'
            },
            {
                'title': 'Clientes',
                'value': f"{resumen['num_clientes']:,}",
                # 'icon': METRIC_ICONS['client'],
                'color': METRIC_COLORS['teal'],
                'card_id': 'transferencias-card-clientes'
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
        print(f"❌ Error actualizando metric cards: {e}")
        # Retornar cards vacías en caso de error
        return create_empty_metrics(is_dark=theme == 'dark', count=8)

@callback(
    [Output('transferencias-filtro-monto-ventas', 'min'),
     Output('transferencias-filtro-monto-ventas', 'max'),
     Output('transferencias-filtro-monto-ventas', 'value'),
     Output('transferencias-filtro-monto-ventas', 'marks'),
     Output('transferencias-filtro-monto-ventas', 'step')],
    [Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-data-store', 'data')]
)
def update_monto_slider_config(session_data, dropdown_value, data_store):
    """
    Configurar dinámicamente el slider de montos según los datos de transferencias disponibles
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        
        # Obtener datos de transferencias para calcular rangos
        df = analyzer.filter_data(vendedor, 'Todos')
        
        # Filtrar solo ventas reales
        ventas_reales = df[df['tipo'].str.contains(
            'Remision|Factura', case=False, na=False)]
        
        if ventas_reales.empty:
            return 0, 1000000, [0, 1000000], {0: '$0', 1000000: '$1M'}, 50000
        
        # Calcular totales por cliente
        resultado = ventas_reales.groupby('cliente_completo').agg({
            'valor_neto': 'sum'
        }).reset_index()
        
        resultado = resultado[resultado['valor_neto'] > 0]
        
        if resultado.empty:
            return 0, 1000000, [0, 1000000], {0: '$0', 1000000: '$1M'}, 50000
        
        # Calcular min y max
        min_monto = 0
        max_monto = int(resultado['valor_neto'].max())
        
        # Redondear max_monto hacia arriba para mejor UX
        if max_monto < 100000:
            max_monto = ((max_monto // 10000) + 1) * 10000  # Redondear a 10k
            step = 5000
        elif max_monto < 1000000:
            max_monto = ((max_monto // 100000) + 1) * 100000  # Redondear a 100k
            step = 25000
        else:
            max_monto = ((max_monto // 1000000) + 1) * 1000000  # Redondear a 1M
            step = 100000
        
        # Crear marcas dinámicas
        num_marks = 5
        mark_step = max_monto // num_marks
        marks = {}
        
        for i in range(num_marks + 1):
            value = i * mark_step
            if value >= 1000000:
                marks[value] = f'${value/1000000:.1f}M'
            elif value >= 1000:
                marks[value] = f'${value/1000:.0f}K'
            else:
                marks[value] = f'${value:,.0f}'
        
        # Valor por defecto: todo el rango
        default_value = [min_monto, max_monto]
        
        return min_monto, max_monto, default_value, marks, step
        
    except Exception as e:
        print(f"❌ Error configurando slider de montos en transferencias: {e}")
        return 0, 1000000, [0, 1000000], {0: '$0', 1000000: '$1M'}, 50000

@callback(
    Output('transferencias-grafico-transferencias-mes', 'figure'),
    [Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-data-store', 'data'),  # 
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
                color='rgba(0, 119, 182, 0.9)',  # Azul moderno
                width=4,
                shape='spline',  # Líneas redondeadas/suaves
                smoothing=1.0    # Máximo suavizado
            ),
            marker=dict(
                size=10,
                color='rgba(0, 119, 182, 1.0)',
                line=dict(color='white', width=3),
                symbol='circle'
            ),
            fill='tozeroy',  # Rellenar hasta el eje Y (área)
            fillcolor='rgba(0, 119, 182, 0.2)',  # Azul claro transparente
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
        print(f"❌ [update_transferencias_mes] Error: {e}")
        return go.Figure()


@callback(
    Output('transferencias-grafico-estacionalidad', 'figure'),
    [Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-dropdown-mes', 'value'),
     Input('transferencias-data-store', 'data'),  # 
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
        pastel_colors_with_borders = \
            [
                {'fill': 'rgba(0, 119, 182, 0.2)', 'border': 'rgb(0, 119, 182)'}, 
                {'fill': 'rgba(0, 180, 216, 0.2)', 'border': 'rgb(0, 180, 216)'},  
                {'fill': 'rgba(144, 224, 239, 0.2)', 'border': 'rgb(144, 224, 239)'},    
                {'fill': 'rgba(202, 240, 248, 0.2)', 'border': 'rgb(202, 240, 248)'},   
                {'fill': 'rgba(2, 62, 138, 0.2)', 'border': 'rgb(2, 62, 138)'},  
                {'fill': 'rgba(3, 4, 94, 0.2)', 'border': 'rgb(3, 4, 94)'},   
                {'fill': 'rgba(211, 211, 211, 0.2)', 'border': 'rgb(211, 211, 211)'}   
            ]

        fill_colors = \
            [
                pastel_colors_with_borders[i % len(pastel_colors_with_borders)]['fill'] 
                for i in range(len(data))
            ]
            
        border_colors = \
            [
                pastel_colors_with_borders[i % len(pastel_colors_with_borders)]['border'] 
                for i in range(len(data))
            ]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=data['dia_semana_es'],
            y=data['valor_neto'],
            marker=dict(
                color=fill_colors,
                line=dict(color=border_colors, width=1),
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
        print(f"❌ [update_estacionalidad] Error: {e}")
        return go.Figure()


@callback(
    Output('transferencias-grafico-zona', 'figure'),
    [Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-dropdown-mes', 'value'),
     Input('transferencias-data-store', 'data'),  # 
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
        bg_colors = []
        border_colors = []

        for val in data['valor_neto']:
            if max_val == min_val:
                normalized = 0.5  # Si todos son iguales, usar color medio
            else:
                normalized = (val - min_val) / (max_val - min_val)

            if normalized <= 0.5:
                red = 255
                green = int(255 * (normalized * 2))
                blue = 0
            else:
                red = int(255 * (2 - normalized * 2))
                green = 255
                blue = 0

            # Add transparency
            bg_colors.append(f'rgba({red}, {green}, {blue}, 0.4)')
            border_colors.append(f'rgba({red}, {green}, {blue}, 0.9)')

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=data['zona'],
            y=data['valor_neto'],
            marker=dict(
                color=bg_colors,
                line=dict(color=border_colors, width=1),
                opacity=0.6
            ),
            text=[format_currency_int(val) for val in data['valor_neto']],
            textposition='outside',
            textfont=dict(size=10, color=theme_styles['text_color']),
            hovertemplate="<b>%{x}</b><br>Ventas: %{customdata[0]}<br>Clientes: %{customdata[1]}<extra></extra>",
            customdata=[[format_currency_int(val), clientes] for val, clientes in zip(
                data['valor_neto'], data['cliente'])]
        ))

        fig.update_layout(
            height=400,
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
     Input('transferencias-data-store', 'data'),  # 
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

        fig = go.Figure(data=[go.Pie(
            labels=data['forma_pago'],
            values=data['valor_neto'],
            hole=.5,
            opacity=0.8,
            textinfo='percent',
            textfont=dict(color=theme_styles['text_color'], size=10),
            marker=dict(
                colors=bg_colors, 
                line=dict(color=border_colors, width=1.5)
            ),
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
        print(f"❌ [update_forma_pago] Error: {e}")
        return go.Figure()

@callback(
    Output('transferencias-treemap-unificado', 'figure'),
    [Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-filtro-meses', 'value'),
     Input('transferencias-filtro-monto-ventas', 'value'),
     Input('transferencias-data-store', 'data'),
     Input('transferencias-theme-store', 'data')]
)
def update_treemap_unificado(
        session_data, 
        dropdown_value, 
        filtro_meses, 
        filtro_monto, 
        data_store, 
        theme):
    """
    Treemap unificado con ventas por cliente - Verde-Rojo sin jerarquía, categorizado por tendencia
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        theme_styles = get_theme_styles(theme)
        
        # Convert month filter
        if filtro_meses and len(filtro_meses) == 2:
            mes_inicio, mes_fin = filtro_meses
        else:
            mes_inicio, mes_fin = 1, 12  # Por defecto todos los meses

        # Get data filtered by months
        data = analyzer.get_ventas_por_rango_meses(
            vendedor, 
            mes_inicio, 
            mes_fin, 
            filtro_monto[0] if filtro_monto and len(filtro_monto) == 2 else None,
            filtro_monto[1] if filtro_monto and len(filtro_monto) == 2 else None
        )
        
        if not data or data.get('total', pd.DataFrame()).empty:
            # Mensaje específico cuando no hay meses seleccionados
            if mes_inicio == mes_fin:
                meses_esp = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
                            7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}
                mensaje = f"No hay datos disponibles para {meses_esp[mes_inicio]}"
            else:
                meses_esp = {1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
                            7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'}
                mensaje = f"No hay datos disponibles para {meses_esp[mes_inicio]} - {meses_esp[mes_fin]}"
                
            fig = go.Figure()
            fig.add_annotation(
                text=mensaje,
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False,
                font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=600,
                paper_bgcolor=theme_styles['plot_bg'],
                plot_bgcolor=theme_styles['plot_bg']
            )
            return fig
        
        resultado_total = data['total']
        resultado_mensual = data['mensual']
        
        # Función para generar colores verde-rojo modernos
        def get_green_red_color(growth_trend=0, alpha=0.8):
            """Generate modern green-red colors based on growth trend"""
            # growth_trend: 1=positive, 0=neutral, -1=negative
            
            if growth_trend > 0:
                # Verde para crecimiento positivo
                return f'rgba(16, 185, 129, {alpha})'   # emerald-500
            elif growth_trend < 0:
                # Rojo para decrecimiento
                return f'rgba(239, 68, 68, {alpha})'    # red-500
            else:
                # Amarillo/naranja para estable
                return f'rgba(245, 158, 11, {alpha})'   # amber-500
        
        # Structure for treemap - SIN JERARQUÍA
        ids = []
        labels = []
        parents = []
        values = []
        colors = []
        border_colors = []
        
        # Format currency helper
        def format_with_dots(val):
            try:
                return f"${val:,.0f}".replace(',', '.')
            except:
                return f"${val}"
        
        # Build treemap structure - SOLO CLIENTES, SIN SEGUNDO NIVEL
        for idx, (_, row) in enumerate(resultado_total.iterrows()):
            cliente = str(row['cliente_completo'])[:80]
            if len(cliente) < len(str(row['cliente_completo'])):
                cliente += "..."
            
            total_ventas = float(row['valor_neto'])
            total_facturas = int(row['documento_id'])
            
            if total_ventas <= 0:
                continue

            cliente_id = f"C{idx}"
            
            # Determinar tendencia de crecimiento basada en datos mensuales
            cliente_mensual = resultado_mensual[
                resultado_mensual['cliente_completo'] == row['cliente_completo']
            ].sort_values('mes_año')
            
            # Calcular tendencia simple
            growth_trend = 0  # Default neutral
            if len(cliente_mensual) >= 2:
                first_month = cliente_mensual.iloc[0]['valor_neto']
                last_month = cliente_mensual.iloc[-1]['valor_neto']
                if last_month > first_month * 1.1:  # 10% más
                    growth_trend = 1  # Positivo
                elif last_month < first_month * 0.9:  # 10% menos
                    growth_trend = -1  # Negativo
            
            # Emoji según tendencia
            trend_emoji = "🟢" if growth_trend > 0 else "🔴" if growth_trend < 0 else "🟡"
            
            # SOLO CLIENTE - SIN HIJOS
            ids.append(cliente_id)
            labels.append(f"{trend_emoji} {cliente}")
            parents.append("")  # Todos son raíz, sin jerarquía
            values.append(total_ventas)
            colors.append(get_green_red_color(growth_trend, alpha=0.4))
            border_colors.append(get_green_red_color(growth_trend, alpha=0.9))
        
        if not ids:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos procesables",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False,
                font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=600,
                paper_bgcolor=theme_styles['plot_bg']
            )
            return fig
        
        # Create custom text labels - SOLO PARA CLIENTES
        text_labels = []
        
        for i, (id_item, label, value) in enumerate(zip(ids, labels, values)):
            # Obtener datos del cliente
            row = resultado_total.iloc[i]
            facturas = int(row['documento_id'])
            
            text_labels.append(
                f"<b>{label}</b><br>{format_with_dots(value)}<br>{facturas} facturas"
            )
        
        # Create treemap - PLANO, SIN JERARQUÍA
        fig = go.Figure(go.Treemap(
            ids=ids,
            labels=labels,
            parents=parents,
            values=values,
            text=text_labels,
            texttemplate="%{text}",
            textposition="middle center",
            textfont=dict(size=11, color=theme_styles['text_color'], family='Inter'),
            marker=dict(
                colors=colors,
                line=dict(width=1.5, color=border_colors)
            ),
            hovertemplate="<br>%{text}<br><extra></extra>",
            branchvalues="total",
            sort=True,
            tiling=dict(
                packing="squarify",  
                pad=3
            )
        ))
        
        # Add period info to title in Spanish
        period_text = ""
        
        if mes_inicio and mes_fin:
            try:
                meses_esp = {
                    1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr',
                    5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago',
                    9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
                }
                
                if mes_inicio == mes_fin:
                    period_text = f" ({meses_esp[mes_inicio]})"
                else:
                    period_text = f" ({meses_esp[mes_inicio]} - {meses_esp[mes_fin]})"
            except:
                pass
        
        fig.update_layout(
            height=650,
            margin=dict(t=80, b=20, l=10, r=10),
            font=dict(family="Inter", color=theme_styles['text_color']),
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            title=dict(
                text=f"Ventas por Cliente - Análisis Temporal{period_text}<br><sub>🟢 Crecimiento positivo | 🟡 Estable | 🔴 Decrecimiento</sub>",
                x=0.5,
                y=0.98,
                xanchor='center',
                yanchor='top',
                font=dict(
                    size=16,
                    color=theme_styles['text_color'],
                    family="Inter"
                )
            )
        )
        
        return fig
        
    except Exception as e:
        print(f"❌ Error en treemap_unificado: {e}")
        import traceback
        traceback.print_exc()
        
        # Error figure
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error cargando treemap:<br>{str(e)[:80]}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=14, color='red')
        )
        fig.update_layout(
            height=600,
            paper_bgcolor=theme_styles.get('plot_bg', 'white') if 'theme_styles' in locals() else 'white'
        )
        return fig

@callback(
    Output('transferencias-treemap-dias-sin-venta', 'figure'),
    [Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-data-store', 'data'),  # 
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
            texttemplate="<b>%{label}</b><br>Ventas: %{customdata}",
            hovertemplate="<b>%{text}</b><br>" +
                         # %{value} now shows days
                         "Días sin venta: %{value}<br>" +
                         "Ventas históricas: %{customdata[0]}<br>" +
                         "Última venta: %{customdata[1]}<br>" +
                         "<extra></extra>",
            text=[cliente[:80] + "..." if len(cliente) > 80 else cliente
                  for cliente in data['cliente_completo']],
            customdata=[[format_currency_int(transferencias), fecha_str]
                        for transferencias, fecha_str in zip(
                data['valor_neto'],
                fechas_formatted)],
            marker=dict(
                colors=data['dias_sin_venta'],  
                colorscale='RdYlBu_r',
                line=dict(width=2, color='white'),
                cmin=data['dias_sin_venta'].min(),
                cmax=data['dias_sin_venta'].max()
            ),
            textfont=dict(size=10)
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
     Input('transferencias-dropdown-tipo-evolucion', 'value'),
     Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-dropdown-mes', 'value'),
     Input('transferencias-data-store', 'data'),
     Input('transferencias-theme-store', 'data')]
)
def update_evolucion_cliente(cliente, tipo_evolucion, session_data, dropdown_value, mes, data_store, theme):
    """
    Update client evolution chart - diario o mensual
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        theme_styles = get_theme_styles(theme)

        if cliente == 'Seleccione un cliente':
            fig = go.Figure()
            tipo_text = "diaria" if tipo_evolucion == 'diario' else "mensual"
            fig.add_annotation(
                text=f"Seleccione un cliente para ver su evolución {tipo_text} de transferencias",
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
                xaxis=dict(
                    showgrid=True,
                    gridcolor=theme_styles['grid_color'],
                    gridwidth=1,
                    linecolor=theme_styles['grid_color'],
                    zeroline=False
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor=theme_styles['grid_color'],
                    gridwidth=1,
                    linecolor=theme_styles['grid_color'],
                    zeroline=False
                ),
                font=dict(
                    family="Inter", 
                    size=12,
                    color=theme_styles['text_color']
                )
            )
            return fig

        # Obtener datos según tipo de evolución
        if tipo_evolucion == 'mensual':
            # Usar datos mensuales del analyzer
            data = analyzer.get_ventas_por_rango_meses(vendedor, 1, 12)  # Todo el año
            if data and not data.get('mensual', pd.DataFrame()).empty:
                data_mensual = data['mensual']
                data_cliente = data_mensual[
                    data_mensual['cliente_completo'] == cliente
                ].sort_values('mes_año')
                
                if not data_cliente.empty:
                    # Convertir a formato compatible
                    data = pd.DataFrame({
                        'fecha_str': data_cliente['mes_año'],
                        'valor_neto': data_cliente['valor_neto'],
                        'documento_id': data_cliente['documento_id']
                    })
                else:
                    data = pd.DataFrame()
            else:
                data = pd.DataFrame()
        else:
            # Usar método original para datos diarios
            data = analyzer.get_evolucion_cliente(cliente, vendedor)
            
            # Apply month filter if specified
            if mes and mes != 'Todos' and not data.empty:
                try:
                    data = data[data['fecha_str'].str.startswith(mes)]
                except:
                    pass

        if data.empty:
            tipo_text = "diarios" if tipo_evolucion == 'diario' else "mensuales"
            mensaje = f"No hay datos {tipo_text} para {cliente}"
            if mes != 'Todos' and tipo_evolucion == 'diario':
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
                xaxis=dict(
                    showgrid=True,
                    gridcolor=theme_styles['grid_color'],
                    gridwidth=1,
                    linecolor=theme_styles['grid_color'],
                    zeroline=False
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor=theme_styles['grid_color'],
                    gridwidth=1,
                    linecolor=theme_styles['grid_color'],
                    zeroline=False
                ),
                plot_bgcolor=theme_styles['plot_bg'],
                paper_bgcolor=theme_styles['plot_bg'],
                font=dict(family="Inter", size=12,
                          color=theme_styles['text_color'])
            )
            return fig

        # Calculate totals for title
        total_transferencias_periodo = data['valor_neto'].sum()
        num_periodos = len(data)

        # Create chart
        fig = go.Figure()
        
        # Colores según tipo
        if tipo_evolucion == 'mensual':
            # Colores más intensos para mensual
            colors = [
                'rgba(59, 130, 246, 0.4)', 'rgba(16, 185, 129, 0.4)',
                'rgba(245, 158, 11, 0.4)', 'rgba(239, 68, 68, 0.4)',
                'rgba(139, 92, 246, 0.4)', 'rgba(236, 72, 153, 0.4)'
            ]
            border_colors = [
                'rgba(59, 130, 246, 0.9)', 'rgba(16, 185, 129, 0.9)',
                'rgba(245, 158, 11, 0.9)', 'rgba(239, 68, 68, 0.9)',
                'rgba(139, 92, 246, 0.9)', 'rgba(236, 72, 153, 0.9)'
            ]
        else:
            # Colores pastel para diario
            colors = [
                'rgba(144, 238, 144, 0.4)', 'rgba(173, 216, 230, 0.4)',
                'rgba(255, 218, 185, 0.4)', 'rgba(221, 160, 221, 0.4)',
                'rgba(175, 238, 238, 0.4)', 'rgba(255, 182, 193, 0.4)'
            ]
            border_colors = [
                'rgba(144, 238, 144, 0.9)', 'rgba(173, 216, 230, 0.9)',
                'rgba(255, 218, 185, 0.9)', 'rgba(221, 160, 221, 0.9)',
                'rgba(175, 238, 238, 0.9)', 'rgba(255, 182, 193, 0.9)'
            ]

        bar_colors = [colors[i % len(colors)] for i in range(len(data))]
        border_colors_list = [border_colors[i % len(border_colors)] for i in range(len(data))]

        fig.add_trace(go.Bar(
            x=data['fecha_str'],
            y=data['valor_neto'],
            marker=dict(
                color=bar_colors,
                line=dict(color=border_colors_list, width=1),
                opacity=0.9
            ),
            text=[format_currency_int(val) if val > 50000 else '' for val in data['valor_neto']],
            textposition='outside',
            textfont=dict(size=9, color=theme_styles['text_color']),
            hovertemplate="<b>%{x}</b><br>" +
                         "Ventas: %{customdata[0]}<br>" +
                         "Facturas: %{customdata[1]}<br>" +
                         "<extra></extra>",
            customdata=[[format_currency_int(val), facturas] for val, facturas in zip(
                data['valor_neto'], data['documento_id'])]
        ))

        # Título dinámico
        cliente_corto = cliente[:80] + '...' if len(cliente) > 80 else cliente
        total_ventas_str = format_currency_int(total_transferencias_periodo)
        
        periodo_text = "días" if tipo_evolucion == 'diario' else "meses"
        promedio_text = "diario" if tipo_evolucion == 'diario' else "mensual"
        
        ticket_promedio = format_currency_int(
            total_transferencias_periodo / num_periodos) if num_periodos != 0 else 0

        titulo_completo = (
            f"<span style='font-size:16px; font-weight:bold;'>"
            f"Total: {total_ventas_str} ({num_periodos} {periodo_text})</span>"
            f"<br><span style='font-size:13px; margin-top:10px; display:inline-block;'>"
            f"Promedio {promedio_text}: {ticket_promedio}</span>"
            f"<br><span style='font-size:10px; margin-top:10px; display:inline-block;'>"
            f"{cliente_corto} - {tipo_evolucion.title()}</span>"
        )

        fig.update_layout(
            title=dict(
                text=titulo_completo,
                x=0.5,
                font=dict(color=theme_styles['text_color']),
                pad=dict(t=40)  
            ),
            height=480,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=12, color=theme_styles['text_color']),
            xaxis=dict(
                title="Fecha" if tipo_evolucion == 'diario' else "Mes",
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                linecolor=theme_styles['grid_color'],
                linewidth=0.5,
                tickangle=-45,
                type='category',
                tickfont=dict(color=theme_styles['text_color']),
                zeroline=False
            ),
            yaxis=dict(
                title="Ventas ($)",
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                linecolor=theme_styles['grid_color'],
                linewidth=0.5,
                tickformat='$,.0f',
                tickfont=dict(color=theme_styles['text_color']),
                zeroline=False
            ),
            showlegend=False,
            margin=dict(t=110, b=80, l=80, r=40)
        )

        return fig
    except Exception as e:
        print(f"❌ [update_evolucion_cliente] Error: {e}")
        return go.Figure()

def hex_to_rgba(hex_color, alpha=0.5):
    """
    Convert hex color to rgba format.
    """
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    return f'rgba({r},{g},{b},{alpha})'


@callback(
    Output('transferencias-top-clientes', 'figure'),
    [Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-dropdown-mes', 'value'),
     Input('transferencias-data-store', 'data'),
     Input('transferencias-theme-store', 'data')]
)
def update_top_clientes(session_data, dropdown_value, mes, data_store, theme):
    """
    Update top customers chart with custom fill and border colors.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_top_clientes(vendedor, mes, top_n=10)
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
                height=400,
                paper_bgcolor=theme_styles['plot_bg']
            )
            return fig

        # Define color palettes
        base_colors = [
            "#0077B6", "#00B4D8", "#90E0EF", "#CAF0F8", "#023E8A",
            "#03045E", "#0096C7", "#48CAE4", "#ADE8F4", "#61A5C2"
        ]
        fill_colors = [hex_to_rgba(c, 0.2) for c in base_colors]
        border_colors = base_colors

        # Prepare data
        data_sorted = data.sort_values('valor_neto', ascending=True)
        data_sorted['rank'] = sorted(range(1, len(data_sorted) + 1), reverse=True)
        data_sorted['short_label'] = [f"#{i}" for i in data_sorted['rank']]

        # Build figure
        fig = go.Figure()
        for i, row in data_sorted.iterrows():
            fig.add_trace(go.Bar(
                x=[row['valor_neto']],
                y=[row['short_label']],
                orientation='h',
                marker=dict(
                    color=fill_colors[i % len(fill_colors)],
                    line=dict(color=border_colors[i % len(border_colors)], width=1.5)
                ),
                text=[row['cliente_completo'][:100] + "..." if len(row['cliente_completo']) > 100 else row['cliente_completo']],
                textposition='inside',
                textfont=dict(color=theme_styles['text_color'], size=10),
                hovertemplate=(
                    f"<b>{row['cliente_completo']}</b><br>"
                    f"Ventas: {format_currency_int(row['valor_neto'])}<br>"
                    f"Facturas: {row['documento_id']}<extra></extra>"
                ),
                showlegend=False
            ))

        # Layout
        fig.update_layout(
            height=400,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=12, color=theme_styles['text_color']),
            xaxis=dict(
                tickformat='$,.0f',
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                title="Ventas"
            ),
            yaxis=dict(
                title="Ranking",
                categoryorder='array',
                categoryarray=data_sorted['short_label']
            ),
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
     Input('transferencias-data-store', 'data')]  # 
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
                'flex': '0 0 45%',  
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
                title += f"\n{vendedor}\n{mes}"
            elif vendedor != 'Todos':
                title += f"\n{vendedor}"
            elif mes != 'Todos':
                title += f"\n{mes}"
            else:
                title += "\nTodos los Transferencistas"
            
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
    Output('transferencias-subtitulo', 'children'),
    [Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-dropdown-mes', 'value')]
)
def update_subtitle(session_data, dropdown_value, mes):
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
        parts = []
        
        if vendedor and vendedor != 'Todos':
            parts.append(f"{vendedor.title()}")
        else:
            parts.append("Todos los Transferencistas")
            
        if mes and mes != 'Todos':
            parts.append(f"{mes}")
        else:
            parts.append("Todos los períodos")
            
        return " • ".join(parts)
        
    except Exception as e:
        print(f"❌ [update_subtitle] Error: {e}")
        return "Dashboard de Transferencias"


@callback(
    [Output('transferencias-theme-store', 'data'),
     Output('transferencias-theme-toggle', 'children'),
     Output('transferencias-main-container', 'style')],
    [Input('transferencias-theme-toggle', 'n_clicks')],
    [State('transferencias-theme-store', 'data')]
)
def toggle_theme(n_clicks, current_theme):
    """
    Toggle between light and dark theme with animated gradient backgrounds.
    """
    if not n_clicks:
        # Tema claro por defecto
        return (
            "light",
            "🌙",
            {
                'width': '100%', 'minHeight': '100vh',
                'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
                'transition': 'all 0.3s ease', 'padding': '20px 0',
                'background': 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 25%, #f8fafc 50%, #f1f5f9 100%)',
                'backgroundSize': '400% 400%',
                'animation': 'gradientShift 15s ease infinite',
                'color': '#111827'
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
                'transition': 'all 0.3s ease', 'padding': '20px 0',
                'background': 'linear-gradient(135deg, #0f172a 0%, #1e293b 25%, #334155 50%, #475569 100%)',
                'backgroundSize': '400% 400%',
                'animation': 'gradientShift 15s ease infinite',
                'color': '#f8fafc'
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
                'transition': 'all 0.3s ease', 'padding': '20px 0',
                'background': 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 25%, #f8fafc 50%, #f1f5f9 100%)',
                'backgroundSize': '400% 400%',
                'animation': 'gradientShift 15s ease infinite',
                'color': '#111827'
            }
        )

@callback(
    [Output('transferencias-dropdown-vendedor', 'style'),
     Output('transferencias-dropdown-mes', 'style'),
     Output('transferencias-dropdown-cliente', 'style'),
     Output('transferencias-dropdown-tipo-evolucion', 'style'),
     Output('transferencias-heatmap-clientes', 'style'), 
     Output('transferencias-dropdown-vendedor', 'className'),
     Output('transferencias-dropdown-mes', 'className'),
     Output('transferencias-dropdown-cliente', 'className'),
     Output('transferencias-dropdown-tipo-evolucion', 'className'),
     Output('transferencias-heatmap-clientes', 'className')], 
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
    
    # Estilo específico para dropdown del heatmap (letra más pequeña)
    heatmap_dropdown_style = get_dropdown_style(theme).copy()
    heatmap_dropdown_style.update({
        'fontFamily': 'Inter',
        'fontSize': '12px',  # Mantener tamaño específico
        'height': 'auto',    # Altura automática para multi-select
        'minHeight': '38px'  # Altura mínima
    })

    # Special handling for vendor dropdown - hide if not admin
    if not session_data or not can_see_all_vendors(session_data):
        vendedor_style = {'display': 'none'}
    else:
        vendedor_style = dropdown_style.copy()

    # CSS class for dark theme
    css_class = 'dash-dropdown dark-theme' if theme == 'dark' else 'dash-dropdown'
    
    # Clase específica para el dropdown del heatmap
    heatmap_css_class = f'{css_class} heatmap-dropdown'

    return (
        # Styles
        vendedor_style, dropdown_style, dropdown_style, 
        dropdown_style, heatmap_dropdown_style,
        # Classes  
        css_class, css_class, css_class, 
        css_class, heatmap_css_class 
    )

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
     Output('transferencias-row-top-clientes', 'style'),
     Output('transferencias-row-nueva-treemap', 'style'),
     Output('transferencias-row2-container', 'style'),
     Output('transferencias-row2-5-container', 'style'),
     Output('transferencias-row-heatmap', 'style'),
     Output('transferencias-heatmap-top10', 'style'),    
     Output('transferencias-heatmap-bottom10', 'style')],
    [Input('transferencias-theme-store', 'data')]
)
def update_container_styles(theme):
    """Update styles for chart containers and heatmap buttons based on theme."""
    theme_styles = get_theme_styles(theme)

    # Estilo base para contenedores
    base_style = {
        'backgroundColor': theme_styles['paper_color'],
        'padding': '25px',
        'borderRadius': '12px',
        'boxShadow': theme_styles['card_shadow'],
        'margin': '15px 0',
        'color': theme_styles['text_color'],
        'transition': 'all 0.3s ease'
    }
    
    # Estilo para botones del heatmap según tema
    if theme == 'dark':
        button_style = {
            'padding': '8px 16px',
            'border': '2px solid #4b5563',
            'borderRadius': '20px',
            'background': '#374151',
            'color': '#f9fafb',
            'fontFamily': 'Inter',
            'fontWeight': '500',
            'fontSize': '12px',
            'cursor': 'pointer',
            'transition': 'all 0.3s ease',
            'minWidth': '120px',
            'textAlign': 'center',
            'marginRight': '10px'
        }
    else:
        button_style = {
            'padding': '8px 16px',
            'border': '2px solid #e5e7eb',
            'borderRadius': '20px',
            'background': 'white',
            'color': '#6b7280',
            'fontFamily': 'Inter',
            'fontWeight': '500',
            'fontSize': '12px',
            'cursor': 'pointer',
            'transition': 'all 0.3s ease',
            'minWidth': '120px',
            'textAlign': 'center',
            'marginRight': '10px'
        }
    
    # Retornar estilos: 8 contenedores + 2 botones
    return [base_style] * 7 + [button_style, button_style]

@callback(
    Output('transferencias-heatmap-variaciones', 'figure'),
    [Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-heatmap-rango-meses', 'value'),
     Input('transferencias-heatmap-top10', 'n_clicks'),
     Input('transferencias-heatmap-bottom10', 'n_clicks'),
     Input('transferencias-heatmap-clientes', 'value'),
     Input('transferencias-data-store', 'data'),
     Input('transferencias-theme-store', 'data')],
    [State('transferencias-heatmap-top10', 'className'),
     State('transferencias-heatmap-bottom10', 'className')]
)
def update_heatmap_variaciones(session_data, dropdown_value, rango_meses, top10_clicks, 
                              bottom10_clicks, clientes_seleccionados, data_store, theme,
                              top10_class, bottom10_class):
    """Actualizar heatmap con 3 tipos de filtros - CORREGIDO"""
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        theme_styles = get_theme_styles(theme)
        
        # Obtener rango de meses
        if rango_meses and len(rango_meses) == 2:
            mes_inicio, mes_fin = rango_meses
        else:
            mes_inicio, mes_fin = get_ultimos_3_meses()
        
        # Determinar tipo de filtro y título
        data = pd.DataFrame()
        titulo_filtro = "Primeros 10"
        
        # CORRECCIÓN 1: Prioridad: clientes específicos > botones activos
        if clientes_seleccionados and len(clientes_seleccionados) > 0:
            data = analyzer.get_variaciones_clientes_especificos(
                vendedor, mes_inicio, mes_fin, clientes_seleccionados
            )
            titulo_filtro = f"Comparación de {len(clientes_seleccionados)} clientes"
        else:
            # CORRECCIÓN: Usar las clases CSS para determinar cuál botón está activo
            if 'active' in (bottom10_class or ''):
                filtro_tipo = 'bottom10'
                titulo_filtro = "Últimos 10"
            else:
                filtro_tipo = 'top10'
                titulo_filtro = "Primeros 10"
            
            data = analyzer.get_variaciones_mensuales_clientes(
                vendedor, mes_inicio, mes_fin, filtro_tipo
            )
        
        if data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay suficientes datos para el período seleccionado",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False,
                font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=500,  # CORRECCIÓN 2: Altura fija para evitar cambios
                paper_bgcolor=theme_styles['plot_bg'],
                plot_bgcolor=theme_styles['plot_bg']
            )
            return fig
        
        # Preparar datos
        z_values = data.values
        text_values = [[f"{val:+.1f}%" if not pd.isna(val) and val != 0 else "" 
                       for val in row] for row in z_values]
        
        # Crear heatmap
        fig = go.Figure(data=go.Heatmap(
            z=z_values,
            x=data.columns,
            y=[url[:40] + "..." if len(url) > 40 else url for url in data.index],
            text=text_values,
            texttemplate="%{text}",
            textfont={"family": "Inter", "size": 10, "color": "white"},
            colorscale=[
                [0.0, "#b91c1c"], [0.15, "#dc2626"], [0.3, "#ef4444"],
                [0.4, "#f87171"], [0.45, "#fbbf24"], [0.5, "#e5e7eb"],
                [0.55, "#84cc16"], [0.6, "#22c55e"], [0.7, "#16a34a"],
                [0.85, "#15803d"], [1.0, "#166534"]
            ],
            showscale=False,
            hoverongaps=False,
            hovertemplate="<b>%{y}</b><br>%{x}<br>Variación: %{z:+.1f}%<extra></extra>",
            xgap=1,
            ygap=1,
            zmin=-100,
            zmax=100
        ))
        
        # Layout con altura estable
        fig.update_layout(
            height=550,  # Usar altura calculada de forma estable
            margin=dict(t=50, b=60, l=220, r=20),
            font=dict(family="Inter", color=theme_styles['text_color']),
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            title=dict(
                text=titulo_filtro,
                x=0.5,
                font=dict(size=14, color=theme_styles['text_color'])
            ),
            xaxis=dict(
                tickangle=-45,
                tickfont=dict(color=theme_styles['text_color'], size=9),
                title_font=dict(color=theme_styles['text_color']),
                showgrid=False
            ),
            yaxis=dict(
                tickfont=dict(color=theme_styles['text_color'], size=9),
                title_font=dict(color=theme_styles['text_color']),
                showgrid=False
            )
        )
        
        return fig
        
    except Exception as e:
        print(f"❌ Error en heatmap: {e}")
        fig = go.Figure()
        fig.update_layout(height=500)  # Altura fija en caso de error
        return fig

@callback(
    Output('transferencias-heatmap-clientes', 'options'),
    [Input('session-store', 'data'),
     Input('transferencias-dropdown-vendedor', 'value'),
     Input('transferencias-heatmap-rango-meses', 'value'),
     Input('transferencias-data-store', 'data')]
)
def update_clientes_heatmap_options(session_data, dropdown_value, rango_meses, data_store):
    """Actualizar opciones de clientes para heatmap"""
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        
        # Obtener rango de meses
        if rango_meses and len(rango_meses) == 2:
            mes_inicio, mes_fin = rango_meses
        else:
            mes_inicio, mes_fin = get_ultimos_3_meses()
        
        # Obtener lista de clientes con datos en el período
        clientes = analyzer.get_clientes_con_variaciones(vendedor, mes_inicio, mes_fin)
        
        if clientes:
            options = [
                {
                    'label': f"{cliente[:40]}{'...' if len(cliente) > 40 else ''}", 
                    'value': cliente
                } 
                for cliente in sorted(clientes)
            ]
            return options
        
        return []
        
    except Exception as e:
        print(f"❌ Error obteniendo clientes para heatmap: {e}")
        return []

@callback(
    Output('transferencias-heatmap-clientes', 'value'),
    [Input('transferencias-heatmap-clientes', 'value')],
    prevent_initial_call=True
)
def limit_cliente_selection(selected_clientes):
    """Limitar selección a máximo 5 clientes"""
    if selected_clientes and len(selected_clientes) > 10:
        return selected_clientes[:10]
    return selected_clientes

@callback(
    [Output('transferencias-heatmap-top10', 'className'),
     Output('transferencias-heatmap-bottom10', 'className'),
     Output('transferencias-heatmap-clientes', 'value', allow_duplicate=True)],
    [Input('transferencias-heatmap-top10', 'n_clicks'),
     Input('transferencias-heatmap-bottom10', 'n_clicks'),
     Input('transferencias-heatmap-clientes', 'value')],
    prevent_initial_call=True
)
def update_heatmap_button_styles(top10_clicks, bottom10_clicks, clientes_seleccionados):
    """Actualizar estilos de botones y limpiar selección cuando se usa ranking"""
    ctx = dash.callback_context
    if not ctx.triggered:
        return 'heatmap-filter-btn active', 'heatmap-filter-btn', dash.no_update
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Si se seleccionaron clientes, desactivar botones
    if clientes_seleccionados and len(clientes_seleccionados) > 0:
        return 'heatmap-filter-btn', 'heatmap-filter-btn', dash.no_update
    
    # Si se presionó un botón, limpiar selección de clientes y activar botón
    if 'top10' in trigger_id:
        return 'heatmap-filter-btn active', 'heatmap-filter-btn', []
    elif 'bottom10' in trigger_id:
        return 'heatmap-filter-btn', 'heatmap-filter-btn active', []
    
    # Default
    return 'heatmap-filter-btn active', 'heatmap-filter-btn', dash.no_update



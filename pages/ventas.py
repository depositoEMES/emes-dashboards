import math
import numpy as np
import time
from datetime import datetime

import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from components import (
    create_metrics_grid, 
    create_empty_metrics, 
    METRIC_COLORS, 
)
from analyzers import VentasAnalyzer
from utils import (
    format_currency_int, 
    get_theme_styles,
    get_dropdown_style,
    get_ultimos_3_meses
)

analyzer = VentasAnalyzer()

# Carga inicial opcional (se recarga on-demand)
try:
    df = analyzer.load_data_from_firebase()
except Exception as e:
    print(f"⚠️ [VentasPage] Carga inicial falló (se recargará on-demand): {e}")
    df = pd.DataFrame()

# Try to load optional data (convenios, recibos, num_clientes)
try:
    df_convenios = analyzer.load_convenios_from_firebase()
except Exception as e:
    print(f"⚠️ [VentasPage] Could not load convenios: {e}")
    df_convenios = pd.DataFrame()

try:
    df_recibos = analyzer.load_recibos_from_firebase()
except Exception as e:
    print(f"⚠️ [VentasPage] Could not load recibos: {e}")
    df_recibos = pd.DataFrame()

try:
    df_num_clientes = analyzer.load_num_clientes_from_firebase()
except Exception as e:
    print(f"⚠️ [VentasPage] Could not load num_clientes: {e}")
    df_num_clientes = pd.DataFrame()


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
    dcc.Store(id='ventas-data-store', data={'last_update': 0}),

    # Notification area
    html.Div(id='ventas-notification-area', children=[], style={
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
                    id='ventas-titulo-principal',
                    className="main-title",
                    children="Vendedores"
                ),
                html.P(
                    id='ventas-subtitulo',
                    className="main-subtitle",
                    children="Análisis completo de ventas y performance"
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
                    id="ventas-theme-toggle",
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
        ], className="top-header", id='ventas-header-container', style={
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
                html.Label("Vendedor:",
                           id='ventas-dropdown-vendedor-label',
                           style={
                               'fontWeight': '600',
                               'fontSize': '14px',
                               'marginBottom': '8px',
                               'display': 'block'
                           }),
                dcc.Dropdown(
                    id='ventas-dropdown-vendedor',
                    options=[{'label': v, 'value': v} for v in analyzer.vendedores_list],
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
            }, id='ventas-dropdown-vendedor-container'),

            html.Div([
                html.Label("Período:",
                           style={
                               'fontWeight': '600',
                               'fontSize': '14px',
                               'marginBottom': '8px',
                               'display': 'block'
                           }),
                dcc.Dropdown(
                    id='ventas-dropdown-mes',
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
                    id="ventas-btn-actualizar",
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
        ], id='ventas-controls-container', style={
            'display': 'flex',
            'gap': '24px',
            'alignItems': 'stretch',
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'flexWrap': 'wrap'
        }),

        html.Div(id="ventas-metrics-cards", children=[], style={'marginBottom': '24px'}),

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
        ], id='ventas-row1-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

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
        ], id='ventas-row1-2-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

        # Fila 1.3: Ventas por vendedor (subplots)
        html.Div([
            html.H3("Evolución Individual por Vendedor", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
            html.P("(Gráficos de área individuales - Solo visible para administradores)", style={
                'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '12px', 'margin': '0 0 20px 0'}),
            dcc.Graph(id='ventas-graficos-area-individuales')
        ], id='ventas-row1-3-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

        # Fila 1.5: Evolución de Ventas por Cliente Específico
        html.Div([
            html.H3("Evolución Ventas por Cliente", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
            html.Div([
                # Dropdown de cliente
                html.Div([
                    html.Label("Cliente:", style={
                            'fontWeight': 'bold', 'marginBottom': '8px', 'fontFamily': 'Inter', 'fontSize': '14px'}),
                    dcc.Dropdown(
                        id='ventas-dropdown-cliente',
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
                        id='ventas-dropdown-tipo-evolucion',
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
            
            dcc.Graph(id='ventas-grafico-evolucion-cliente')
        ], id='ventas-row1-5-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

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
        ], id='ventas-row2-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

        # Fila 2.5: Ventas Acumuladas por Cliente (Treemap solo)
        html.Div([
            html.H3("Ventas por Cliente - Análisis Temporal", style={
                'textAlign': 'center', 
                'marginBottom': '25px', 
                'fontFamily': 'Inter'
            }),
            
            # Contenedor de filtros OPTIMIZADOS
            html.Div([
                # Filtro de número de clientes (izquierda)
                html.Div([
                    html.Label("Número de Clientes a Mostrar:", style={
                        'fontWeight': 'bold',
                        'marginBottom': '10px',
                        'fontFamily': 'Inter',
                        'fontSize': '14px'
                    }),
                    dcc.Slider(
                        id='ventas-filtro-num-clientes',
                        min=10,
                        max=200,  
                        step=10,
                        value=10,  # Por defecto 50 clientes
                        marks={
                            10: '10', 25: '25', 50: '50', 
                            100: '100', 150: '150', 200: '200+'
                        },
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], style={
                    'width': '48%',
                    'display': 'inline-block',
                    'marginRight': '4%'
                }),
                
                # Filtro de categoría de crecimiento (derecha)
                html.Div([
                    html.Label("Filtrar por Tendencia:", style={
                        'fontWeight': 'bold',
                        'marginBottom': '10px',
                        'fontFamily': 'Inter',
                        'fontSize': '14px'
                    }),
                    dcc.Dropdown(
                        id='ventas-filtro-tendencia',
                        options=[
                            {'label': '🟢 Crecimiento Positivo', 'value': 'positivo'},
                            {'label': '🟡 Estable', 'value': 'estable'},
                            {'label': '🔴 Decrecimiento', 'value': 'negativo'},
                            {'label': '📊 Todos', 'value': 'todos'}
                        ],
                        value='todos',
                        placeholder="Seleccionar tendencia...",
                        style={'fontFamily': 'Inter', 'fontSize': '14px'}
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
            
            dcc.Graph(id='ventas-treemap-unificado', style={'height': '650px'})
            
        ], id='ventas-row2-5-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

        # Fila 3.5: Top Clientes y Clientes Impactados
        html.Div([
            html.H3("Clientes por Días Sin Venta", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
            
            # Slider dinámico para días sin venta
            html.Div([
                html.Label("Días mínimos sin venta:", style={
                    'fontWeight': 'bold',
                    'marginBottom': '10px',
                    'fontFamily': 'Inter',
                    'fontSize': '14px',
                    'display': 'block'
                }),
                dcc.Slider(
                    id='ventas-filtro-dias-sin-venta',
                    min=0,
                    max=365,  # Se configurará dinámicamente
                    step=1,
                    value=30,  # Valor por defecto
                    marks={},  # Se configurarán dinámicamente
                    tooltip={
                        "placement": "bottom", 
                        "always_visible": True,
                        "style": {"color": "white", "fontSize": "12px"}
                    }
                )
            ], style={
                'marginBottom': '15px',
                'padding': '15px',
                'borderRadius': '8px',
                'border': '1px solid #e5e7eb'
            }),
            
            html.P(id='ventas-texto-dias-sin-venta', 
                children="(Clientes que no han comprado en 30+ días - Tamaño por total de ventas históricas)", 
                style={'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '12px', 'margin': '0 0 20px 0'}),
            
            dcc.Graph(id='ventas-treemap-dias-sin-venta')
        ], id='ventas-row-nueva-treemap', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

        # Fila 4: Top Clientes y Clientes Impactados
        html.Div([
            html.Div([
                html.H3("Top 10 - Clientes por Ventas ($)", style={'textAlign': 'center',
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
        ], id='ventas-row4-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

        # Fila 5: Análisis de Convenios
        html.Div([
            html.H3("Análisis de Cumplimiento de Convenios", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),
            html.P("(Comparación entre metas vs. ventas reales y descuentos acordados vs. descuentos aplicados)", style={
                   'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '12px', 'margin': '0 0 20px 0'}),
            html.Div(id='ventas-tabla-convenios')
        ], id='ventas-row5-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

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
        ], id='ventas-row6-container', style={
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
                        id='ventas-heatmap-rango-meses',
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
                            html.Button("📈 Primeros 10", id="ventas-heatmap-top10", 
                                    className="heatmap-filter-btn active", n_clicks=0,
                                    style={'marginRight': '10px'}),
                            html.Button("📉 Últimos 10", id="ventas-heatmap-bottom10", 
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
                            id='ventas-heatmap-clientes',
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
                id='ventas-heatmap-variaciones', 
                style={
                    'height': '600px',
                    'overflowY': 'auto',  # Scroll vertical
                    'overflowX': 'auto'   # Scroll horizontal si es necesario
                }
            )
            
        ], id='ventas-row-heatmap', style={
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
    
], id='ventas-main-container', style={
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
    Output('ventas-data-store', 'data'),
    [Input('ventas-btn-actualizar', 'n_clicks')],
    prevent_initial_call=True
)
def update_ventas_data(n_clicks):
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
            print(f"❌ [VentasPage] Error en actualización #{n_clicks}: {e}")
            return {
                'last_update': n_clicks,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'success': False
            }

    return dash.no_update


@callback(
    Output('ventas-notification-area', 'children'),
    [Input('ventas-data-store', 'data')],
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
                }, id='ventas-success-notification')
            ])

    return []


@callback(
    [Output('ventas-btn-actualizar', 'children'),
     Output('ventas-btn-actualizar', 'disabled')],
    [Input('ventas-data-store', 'data')],
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
    [Output('ventas-card-1-title', 'style'),
     Output('ventas-card-2-title', 'style'),
     Output('ventas-card-3-title', 'style'),
     Output('ventas-card-4-title', 'style'),
     Output('ventas-card-5-title', 'style'),
     Output('ventas-card-6-title', 'style'),
     Output('ventas-card-7-title', 'style'),
     Output('ventas-card-8-title', 'style')],
    [Input('ventas-theme-store', 'data')]
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
    [Output('ventas-filtro-monto-ventas', 'min'),
     Output('ventas-filtro-monto-ventas', 'max'),
     Output('ventas-filtro-monto-ventas', 'value'),
     Output('ventas-filtro-monto-ventas', 'marks'),
     Output('ventas-filtro-monto-ventas', 'step')],
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-data-store', 'data')]
)
def update_monto_slider_config(session_data, dropdown_value, data_store):
    """
    Configurar dinámicamente el slider de montos según los datos de ventas disponibles
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        
        # Obtener datos de ventas para calcular rangos
        df = analyzer.filter_data(vendedor, 'Todos')
        
        # Filtrar solo ventas reales
        ventas_reales = df[df['tipo'].str.contains(
            'Remision', case=False, na=False)]
        
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
        print(f"❌ Error configurando slider de montos en ventas: {e}")
        return 0, 1000000, [0, 1000000], {0: '$0', 1000000: '$1M'}, 50000

@callback(
    Output('ventas-grafico-ventas-mes', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-data-store', 'data'),  # 
     Input('ventas-theme-store', 'data')]
)
def update_ventas_mes(session_data, dropdown_value, data_store, theme):
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
        print(f"❌ [update_ventas_mes] Error: {e}")
        return go.Figure()


@callback(
    Output('ventas-grafico-estacionalidad', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-data-store', 'data'),  # 
     Input('ventas-theme-store', 'data')]
)
def update_estacionalidad(session_data, dropdown_value, mes, data_store, theme):
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
    Output('ventas-grafico-zona', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-data-store', 'data'),  # 
     Input('ventas-theme-store', 'data')]
)
def update_zona(session_data, dropdown_value, mes, data_store, theme):
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
    Output('ventas-grafico-forma-pago', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-data-store', 'data'),  # 
     Input('ventas-theme-store', 'data')]
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

def hex_to_rgba(hex_color, alpha=0.5):
    """
    Convert hex color to rgba format.
    """
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    return f'rgba({r},{g},{b},{alpha})'

@callback(
    Output('ventas-top-clientes', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-data-store', 'data'),  # 
     Input('ventas-theme-store', 'data')]
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
    Output('ventas-treemap-unificado', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-filtro-num-clientes', 'value'),
     Input('ventas-filtro-tendencia', 'value'),
     Input('ventas-data-store', 'data'),
     Input('ventas-theme-store', 'data')]
)
def update_treemap_unificado(
        session_data, 
        dropdown_value, 
        num_clientes, 
        filtro_tendencia, 
        data_store, 
        theme):
    """
    Segmented sales based on "vendedor".
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        theme_styles = get_theme_styles(theme)
        
        # Obtener datos pre-filtrados directamente
        df = analyzer.filter_data(vendedor, 'Todos')
        
        if df.empty:
            return create_empty_figure("No hay datos disponibles", theme_styles)
        
        # Filtro único y directo
        ventas_mask = df['tipo'].str.contains('Remision', case=False, na=False)
        ventas_reales = df[ventas_mask].copy()
        
        if ventas_reales.empty:
            return create_empty_figure("No hay ventas registradas", theme_styles)
        
        # Agrupación simple sin columnas auxiliares
        resultado_total = ventas_reales.groupby('cliente_completo', as_index=False).agg({
            'valor_neto': 'sum',
            'documento_id': 'count'
        })
        
        # Filtro rápido
        resultado_total = \
            resultado_total[resultado_total['valor_neto'] > 0].copy()
        
        if resultado_total.empty:
            return \
                create_empty_figure("No hay datos con ventas positivas", theme_styles)
        
        # Cálculo de tendencia 
        top_previo = min(num_clientes * 2, num_clientes)  
        resultado_work = resultado_total.nlargest(top_previo, 'valor_neto').copy()
        
        # Inicializar campos
        resultado_work['tendencia'] = 'estable'
        resultado_work['pct_crecimiento'] = 0.0
        
        # Crear índice de meses una sola vez
        ventas_reales['mes_periodo'] = ventas_reales['fecha'].dt.to_period('M')
        
        # Calcular tendencia con ACUMULADO DE VARIACIONES para clientes relevantes
        for idx, row in resultado_work.iterrows():
            try:
                cliente = row['cliente_completo']
                
                # Obtener serie temporal mensual del cliente
                cliente_mensual = ventas_reales[
                    ventas_reales['cliente_completo'] == cliente
                ].groupby('mes_periodo')['valor_neto'].sum().sort_index()
                
                if len(cliente_mensual) >= 2:
                    variaciones_mensuales = []
                    
                    for i in range(1, len(cliente_mensual)):
                        mes_anterior = cliente_mensual.iloc[i-1]
                        mes_actual = cliente_mensual.iloc[i]
                        
                        if mes_anterior > 0:  # Evitar división por cero
                            variacion = ((mes_actual - mes_anterior) / mes_anterior) * 100
                            variaciones_mensuales.append(variacion)
                        elif mes_actual > 0 and mes_anterior == 0:
                            variaciones_mensuales.append(100.0)  # 100% de crecimiento
                    
                    if variaciones_mensuales:
                        pct_acumulado = sum(variaciones_mensuales)
                        resultado_work.at[idx, 'pct_crecimiento'] = pct_acumulado
                        
                        # Categorización basada en acumulado
                        if pct_acumulado > 20:  
                            resultado_work.at[idx, 'tendencia'] = 'positivo'
                        elif pct_acumulado < -20:  
                            resultado_work.at[idx, 'tendencia'] = 'negativo'
                        
            except Exception as e:
                continue
        
        # Aplicar filtro de tendencia sin copiar DataFrames
        if filtro_tendencia != 'todos':
            resultado_work = \
                resultado_work[resultado_work['tendencia'] == filtro_tendencia]
            
            if resultado_work.empty:
                return \
                    create_empty_figure(f"No hay clientes con tendencia '{filtro_tendencia}'", theme_styles)
        
        # Limitación final temprana
        resultado_final = resultado_work.nlargest(num_clientes, 'valor_neto')
        
        # Construcción directa inline (sin funciones auxiliares)
        ids = [f"C{i}" for i in range(len(resultado_final))]
        
        # Colores y emojis inline
        color_map = \
            {
                'positivo': 'rgba(22,163,74,0.6)' if theme == 'light' else 'rgba(34,197,94,0.4)',
                'negativo': 'rgba(153, 27, 27,0.6)' if theme == 'light' else 'rgba(239, 68, 68,0.4)',
                'estable': 'rgba(217,119,6,0.6)' if theme == 'light' else 'rgba(251,191,36,0.4)'
            }
        
        border_map = \
            {
                'positivo': 'rgba(22,163,74,1.0)' if theme == 'light' else 'rgba(34,197,94,1.0)',
                'negativo': 'rgba(153, 27, 27,1.0)' if theme == 'light' else 'rgba(239, 68, 68,1.0)',
                'estable': 'rgba(217,119,6,1.0)' if theme == 'light' else 'rgba(251,191,36,1.0)'
            }
        
        emoji_map = {'positivo': '🟢', 'negativo': '🔴', 'estable': '🟡'}
        
        # Construcción en una sola pasada
        labels = []
        colors = []
        border_colors = []
        values = []
        text_labels = []
        
        for i, (_, row) in enumerate(resultado_final.iterrows()):
            # Procesar datos básicos
            cliente = \
                str(row['cliente_completo'])[:80] + ("..." if len(str(row['cliente_completo'])) > 80 else "")
            tendencia = row['tendencia']
            emoji = emoji_map[tendencia]
            valor = row['valor_neto']
            facturas = int(row['documento_id'])
            pct = row['pct_crecimiento']
            
            # Construir elementos
            labels.append(f"{emoji} {cliente}")
            colors.append(color_map[tendencia])
            border_colors.append(border_map[tendencia])
            values.append(valor)
            
            # Texto optimizado
            valor_fmt = \
                f"${valor/1000000:.1f}M" if valor >= 1000000 else f"${valor/1000:.0f}K" if valor >= 1000 else f"${valor:,.0f}".replace(',', '.')
            text_labels.append(
                f"<b>{emoji} {cliente}</b><br>"
                f"<span style='font-size:14px;font-weight:bold'>{valor_fmt}</span><br>"
                f"<span style='font-size:10px;opacity:0.9'>{facturas} fact. | {pct:+.0f}%</span>"
            )
        
        # Figura mínima sin configuraciones extra
        fig = go.Figure(go.Treemap(
            ids=ids,
            labels=labels,
            parents=[""] * len(ids),
            values=values,
            text=text_labels,
            texttemplate="%{text}",
            textposition="middle center",
            textfont=dict(
                size=11, 
                color=theme_styles['text_color'], 
                family='Inter'
            ),
            marker=dict(
                colors=colors,
                line=dict(width=1.0, color=border_colors)
            ),
            hovertemplate="<b>%{text}</b><extra></extra>",
            sort=True,
            tiling=dict(packing="binary", pad=2)
        ))
        
        # Layout mínimo
        tendencia_names = \
            {
                'positivo': 'Crecimiento',
                'negativo': 'Decrecimiento', 
                'estable': 'Estable',
                'todos': 'Todas'
            }
        
        fig.update_layout(
            height=650,
            margin=dict(t=70, b=10, l=5, r=5),
            font=dict(
                family="Inter", 
                color=theme_styles['text_color']
            ),
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            title=dict(
                text=f"Top {len(resultado_final)} Clientes - {tendencia_names.get(filtro_tendencia, 'Filtro')}<br><sub>🟢 Crecimiento | 🟡 Estable | 🔴 Decrecimiento</sub>",
                x=0.5, y=0.98, 
                font=dict(size=16, color=theme_styles['text_color'])
            )
        )
        
        return fig

    except Exception as e:
        print(f"❌ Error en treemap optimizado: {e}")
        
        return \
            create_empty_figure(
                "Error de procesamiento", 
                theme_styles if 'theme_styles' in locals() else {'plot_bg': 'white', 'text_color': 'black'}
            )

def create_empty_figure(message, theme_styles):
    """
    Crear figura vacía.
    """
    fig = go.Figure()
    fig.add_annotation(
        text=message, xref="paper", yref="paper",
        x=0.5, y=0.5, xanchor='center', yanchor='middle',
        showarrow=False, 
        font=dict(size=16, color=theme_styles['text_color'], family='Inter')
    )
    fig.update_layout(
        height=600, 
        paper_bgcolor=theme_styles['plot_bg'],
        plot_bgcolor=theme_styles['plot_bg']
    )
    return fig


@callback(
    Output('ventas-grafico-clientes-impactados', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-data-store', 'data'),  # 
     Input('ventas-theme-store', 'data')]
)
def update_clientes_impactados(session_data, dropdown_value, data_store, theme):
    """
    Update clients impacted chart with horizontal bars and total clients bar.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data, porcentaje_promedio, total_clientes = \
            analyzer.get_clientes_impactados_por_periodo(vendedor)
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
            opacity=0.6,
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
            marker=dict(color='#3498db', opacity=0.7),
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
        print(f"❌ [update_clientes_impactados] Error: {e}")
        return go.Figure()


@callback(
    Output('ventas-tabla-convenios', 'children'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-data-store', 'data'),  # 
     Input('ventas-theme-store', 'data')]
)
def update_tabla_convenios(session_data, dropdown_value, mes, data_store, theme):
    """
    Update convenios analysis table with enhanced design and expected sales.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_analisis_convenios(vendedor, mes="Todos") # Don't apply month filter
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
                    'color': 'white', 'fontFamily': 'Inter', 'fontSize': '12px', 'textAlign': 'center',
                    'position': 'sticky', 'top': '0', 'zIndex': '10'}),
            html.Th("Vendedor", style={'padding': '12px', 'backgroundColor': '#34495e',
                    'color': 'white', 'fontFamily': 'Inter', 'fontSize': '12px', 'textAlign': 'center',
                    'position': 'sticky', 'top': '0', 'zIndex': '10'}),
            html.Th("Ventas", style={'padding': '12px', 'backgroundColor': '#34495e',
                    'color': 'white', 'fontFamily': 'Inter', 'fontSize': '12px', 'textAlign': 'center',
                    'position': 'sticky', 'top': '0', 'zIndex': '10'}),
            html.Th("Ventas Esperadas", style={'padding': '12px', 'backgroundColor': '#34495e',
                    'color': 'white', 'fontFamily': 'Inter', 'fontSize': '12px', 'textAlign': 'center',
                    'position': 'sticky', 'top': '0', 'zIndex': '10'}),
            html.Th("Meta", style={'padding': '12px', 'backgroundColor': '#34495e',
                    'color': 'white', 'fontFamily': 'Inter', 'fontSize': '12px', 'textAlign': 'center',
                    'position': 'sticky', 'top': '0', 'zIndex': '10'}),
            html.Th("% Cumplimiento", style={'padding': '12px', 'backgroundColor': '#34495e',
                    'color': 'white', 'fontFamily': 'Inter', 'fontSize': '12px', 'textAlign': 'center',
                    'position': 'sticky', 'top': '0', 'zIndex': '10'}),
            html.Th("Estado", style={'padding': '12px', 'backgroundColor': '#34495e',
                    'color': 'white', 'fontFamily': 'Inter', 'fontSize': '12px', 'textAlign': 'center',
                    'position': 'sticky', 'top': '0', 'zIndex': '10'}),
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
        print(f"❌ [update_tabla_convenios] Error: {e}")
        return html.Div([html.P("Error al cargar datos de convenios")])


@callback(
    Output('ventas-grafico-recaudo-temporal', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-vista-recaudo', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-data-store', 'data'),  # 
     Input('ventas-theme-store', 'data')]
)
def update_grafico_recaudo_temporal(session_data, dropdown_value, vista_recaudo, mes, data_store, theme):
    """
    Update temporal recaudo chart with ascending/descending colors for daily view.
    """
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
            valores = data['valor_recibo'].tolist()
            bar_colors = []
            border_colors = []

            # Color para la primera barra (neutro)
            bar_colors.append('rgba(173, 216, 230, 0.4)')  # Light blue
            border_colors.append('rgba(173, 216, 230, 0.9)')  # Light blue

            # Determinar colores basado en tendencia
            for i in range(1, len(valores)):
                if valores[i] > valores[i-1]:
                    # Ascendente - Verde pastel
                    bar_colors.append('rgba(144, 238, 144, 0.4)')  # Light green
                    border_colors.append('rgba(144, 238, 144, 0.9)')  # Light green
                elif valores[i] < valores[i-1]:
                    # Descendente - Rosa pastel
                    bar_colors.append('rgba(255, 182, 193, 0.4)')  # Light pink
                    border_colors.append('rgba(255, 182, 193, 0.9)')  # Light pink
                else:
                    bar_colors.append('rgba(173, 216, 230, 0.4)')  # Light blue
                    border_colors.append('rgba(173, 216, 230, 0.9)')  # Light blue

            fig.add_trace(go.Bar(
                x=data[x_field],
                y=data['valor_recibo'],
                marker=dict(
                    color=bar_colors,
                    line=dict(color=border_colors, width=1),
                    opacity=0.9
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
            xaxis=dict(
                showgrid=True, 
                gridcolor=theme_styles['grid_color'],
                gridwidth=0.5,
                title=x_title, 
                tickangle=-45 if chart_type == 'bar' else 0),
            yaxis=dict(
                showgrid=True, 
                gridcolor=theme_styles['grid_color'], 
                gridwidth=0.5,
                tickformat='$,.0f', 
                title="Recaudo ($)"),
            showlegend=False,
            margin=dict(t=40, b=80, l=60, r=20)
        )

        return fig
    except Exception as e:
        print(f"❌ [update_grafico_recaudo_temporal] Error: {e}")
        return go.Figure()


@callback(
    Output('ventas-grafico-recaudo-vendedor', 'figure'),
    [Input('ventas-dropdown-mes', 'value'),
     Input('ventas-data-store', 'data'),  # 
     Input('ventas-theme-store', 'data')]
)
def update_grafico_recaudo_vendedor(mes, data_store, theme):
    """
    Update vendor summary chart - filter by specific month if selected.
    """
    try:
        data, total_recaudo = analyzer.get_recaudo_por_vendedor(mes)
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
        print(f"❌ [update_grafico_recaudo_vendedor] Error: {e}")
        return go.Figure()


@callback(
    Output('ventas-treemap-dias-sin-venta', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-filtro-dias-sin-venta', 'value'),
     Input('ventas-data-store', 'data'),
     Input('ventas-theme-store', 'data')]
)
def update_treemap_dias_sin_venta(session_data, dropdown_value, dias_minimos, data_store, theme):
    """
    Update days without sales treemap - TAMAÑO Y COLOR basados en DÍAS SIN VENTA
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        data = analyzer.get_dias_sin_venta_por_cliente(vendedor)
        theme_styles = get_theme_styles(theme)
        
        # Aplicar filtro de días mínimos (por defecto 30)
        dias_filtro = dias_minimos if dias_minimos is not None else 30
        
        # Solo filtrar si dias_filtro > 0
        if dias_filtro > 0:
            data = data[data['dias_sin_venta'] >= dias_filtro] if not data.empty else data

        if data.empty:
            fig = go.Figure()
            if dias_filtro == 0:
                mensaje = "No hay clientes con datos de días sin venta"
            else:
                mensaje = f"No hay clientes sin ventas por {dias_filtro}+ días"
            
            fig.add_annotation(
                text=mensaje,
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False,
                font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=500, 
                paper_bgcolor=theme_styles['plot_bg'],
                plot_bgcolor=theme_styles['plot_bg']
            )
            return fig
        
        # Clean data
        data = data.copy()
        data = data.dropna(subset=['cliente_completo', 'dias_sin_venta'])
        
        # Asegurar que dias_sin_venta sea numérico
        data['dias_sin_venta'] = pd.to_numeric(data['dias_sin_venta'], errors='coerce')
        data = data.dropna(subset=['dias_sin_venta'])
        
        # Filtrar valores negativos o zero (no tiene sentido en este contexto)
        data = data[data['dias_sin_venta'] > 0]
        
        # Asegurar que cliente_completo no esté vacío
        data = data[data['cliente_completo'].str.strip() != '']
        
        if data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos válidos para mostrar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False,
                font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(height=500, paper_bgcolor=theme_styles['plot_bg'])
            return fig

        def get_categoria_y_color(dias, alpha=0.4, is_dark_theme=False):
            """
            Categorizar días y obtener color según urgencia y tema.
            """
            if is_dark_theme:
                if dias < 30:
                    return "Reciente (< 1 mes)", f"rgba(34, 197, 94, {alpha})"      # Verde vibrante
                elif dias < 60:
                    return "1-2 meses", f"rgba(251, 191, 36, {alpha})"              # Amarillo dorado
                elif dias < 90:
                    return "2-3 meses", f"rgba(245, 158, 11, {alpha})"              # Naranja vibrante
                elif dias < 180:
                    return "3-6 meses", f"rgba(239, 68, 68, {alpha})"               # Rojo vibrante
                else:
                    return "6+ meses", f"rgba(153, 27, 27, {alpha})"                # Rojo oscuro intenso
            else:
                if dias < 30:
                    return "Reciente (< 1 mes)", f"rgba(21, 128, 61, {alpha})"      # Verde bosque
                elif dias < 60:
                    return "1-2 meses", f"rgba(180, 83, 9, {alpha})"                # Naranja tierra
                elif dias < 90:
                    return "2-3 meses", f"rgba(154, 52, 18, {alpha})"               # Naranja rojizo oscuro
                elif dias < 180:
                    return "3-6 meses", f"rgba(153, 27, 27, {alpha})"               # Rojo granate
                else:
                    return "6+ meses", f"rgba(69, 10, 10, {alpha})"   

        # Aplicar categorización
        data = data.copy()
        data['categoria'] = \
            data['dias_sin_venta'].apply(lambda x: get_categoria_y_color(x)[0])
        data['color'] = \
            data['dias_sin_venta'].apply(lambda x: get_categoria_y_color(x)[1])
        data['border_color'] = \
            data['dias_sin_venta'].apply(lambda x: get_categoria_y_color(x, alpha=0.9)[1])

        # Create labels optimizadas
        labels = []
        
        for _, row in data.iterrows():
            cliente = row['cliente_completo']
            dias = int(row['dias_sin_venta'])
            categoria = row['categoria']
            
            # Truncar nombre si es muy largo
            cliente_corto = cliente[:50] + "..." if len(cliente) > 50 else cliente
            
            labels.append(f"{cliente_corto}\n{dias} días\n({categoria})")

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
                
        
        ids = data.index.astype(str)
                
        # Create treemap - TAMAÑO basado en DÍAS SIN VENTA
        fig = go.Figure(go.Treemap(
            ids=ids,
            labels=labels,
            values=data['dias_sin_venta'],  # ← TAMAÑO por días sin venta
            parents=[""] * len(data),
            text=[f"<b>{cliente[:80]}{'...' if len(cliente) > 80 else ''}</b><br>"
                  f"<span style='font-size:14px'>{int(dias)} días</span><br>"
                  f"<span style='font-size:10px'>{categoria}</span>"
                  for cliente, dias, categoria in zip(
                      data['cliente_completo'], 
                      data['dias_sin_venta'],
                      data['categoria']
                  )],
            texttemplate="%{text}",
            textposition="middle center",
            textfont=dict(size=10, color=theme_styles['text_color'], family='Inter', weight='bold'),
            hovertemplate="<b>%{customdata[0]}</b><br>" +
                         "Días sin venta: <b>%{value}</b><br>" +
                         "Categoría: <b>%{customdata[1]}</b><br>" +
                         "Ventas históricas: %{customdata[2]}<br>" +
                         "Última venta: %{customdata[3]}<br>" +
                         "<extra></extra>",
            customdata=[[
                cliente,
                categoria, 
                format_currency_int(ventas),
                fecha_str
            ] for cliente, categoria, ventas, fecha_str in zip(
                data['cliente_completo'],
                data['categoria'],
                data['valor_neto'],
                fechas_formatted
            )],
            marker=dict(
                colors=data['color'].tolist(), 
                line=dict(width=1.0, color=data['border_color'])
            ),
            branchvalues="remainder",
            sort=True,  # Ordenar por tamaño (días sin venta)
            tiling=dict(packing="binary")
        ))

        # Título con información adicional
        total_clientes = len(data)
        promedio_dias = data['dias_sin_venta'].mean()

        fig.update_layout(
            height=500,
            font=dict(
                family="Inter", 
                size=12, 
                color=theme_styles['text_color']
            ),
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            margin=dict(t=40, b=0, l=0, r=0),
            title=dict(
                text=f"Clientes por Días Sin Venta ({total_clientes} clientes, promedio: {promedio_dias:.0f} días)",
                x=0.5, y=0.98, xanchor='center', yanchor='top',
                font=dict(size=14, color=theme_styles['text_color'], family="Inter")
            )
        )

        return fig
        
    except Exception as e:
        print(f"❌ [update_treemap_dias_sin_venta] Error: {e}")
        import traceback
        traceback.print_exc()
        
        fig = go.Figure()
        fig.update_layout(
            height=500,
            paper_bgcolor=theme_styles.get('plot_bg', 'white') if 'theme_styles' in locals() else 'white'
        )
        return fig


@callback(
    Output('ventas-grafico-evolucion-cliente', 'figure'),
    [Input('ventas-dropdown-cliente', 'value'),
     Input('ventas-dropdown-tipo-evolucion', 'value'),  # NUEVO INPUT
     Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-data-store', 'data'),
     Input('ventas-theme-store', 'data')]
)
def update_evolucion_cliente(
        cliente, 
        tipo_evolucion, 
        session_data, 
        dropdown_value, 
        mes, 
        data_store, 
        theme):
    """
    Update client evolution chart - filtered by month using main DataFrame.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        theme_styles = get_theme_styles(theme)

        if cliente == 'Seleccione un cliente':
            fig = go.Figure()
            tipo_text = "diaria" if tipo_evolucion == 'diario' else "mensual"
            fig.add_annotation(
                text=f"Seleccione un cliente para ver su evolución {tipo_text} de ventas",
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

        # NUEVO: Obtener datos según tipo de evolución
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
        total_ventas_periodo = data['valor_neto'].sum()
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
        total_ventas_str = format_currency_int(total_ventas_periodo)
        
        periodo_text = "días" if tipo_evolucion == 'diario' else "meses"
        promedio_text = "diario" if tipo_evolucion == 'diario' else "mensual"
        
        ticket_promedio = format_currency_int(
            total_ventas_periodo / num_periodos) if num_periodos != 0 else 0

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



@callback(
    Output('ventas-grafico-comparativa-vendedores', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-tipo-grafico', 'value'),
     Input('ventas-data-store', 'data'),  # 
     Input('ventas-theme-store', 'data')]
)
def update_comparativa_vendedores(session_data, tipo_grafico, data_store, theme):
    """
    Update comparative sales chart with enhanced visual appeal.
    """
    from utils import can_see_all_vendors

    try:
        # Solo mostrar si es administrador
        if not session_data or not can_see_all_vendors(session_data):
            return go.Figure().update_layout(
                height=10,  # Altura mínima permitida
                margin={'t': 0, 'b': 0, 'l': 0, 'r': 0},
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis={'visible': False, 'showgrid': False},
                yaxis={'visible': False, 'showgrid': False},
                showlegend=False
            )

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

        promedio_valores = [
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
            """Retorna color basado en volumen: rojo (bajo) a verde (alto)."""
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
                normalized_vol = (volumen_total - min_volumen) / (max_volumen -
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

        else:  # barras agrupadas
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
                        line=dict(color=color, width=2)
                    ),
                    hovertemplate="<b>%{fullData.name}</b> | 💰 %{customdata[0]} | 📊 %{customdata[1]} | 🎯 %{customdata[2]}<extra></extra>",
                    customdata=[[
                        format_currency_int(val),
                        f"🔥 +{format_currency_int(val - promedios_mensuales.get(mes, 0))}" if val > promedios_mensuales.get(mes, 0)
                        else f"📉 {format_currency_int(val - promedios_mensuales.get(mes, 0))}",
                        format_currency_int(volumen_total)
                    ] for mes, val in zip(all_months, valores_ordenados)]
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
        print(f"❌ [update_comparativa_vendedores] Error: {e}")
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
     Input('ventas-data-store', 'data'),  # 
     Input('ventas-theme-store', 'data')]
)
def update_area_charts_individuales(session_data, data_store, theme):
    """
    Create individual area charts for each vendor (4 per row, all vendors).
    """
    from utils import can_see_all_vendors

    try:
        theme_styles = get_theme_styles(theme)

        # Solo mostrar si es administrador
        if not session_data or not can_see_all_vendors(session_data):
            return go.Figure().update_layout(
                height=10,  # Altura mínima permitida
                margin={'t': 0, 'b': 0, 'l': 0, 'r': 0},
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis={'visible': False, 'showgrid': False},
                yaxis={'visible': False, 'showgrid': False},
                showlegend=False
            )
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
        print(f"❌ [update_area_charts_individuales] Error: {e}")
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


# ========== CALLBACKS DE DROPDOWNS Y INTERACCIONES ==========

@callback(
    Output('ventas-dropdown-cliente', 'options'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-data-store', 'data')]  # 
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
    Output('ventas-dropdown-cliente', 'value'),
    [Input('ventas-dropdown-vendedor', 'value')]
)
def reset_cliente_selection(vendedor):
    """Reset client selection when salesperson changes."""
    return 'Seleccione un cliente'


@callback(
    Output('ventas-total-recaudo-titulo', 'children'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-data-store', 'data')]  # 
)
def update_titulo_recaudo(session_data, dropdown_value, mes, data_store):
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
        print(f"❌ [update_titulo_recaudo] Error: {e}")
        return "Recaudo Total: $0"


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
    Output('ventas-titulo-principal', 'children'),
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
            return "Vendedores"

        if can_see_all_vendors(session_data):
            vendedor = dropdown_value if dropdown_value else 'Todos'
            title = "Vendedores"
            return title
        else:
            vendor = get_user_vendor_filter(session_data)
            title = f"Vendedores"
            return title
    except Exception as e:
        print(f"❌ [update_title] Error: {e}")
        return "Vendedores"

@callback(
    Output('ventas-subtitulo', 'children'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value')]
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
            parts.append("Todos los Vendedores")
            
        if mes and mes != 'Todos':
            parts.append(f"{mes}")
        else:
            parts.append("Todos los períodos")
            
        return " • ".join(parts)
        
    except Exception as e:
        print(f"❌ [update_subtitle] Error: {e}")
        return "Análisis completo de ventas y performance"


@callback(
    [Output('ventas-theme-store', 'data'),
     Output('ventas-theme-toggle', 'children'),
     Output('ventas-main-container', 'style')],
    [Input('ventas-theme-toggle', 'n_clicks')],
    [State('ventas-theme-store', 'data')]
)
def toggle_theme(n_clicks, current_theme):
    """
    Toggle between light and dark theme.
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
            # Mostrar para administradores con más ancho
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
    [Output('ventas-dropdown-vendedor', 'style'),
     Output('ventas-dropdown-mes', 'style'),
     Output('ventas-dropdown-cliente', 'style'),
     Output('ventas-dropdown-tipo-evolucion', 'style'),
     Output('ventas-dropdown-vista-recaudo', 'style'),
     Output('ventas-dropdown-tipo-grafico', 'style'),
     Output('ventas-heatmap-clientes', 'style'),
     Output('ventas-filtro-tendencia', 'style'),
     Output('ventas-dropdown-vendedor', 'className'),
     Output('ventas-dropdown-mes', 'className'),
     Output('ventas-dropdown-cliente', 'className'),
     Output('ventas-dropdown-tipo-evolucion', 'className'),
     Output('ventas-dropdown-vista-recaudo', 'className'),
     Output('ventas-dropdown-tipo-grafico', 'className'),
     Output('ventas-heatmap-clientes', 'className'),
     Output('ventas-filtro-tendencia', 'className')],
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
    
    # Estilo específico para dropdown del heatmap (letra más pequeña)
    heatmap_dropdown_style = get_dropdown_style(theme).copy()
    heatmap_dropdown_style.update({
        'fontFamily': 'Inter',
        'fontSize': '12px',  # Mantener tamaño específico
        'height': 'auto',    # Altura automática para multi-select
        'minHeight': '38px'  # Altura mínima
    })

    # CSS class for dark theme
    css_class = 'dash-dropdown dark-theme' if theme == 'dark' else 'dash-dropdown'
    
    # Clase específica para el dropdown del heatmap
    heatmap_css_class = f'{css_class} heatmap-dropdown'

    return \
        (
            # Styles
            vendedor_style, dropdown_style, dropdown_style,
            dropdown_style, vista_style, tipo_grafico_style, 
            heatmap_dropdown_style, dropdown_style,
            # Classes
            css_class, css_class, css_class, css_class,
            css_class, css_class, heatmap_css_class, css_class
        )


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

@callback(
    [Output('ventas-row1-container', 'style'),
     Output('ventas-row1-2-container', 'style'),      
     Output('ventas-row1-3-container', 'style'),
     Output('ventas-row-nueva-treemap', 'style'),      
     Output('ventas-row1-5-container', 'style'),
     Output('ventas-row2-container', 'style'),
     Output('ventas-row2-5-container', 'style'),
     Output('ventas-row4-container', 'style'),
     Output('ventas-row5-container', 'style'),
     Output('ventas-row6-container', 'style'),
     Output('ventas-row-heatmap', 'style'),
     Output('ventas-heatmap-top10', 'style'),     
     Output('ventas-heatmap-bottom10', 'style')], 
    [Input('ventas-theme-store', 'data'),
     Input('session-store', 'data')] 
)
def update_container_styles(theme, session_data):
    """
    Update styles for chart containers based on theme AND handle admin visibility.
    """
    from utils import can_see_all_vendors
    
    theme_styles = get_theme_styles(theme)

    # Estilo base para contenedores normales
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
    
    # Estilo para COMPLETAMENTE OCULTO (como si no existiera)
    hidden_completely = {
        'display': 'none',           # No se renderiza
        'height': '0px',             # Sin altura
        'padding': '0px',            # Sin padding
        'margin': '0px',             # Sin margin
        'border': 'none',            # Sin bordes
        'overflow': 'hidden',        # Oculta cualquier overflow
        'visibility': 'hidden',      # Invisible incluso si se muestra
        'position': 'absolute',      # Fuera del flujo de documento
        'top': '-9999px',           # Muy lejos de la vista
        'opacity': '0'              # Transparente
    }
    
    # Estilo especial para treemap
    treemap_style = base_style.copy()
    treemap_style.update({
        'background': 'linear-gradient(135deg, #ffffff, #f9fafb)' if theme == 'light' else theme_styles['paper_color']
    })
    
    # Determinar si mostrar secciones de admin
    try:
        is_admin = session_data and can_see_all_vendors(session_data)
    except:
        is_admin = False
    
    # Asignar estilos según permisos
    comparativa_style = base_style if is_admin else hidden_completely
    area_individual_style = base_style if is_admin else hidden_completely
    
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

    return [
        base_style,                    # ventas-row1-container (siempre visible)
        comparativa_style,             # ventas-row1-2-container (solo admin)
        area_individual_style,         # ventas-row1-3-container (solo admin)  
        base_style,
        base_style,                    # ventas-row1-5-container (siempre visible)
        base_style,                    # ventas-row2-container (siempre visible)
        treemap_style,                 # ventas-row2-5-container (siempre visible)
        base_style,                    # ventas-row4-container (siempre visible)
        base_style,                    # ventas-row5-container (siempre visible)
        base_style,                    # ventas-row6-container (siempre visible)
        base_style,
        button_style, 
        button_style
    ]


@callback(
    Output('ventas-metrics-cards', 'children'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-data-store', 'data'),
     Input('ventas-theme-store', 'data')]
)
def update_metric_cards(session_data, dropdown_value, mes, data_store, theme):
    """
    Actualizar las metric cards con los datos de ventas
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        is_dark = theme == 'dark'
        
        # Obtener resumen de datos
        resumen = analyzer.get_resumen_ventas(vendedor, mes)
        
        # Preparar datos para las cards
        metrics_data = [
            {
                'title': 'Ventas Totales',
                'value': format_currency_int(resumen['total_ventas']),
                'color': METRIC_COLORS['success'],
                'card_id': 'ventas-card-ventas-totales'
            },
            {
                'title': 'Ventas Netas',
                'value': format_currency_int(resumen['ventas_netas']),
                'color': METRIC_COLORS['primary'],
                'card_id': 'ventas-card-ventas-netas'
            },
            {
                'title': 'Devoluciones',
                'value': format_currency_int(resumen['total_devoluciones']),
                'color': METRIC_COLORS['danger'],
                'card_id': 'ventas-card-devoluciones'
            },
            {
                'title': 'Descuentos',
                'value': format_currency_int(resumen['total_descuentos']),
                'color': METRIC_COLORS['warning'],
                'card_id': 'ventas-card-descuentos'
            },
            {
                'title': 'Valor Promedio',
                'value': format_currency_int(resumen['ticket_promedio']),
                'color': METRIC_COLORS['purple'],
                'card_id': 'ventas-card-valor-promedio'
            },
            {
                'title': '# Facturas',
                'value': f"{resumen['num_facturas']:,}",
                'color': METRIC_COLORS['indigo'],
                'card_id': 'ventas-card-num-facturas'
            },
            {
                'title': '# Devoluciones',
                'value': f"{resumen['num_devoluciones']:,}",
                'color': METRIC_COLORS['orange'],
                'card_id': 'ventas-card-num-devoluciones'
            },
            {
                'title': 'Clientes',
                'value': f"{resumen['num_clientes']:,}",
                'color': METRIC_COLORS['teal'],
                'card_id': 'ventas-card-clientes'
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
    Output('ventas-heatmap-variaciones', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-heatmap-rango-meses', 'value'),
     Input('ventas-heatmap-top10', 'n_clicks'),
     Input('ventas-heatmap-bottom10', 'n_clicks'),
     Input('ventas-heatmap-clientes', 'value'),
     Input('ventas-data-store', 'data'),
     Input('ventas-theme-store', 'data')],
    [State('ventas-heatmap-top10', 'className'),
     State('ventas-heatmap-bottom10', 'className')]
)
def update_heatmap_variaciones(
        session_data, 
        dropdown_value, 
        rango_meses, 
        top10_clicks, 
        bottom10_clicks, 
        clientes_seleccionados, 
        data_store, 
        theme,
        top10_class, 
        bottom10_class):
    """
    Actualizar heatmap con 3 tipos de filtros.
    """
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
                [0.0, "rgba(185, 28, 28, 0.7)"],
                [0.15, "rgba(220, 38, 38, 0.7)"],
                [0.3, "rgba(239, 68, 68, 0.7)"],
                [0.4, "rgba(248, 113, 113, 0.7)"],
                [0.45, "rgba(251, 191, 36, 0.7)"],
                [0.5, "rgba(229, 231, 235, 0.7)"],
                [0.55, "rgba(132, 204, 22, 0.7)"],
                [0.6, "rgba(34, 197, 94, 0.7)"],
                [0.7, "rgba(22, 163, 74, 0.7)"],
                [0.85, "rgba(21, 128, 61, 0.7)"],
                [1.0, "rgba(22, 101, 52, 0.7)"]
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
    Output('ventas-heatmap-clientes', 'options'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-heatmap-rango-meses', 'value'),
     Input('ventas-data-store', 'data')]
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
    Output('ventas-heatmap-clientes', 'value'),
    [Input('ventas-heatmap-clientes', 'value')],
    prevent_initial_call=True
)
def limit_cliente_selection(selected_clientes):
    """Limitar selección a máximo 5 clientes"""
    if selected_clientes and len(selected_clientes) > 10:
        return selected_clientes[:10]
    return selected_clientes

@callback(
    [Output('ventas-heatmap-top10', 'className'),
     Output('ventas-heatmap-bottom10', 'className'),
     Output('ventas-heatmap-clientes', 'value', allow_duplicate=True)],
    [Input('ventas-heatmap-top10', 'n_clicks'),
     Input('ventas-heatmap-bottom10', 'n_clicks'),
     Input('ventas-heatmap-clientes', 'value')],
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

@callback(
    [Output('ventas-filtro-num-clientes', 'max'),
     Output('ventas-filtro-num-clientes', 'marks')],
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-data-store', 'data')]
)
def update_slider_clientes_config(session_data, dropdown_value, data_store):
    """
    Configurar dinámicamente el slider de número de clientes.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        
        # Obtener datos básicos para calcular total de clientes
        df = analyzer.filter_data(vendedor, 'Todos')
        ventas_reales = df[df['tipo'].str.contains('Remision', case=False, na=False)]
        
        if ventas_reales.empty:
            return 200, {10: '10', 50: '50', 100: '100', 200: '200+'}
        
        # Calcular número total de clientes únicos
        total_clientes = ventas_reales['cliente_completo'].nunique()
        
        # Ajustar máximo del slider
        max_clientes = min(max(total_clientes, 50), 500)  # Entre 50 y 500
        
        # Crear marcas dinámicas
        marks = {}
        step_size = max_clientes // 5
        for i in range(0, 6):
            value = min(10 + (i * step_size), max_clientes)
            if value == max_clientes:
                marks[value] = f'{value}+'
            else:
                marks[value] = str(value)
        
        return max_clientes, marks
        
    except Exception as e:
        print(f"❌ Error configurando slider de clientes: {e}")
        return 200, {10: '10', 50: '50', 100: '100', 200: '200+'}
    
@callback(
    [Output('ventas-filtro-dias-sin-venta', 'min'),
     Output('ventas-filtro-dias-sin-venta', 'max'),
     Output('ventas-filtro-dias-sin-venta', 'marks'),
     Output('ventas-filtro-dias-sin-venta', 'value')],
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-data-store', 'data')]
)
def update_slider_dias_sin_venta_config(
        session_data, 
        dropdown_value, 
        data_store):
    """
    Configurar dinámicamente el slider de días sin venta según los datos disponibles
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        
        # Obtener datos de días sin venta
        data = analyzer.get_dias_sin_venta_por_cliente(vendedor)
        
        if data.empty:
            return \
                (
                    0, 
                    365, 
                    {
                        0: '0', 30: '30', 60: '60', 90: '90', 
                        180: '180', 365: '365+'
                    }, 
                    30
                )
        
        # Calcular min y max reales
        min_dias = int(data['dias_sin_venta'].min())
        max_dias = int(data['dias_sin_venta'].max())
        
        # Ajustar valores para mejor UX
        min_slider = max(0, min_dias - 5)  # Dar un poco de margen
        max_slider = min(max_dias + 10, 730)  # Máximo 2 años
        
        # Crear marcas dinámicas inteligentes
        marks = {}
        
        if max_slider <= 90:
            # Para rangos cortos: cada 15 días
            step = 15
            
            for i in range(0, max_slider + 1, step):
                marks[i] = str(i)
        elif max_slider <= 365:
            # Para rangos medianos: cada 30 días
            step = 30
            for i in range(0, max_slider + 1, step):
                if i == 0:
                    marks[i] = '0'
                elif i >= 365:
                    marks[i] = '1 año+'
                else:
                    marks[i] = str(i)
        else:
            # Para rangos largos: marcas especiales
            marks = \
                {
                    0: '0',
                    30: '1 mes',
                    60: '2 meses', 
                    90: '3 meses',
                    180: '6 meses',
                    365: '1 año',
                    max_slider: f'{max_slider//30} meses+'
                }
        
        # Valor por defecto inteligente
        default_value = min(30, max_slider // 3)  # 30 días o 1/3 del máximo
        
        return min_slider, max_slider, marks, default_value
        
    except Exception as e:
        print(f"❌ Error configurando slider de días sin venta: {e}")
        # Configuración de fallback
        return \
            (
                0, 
                365, 
                {
                    0: '0', 30: '30', 60: '60', 90: '90', 
                    180: '180', 365: '365+'
                }, 
                30
            )
import numpy as np
import time
from datetime import datetime

import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from .helpers import VentasAnalysisHelper
from analyzers import VentasAnalyzer, EvaluacionAnalyzer
from utils import (
    format_currency_int,
    get_theme_styles,
    get_dropdown_style,
    get_selected_vendor
)

analyzer = VentasAnalyzer()

# On-demand initial data load with error handling
try:
    df = analyzer.load_data_from_firebase()
except Exception as e:
    print(f"⚠️ [VentasPage] Carga inicial falló (se recargará on-demand): {e}")
    df = pd.DataFrame()

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


layout = html.Div([
    # Store for theme
    dcc.Store(id='ventas-theme-store', data='light'),
    dcc.Store(id='ventas-data-store', data={'last_update': 0}),
    dcc.Store(id='ventas-rfm-cache-status', storage_type='memory'),

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
                    options=[{'label': m, 'value': m}
                             for m in analyzer.meses_list],
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

        html.Div(id="ventas-metrics-cards", children=[],
                 style={'marginBottom': '24px'}),

        html.Div([
            html.H3("Cumplimiento de Cuota", style={
                'textAlign': 'center',
                'marginBottom': '30px',
                'fontFamily': 'Inter',
                'fontSize': '19px',  # Reducido de 20px
                'fontWeight': '600'
            }),

            # Información explicativa
            html.Div([
                html.P([
                    "Análisis de Cumplimiento - Comparación de ventas reales vs objetivos mensual con progreso esperado según días transcurridos del mes"
                ], style={
                    'fontSize': '13px',
                    'color': '#6b7280',
                    'textAlign': 'center',
                    'marginBottom': '25px',  # Más espacio
                    'fontFamily': 'Inter',
                    'lineHeight': '1.5'
                })
            ]),

            # Layout de dos columnas
            html.Div([
                # Columna izquierda: Gráfico (2/3 del ancho)
                html.Div([
                    dcc.Graph(
                        id='ventas-grafico-cumplimiento-cuotas',
                        style={'height': '450px'}
                    )
                ], style={
                    'width': '66%',
                    'display': 'inline-block',
                    'verticalAlign': 'top',
                    'paddingRight': '20px'
                }),

                # Columna derecha: Panel de información (1/3 del ancho)
                html.Div([
                    html.Div(id='ventas-panel-info-cumplimiento', style={
                        'height': '450px',
                        'overflowY': 'auto',
                        'padding': '20px',
                        'borderRadius': '12px',
                        'border': '1px solid #e5e7eb'
                    })
                ], style={
                    'width': '32%',
                    'display': 'inline-block',
                    'verticalAlign': 'top'
                })
            ], style={
                'width': '100%',
                'display': 'flex',
                'gap': '10px'
            })

        ], id='ventas-row-cumplimiento-container', style={
            'borderRadius': '20px',  # Bordes más redondeados
            'padding': '30px',       # Más padding
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

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
            dcc.Graph(id='ventas-grafico-comparativa-vendedores')
        ], id='ventas-row1-2-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

        # Análisis de eficiencia ventas/clientes
        html.Div([
            html.H3("Eficiencia de Ventas por Cliente", style={
                'textAlign': 'center',
                'marginBottom': '20px',
                'fontFamily': 'Inter'
            }, id='ventas-efficiency-title'),

            dcc.Graph(id='ventas-efficiency-chart')

        ], id='ventas-efficiency-container', style={
            'borderRadius': '15px',
            'padding': '25px',
            'marginBottom': '20px',
            'backgroundColor': 'white',
            'border': '1px solid #e5e7eb'
        }),

        # Fila 1.5: Evolución de Ventas por Cliente Específico
        html.Div([
            html.H3("Evolución Ventas por Cliente + Análisis RFM+", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'}),

            # Contenedor principal con dos columnas
            html.Div([
                # Columna izquierda: Controles y gráfico
                html.Div([
                    # Controles
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
                                style={'fontFamily': 'Inter',
                                       'height': '44px'},
                                className='custom-dropdown'
                            )
                        ], style={
                            'width': '65%',
                            'display': 'inline-block',
                            'marginRight': '3%',
                            'verticalAlign': 'top'
                        }),

                        # Dropdown de tipo de evolución
                        html.Div([
                            html.Label("Período:", style={
                                'fontWeight': 'bold', 'marginBottom': '8px', 'fontFamily': 'Inter', 'fontSize': '14px'}),
                            dcc.Dropdown(
                                id='ventas-dropdown-tipo-evolucion',
                                options=[
                                    {'label': '📅 Diario', 'value': 'diario'},
                                    {'label': '📊 Mensual', 'value': 'mensual'}
                                ],
                                value='mensual',  # Cambiar default a mensual para mejor análisis de tendencias
                                style={'fontFamily': 'Inter',
                                       'height': '44px'},
                                className='custom-dropdown'
                            )
                        ], style={
                            'width': '30%',
                            'display': 'inline-block',
                            'verticalAlign': 'top'
                        })
                    ], style={'marginBottom': '20px'}),

                    # Gráfico principal
                    dcc.Graph(id='ventas-grafico-evolucion-cliente',
                              style={'height': '480px'})

                ], style={
                    'width': '70%',
                    'display': 'inline-block',
                    'paddingRight': '20px',
                    'verticalAlign': 'top'
                }),

                # Columna derecha: Panel de detalles RFM+
                html.Div([
                    html.H4("🎯 Análisis RFM+ del Cliente", style={
                        'fontFamily': 'Inter',
                        'fontSize': '16px',
                        'marginBottom': '15px',
                        'textAlign': 'center'
                    }),

                    # Contenedor del panel de detalles
                    html.Div(id='ventas-cliente-rfm-details', children=[
                        html.Div([
                            html.Div("📊", style={
                             'fontSize': '48px', 'textAlign': 'center', 'marginBottom': '15px'}),
                            html.P("Selecciona un cliente para ver su perfil RFM+ completo:",
                                   style={'textAlign': 'center', 'color': '#6b7280', 'fontFamily': 'Inter', 'fontSize': '13px', 'marginBottom': '15px'}),
                            html.Ul([
                                html.Li("📈 Scores de Recency, Frequency, Monetary y Trend", style={
                                    'fontSize': '11px', 'marginBottom': '5px'}),
                                html.Li("🎯 Categorización automática del cliente", style={
                                    'fontSize': '11px', 'marginBottom': '5px'}),
                                html.Li("📊 Análisis de tendencias (CAGR, variaciones)", style={
                                    'fontSize': '11px', 'marginBottom': '5px'}),
                                html.Li("💡 Recomendaciones personalizadas", style={
                                    'fontSize': '11px', 'marginBottom': '5px'}),
                                html.Li("⚠️ Alertas de riesgo o oportunidad", style={
                                    'fontSize': '11px', 'marginBottom': '0px'})
                            ], style={'color': '#6b7280', 'fontFamily': 'Inter', 'paddingLeft': '15px'})
                        ], style={
                            'textAlign': 'center',
                            'padding': '20px',
                            'color': '#9ca3af',
                            'backgroundColor': '#f9fafb',
                            'borderRadius': '8px',
                            'border': '2px dashed #e5e7eb'
                        })
                    ])

                ], style={
                    'width': '28%',
                    'display': 'inline-block',
                    'verticalAlign': 'top',
                    'paddingLeft': '10px'
                })

            ], style={'width': '100%'})

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
            html.H3("Análisis RFM de Clientes", style={
                'textAlign': 'center',
                'marginBottom': '25px',
                'fontFamily': 'Inter'
            }),

            # Información sobre RFM
            html.Div([
                html.P([
                    "📊 ", html.Strong(
                        "RFM Score"), " - Segmentación avanzada basada en:",
                    html.Br(),
                    "🔄 ", html.Strong(
                        "Recency"), " (Recencia): ¿Qué tan recientemente compró?",
                    html.Br(),
                    "📈 ", html.Strong(
                        "Frequency"), " (Frecuencia): ¿Qué tan frecuentemente compra?",
                    html.Br(),
                    "💰 ", html.Strong(
                        "Monetary"), " (Monetario): ¿Cuánto dinero gasta?"
                ], style={
                    'fontSize': '12px',
                    'color': '#6b7280',
                    'textAlign': 'center',
                    'marginBottom': '20px',
                    'fontFamily': 'Inter',
                    'lineHeight': '1.5'
                })
            ]),

            # Contenedor de filtros RFM
            html.Div([
                # Filtro de número de clientes (izquierda)
                html.Div([
                    html.Label("Número de Clientes:", style={
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
                        value=30,  # Valor por defecto reducido para RFM
                        marks={
                            10: '10', 20: '20', 30: '30', 50: '50',
                            100: '100', 150: '150', 200: '200+'
                        },
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ], style={
                    'width': '48%',
                    'display': 'inline-block',
                    'marginRight': '4%'
                }),

                # Filtro de categoría RFM (derecha)
                html.Div([
                    html.Label("Categoría RFM:", style={
                        'fontWeight': 'bold',
                        'marginBottom': '10px',
                        'fontFamily': 'Inter',
                        'fontSize': '14px'
                    }),
                    dcc.Dropdown(
                        id='ventas-filtro-categoria-rfm',
                        options=[
                            {'label': '🏆 Campeones', 'value': '🏆 Campeones'},
                            {'label': '💎 Clientes Leales',
                                'value': '💎 Clientes Leales'},
                            {'label': '⭐ Potenciales Leales',
                                'value': '⭐ Potenciales Leales'},
                            {'label': '🌱 Nuevos Clientes',
                                'value': '🌱 Nuevos Clientes'},
                            {'label': '🚀 Prometedores', 'value': '🚀 Prometedores'},
                            {'label': '⚠️ Necesitan Atención',
                                'value': '⚠️ Necesitan Atención'},
                            {'label': '🔴 En Riesgo', 'value': '🔴 En Riesgo'},
                            {'label': '🆘 No se pueden perder',
                                'value': '🆘 No se pueden perder'},
                            {'label': '😴 Hibernando', 'value': '😴 Hibernando'},
                            {'label': '💸 Perdidos', 'value': '💸 Perdidos'},
                            {'label': '📊 Todas las Categorías', 'value': 'todas'}
                        ],
                        value='todas',
                        placeholder="Filtrar por categoría RFM...",
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

        # Agregar esta sección después del contenedor de cumplimiento de cuotas
        # Fila de Evaluación de Desempeño
        html.Div([
            html.H3("🏆 Evaluación de Desempeño Integral", style={
                'textAlign': 'center',
                'marginBottom': '20px',
                'fontFamily': 'Inter',
                'fontSize': '22px',
                'fontWeight': '600'
            }),

            # Controles de visualización
            html.Div([
                html.Div([
                    html.Label("Métrica Principal:", style={
                        'fontWeight': '600',
                        'fontSize': '13px',
                        'marginBottom': '5px',
                        'display': 'block'
                    }),
                    dcc.RadioItems(
                        id='ventas-eval-metric-selector',
                        options=[
                            {'label': '📊 Score Total', 'value': 'score_total'},
                            {'label': '⚡ Eficiencia', 'value': 'eficiencia'},
                            {'label': '💎 Calidad', 'value': 'calidad'},
                            {'label': '🎯 Score Distribución', 'value': 'score'}
                        ],
                        value='score_total',
                        inline=True,
                        style={'fontSize': '12px'},
                        inputStyle={'marginRight': '8px', 'marginLeft': '15px'}
                    )
                ], style={'marginBottom': '20px', 'textAlign': 'center'}),

                # Checkbox para expandir detalles
                dcc.Checklist(
                    id='ventas-eval-show-details',
                    options=[
                        {'label': '📋 Mostrar detalles por indicador', 'value': 'show'}
                    ],
                    value=['show'],
                    style={'marginBottom': '15px',
                           'textAlign': 'center', 'fontSize': '13px'}
                )
            ]),

            # Podio de los top 3
            html.Div(id='ventas-eval-podium', style={'marginBottom': '30px'}),

            # Tabla general con todos los vendedores
            html.Div(id='ventas-eval-table-container'),

        ], id='ventas-eval-container', style={
            'borderRadius': '20px',
            'padding': '30px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%',
            'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'display': 'none'  # Se mostrará solo para admins
        })

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
            return \
                (
                    [
                        html.Span("🔄", style={'marginRight': '8px'}),
                        'Actualizar Datos'
                    ],
                    False
                )
        else:
            return \
                (
                    [
                        html.Span("⚠️", style={'marginRight': '8px'}),
                        'Reintentar'
                    ],
                    False
                )

    # Estado normal
    return \
        (
            [
                html.Span("🔄", style={'marginRight': '8px'}),
                'Actualizar Datos'
            ],
            False
        )


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
    title_style = \
        {
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
            max_monto = ((max_monto // 100000) + 1) * \
                100000  # Redondear a 100k
            step = 25000
        else:
            max_monto = ((max_monto // 1000000) + 1) * \
                1000000  # Redondear a 1M
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
                {'fill': 'rgba(0, 119, 182, 0.2)',
                 'border': 'rgb(0, 119, 182)'},
                {'fill': 'rgba(0, 180, 216, 0.2)',
                 'border': 'rgb(0, 180, 216)'},
                {'fill': 'rgba(144, 224, 239, 0.2)',
                 'border': 'rgb(144, 224, 239)'},
                {'fill': 'rgba(202, 240, 248, 0.2)',
                 'border': 'rgb(202, 240, 248)'},
                {'fill': 'rgba(2, 62, 138, 0.2)', 'border': 'rgb(2, 62, 138)'},
                {'fill': 'rgba(3, 4, 94, 0.2)', 'border': 'rgb(3, 4, 94)'},
                {'fill': 'rgba(211, 211, 211, 0.2)',
                 'border': 'rgb(211, 211, 211)'}
            ]

        fill_colors = \
            [
                pastel_colors_with_borders[i % len(
                    pastel_colors_with_borders)]['fill']
                for i in range(len(data))
            ]

        border_colors = \
            [
                pastel_colors_with_borders[i % len(
                    pastel_colors_with_borders)]['border']
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
        data_sorted['rank'] = sorted(
            range(1, len(data_sorted) + 1), reverse=True)
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
                    line=dict(color=border_colors[i %
                              len(border_colors)], width=1.5)
                ),
                text=[row['cliente_completo'][:100] +
                      "..." if len(row['cliente_completo']) > 100 else row['cliente_completo']],
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
            font=dict(family="Inter", size=12,
                      color=theme_styles['text_color']),
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
        data = analyzer.get_analisis_convenios(
            vendedor, mes="Todos")  # Don't apply month filter
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
                line=dict(color='rgba(144, 238, 144, 0.4)', width=3),
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
                    bar_colors.append(
                        'rgba(144, 238, 144, 0.4)')  # Light green
                    border_colors.append(
                        'rgba(144, 238, 144, 0.9)')  # Light green
                elif valores[i] < valores[i-1]:
                    # Descendente - Rosa pastel
                    bar_colors.append('rgba(255, 182, 193, 0.4)')  # Light pink
                    border_colors.append(
                        'rgba(255, 182, 193, 0.9)')  # Light pink
                else:
                    bar_colors.append('rgba(173, 216, 230, 0.4)')  # Light blue
                    border_colors.append(
                        'rgba(173, 216, 230, 0.9)')  # Light blue

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
            data = data[data['dias_sin_venta'] >=
                        dias_filtro] if not data.empty else data

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
        data['dias_sin_venta'] = pd.to_numeric(
            data['dias_sin_venta'], errors='coerce')
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
            fig.update_layout(
                height=500, paper_bgcolor=theme_styles['plot_bg'])
            return fig

        def get_categoria_y_color(dias, alpha=0.4, is_dark_theme=False):
            """
            Categorizar días y obtener color según urgencia y tema.
            """
            if is_dark_theme:
                if dias < 30:
                    # Verde vibrante
                    return "Reciente (< 1 mes)", f"rgba(34, 197, 94, {alpha})"
                elif dias < 60:
                    # Amarillo dorado
                    return "1-2 meses", f"rgba(251, 191, 36, {alpha})"
                elif dias < 90:
                    # Naranja vibrante
                    return "2-3 meses", f"rgba(245, 158, 11, {alpha})"
                elif dias < 180:
                    # Rojo vibrante
                    return "3-6 meses", f"rgba(239, 68, 68, {alpha})"
                else:
                    # Rojo oscuro intenso
                    return "6+ meses", f"rgba(153, 27, 27, {alpha})"
            else:
                if dias < 30:
                    # Verde bosque
                    return "Reciente (< 1 mes)", f"rgba(21, 128, 61, {alpha})"
                elif dias < 60:
                    # Naranja tierra
                    return "1-2 meses", f"rgba(180, 83, 9, {alpha})"
                elif dias < 90:
                    # Naranja rojizo oscuro
                    return "2-3 meses", f"rgba(154, 52, 18, {alpha})"
                elif dias < 180:
                    # Rojo granate
                    return "3-6 meses", f"rgba(153, 27, 27, {alpha})"
                else:
                    return "6+ meses", f"rgba(69, 10, 10, {alpha})"

        # Aplicar categorización
        data = data.copy()
        data['categoria'] = \
            data['dias_sin_venta'].apply(lambda x: get_categoria_y_color(x)[0])
        data['color'] = \
            data['dias_sin_venta'].apply(lambda x: get_categoria_y_color(x)[1])
        data['border_color'] = \
            data['dias_sin_venta'].apply(
                lambda x: get_categoria_y_color(x, alpha=0.9)[1])

        # Create labels optimizadas
        labels = []

        for _, row in data.iterrows():
            cliente = row['cliente_completo']
            dias = int(row['dias_sin_venta'])
            categoria = row['categoria']

            # Truncar nombre si es muy largo
            cliente_corto = cliente[:50] + \
                "..." if len(cliente) > 50 else cliente

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
            textfont=dict(
                size=10, color=theme_styles['text_color'], family='Inter', weight='bold'),
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
                font=dict(
                    size=14, color=theme_styles['text_color'], family="Inter")
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
            paper_bgcolor=theme_styles.get(
                'plot_bg', 'white') if 'theme_styles' in locals() else 'white'
        )
        return fig


@callback(
    Output('ventas-grafico-evolucion-cliente', 'figure'),
    [Input('ventas-dropdown-cliente', 'value'),
     Input('ventas-dropdown-tipo-evolucion', 'value'),
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
    Gráfico de evolución de cliente mejorado con indicadores RFM+ y categoría.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        theme_styles = get_theme_styles(theme)

        if cliente == 'Seleccione un cliente':
            fig = go.Figure()
            tipo_text = "diaria" if tipo_evolucion == 'diario' else "mensual"
            fig.add_annotation(
                text=f"Seleccione un cliente para ver su evolución {tipo_text} con análisis RFM+",
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
                height=500,
                plot_bgcolor=theme_styles['plot_bg'],
                paper_bgcolor=theme_styles['plot_bg'],
                font=dict(family="Inter", size=12,
                          color=theme_styles['text_color'])
            )
            return fig

        # ✨ NUEVO: Obtener datos RFM+ del cliente
        client_rfm_details = analyzer.get_client_rfm_details(cliente, vendedor)

        # Obtener datos de evolución temporal
        if tipo_evolucion == 'mensual':
            data = analyzer.get_ventas_por_rango_meses(vendedor, 1, 12)
            if data and not data.get('mensual', pd.DataFrame()).empty:
                data_mensual = data['mensual']
                data_cliente = data_mensual[
                    data_mensual['cliente_completo'] == cliente
                ].sort_values('mes_año')

                if not data_cliente.empty:
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
            data = analyzer.get_evolucion_cliente(cliente, vendedor)

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
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=500,
                plot_bgcolor=theme_styles['plot_bg'],
                paper_bgcolor=theme_styles['plot_bg'],
                font=dict(family="Inter", size=12,
                          color=theme_styles['text_color'])
            )
            return fig

        # Calcular totales para título
        total_ventas_periodo = data['valor_neto'].sum()
        num_periodos = len(data)

        # ✨ CREAR GRÁFICO MEJORADO CON INDICADORES RFM+
        fig = go.Figure()

        # Determinar colores según categoría RFM+ (si disponible)
        if client_rfm_details:
            categoria = client_rfm_details['categoria']
            # Mapeo de colores por categoría
            color_map = {
                "🏆 Campeones Ascendentes": "rgba(34, 197, 94, 0.4)",
                "⚠️ Campeones en Declive": "rgba(245, 158, 11, 0.4)",
                "🚀 Clientes Estrella": "rgba(59, 130, 246, 0.4)",
                "💎 Leales Estables": "rgba(16, 185, 129, 0.4)",
                "📉 En Caída Libre": "rgba(239, 68, 68, 0.4)",
                "⭐ Potenciales con Momentum": "rgba(132, 204, 22, 0.4)",
                "🌱 Nuevos en Desarrollo": "rgba(34, 197, 94, 0.4)",
                "🔥 Oportunidades Calientes": "rgba(249, 115, 22, 0.4)",
                "⚠️ Atención Urgente": "rgba(239, 68, 68, 0.4)",
                "🆘 Rescate Inmediato": "rgba(220, 38, 38, 0.4)",
                "😴 Hibernando Estables": "rgba(107, 114, 128, 0.4)",
                "💸 Perdidos": "rgba(75, 85, 99, 0.4)",
                "🔄 Comportamiento Irregular": "rgba(139, 92, 246, 0.4)"
            }

            border_color_map = {k: v.replace("0.8", "1.0").replace(
                "0.6", "1.0") for k, v in color_map.items()}

            bar_color = color_map.get(categoria, "rgba(107, 114, 128, 0.6)")
            border_color = border_color_map.get(
                categoria, "rgba(107, 114, 128, 1.0)")
        else:
            # Colores por defecto si no hay datos RFM+
            bar_color = "rgba(59, 130, 246, 0.6)"
            border_color = "rgba(59, 130, 246, 1.0)"

        # Añadir barras de evolución
        fig.add_trace(go.Bar(
            x=data['fecha_str'],
            y=data['valor_neto'],
            marker=dict(
                color=bar_color,
                line=dict(color=border_color, width=1.5),
                opacity=0.9
            ),
            text=[format_currency_int(
                val) if val > 50000 else '' for val in data['valor_neto']],
            textposition='outside',
            textfont=dict(size=10, color=theme_styles['text_color']),
            hovertemplate="<b>%{x}</b><br>" +
                         "Ventas: %{customdata[0]}<br>" +
                         "Facturas: %{customdata[1]}<br>" +
                         "<extra></extra>",
            customdata=[[format_currency_int(val), facturas] for val, facturas in zip(
                data['valor_neto'], data['documento_id'])]
        ))

        # ✨ AÑADIR LÍNEA DE TENDENCIA si hay suficientes datos
        if len(data) >= 3 and client_rfm_details:
            # Calcular línea de tendencia simple
            x_numeric = list(range(len(data)))
            y_values = data['valor_neto'].values

            # Regresión lineal simple
            x_mean = np.mean(x_numeric)
            y_mean = np.mean(y_values)

            # Calcular pendiente y intercepto
            numerator = np.sum((np.array(x_numeric) - x_mean)
                               * (y_values - y_mean))
            denominator = np.sum((np.array(x_numeric) - x_mean) ** 2)

            if denominator != 0:
                slope = numerator / denominator
                intercept = y_mean - slope * x_mean

                # Generar línea de tendencia
                trend_y = [slope * x + intercept for x in x_numeric]

                # Determinar color de tendencia
                trend_color = "rgba(34, 197, 94, 0.4)" if slope > 0 else "rgba(239, 68, 68, 0.4)"

                fig.add_trace(go.Scatter(
                    x=data['fecha_str'],
                    y=trend_y,
                    mode='lines',
                    name='Tendencia',
                    line=dict(
                        color=trend_color,
                        width=2.2,
                        dash='dash'
                    ),
                    hovertemplate="Línea de tendencia<br>%{y}<extra></extra>",
                    showlegend=False
                ))

        # ✨ CONSTRUIR TÍTULO MEJORADO CON INFORMACIÓN RFM+
        cliente_corto = cliente[:80] + '...' if len(cliente) > 80 else cliente
        total_ventas_str = format_currency_int(total_ventas_periodo)

        periodo_text = "días" if tipo_evolucion == 'diario' else "meses"
        promedio_text = "diario" if tipo_evolucion == 'diario' else "mensual"

        ticket_promedio = format_currency_int(
            total_ventas_periodo / num_periodos) if num_periodos != 0 else 0

        # Título base
        titulo_base = (
            f"<span style='font-size:17px; font-weight:bold;'>"
            f"{cliente_corto}</span><br>"
            f"<span style='font-size:14px; margin-top:5px; display:inline-block;'>"
            f"💰 Total: {total_ventas_str} | 📊 Ticket promedio {promedio_text}: {ticket_promedio} | 📈 {num_periodos} {periodo_text}</span>"
        )

        # ✨ AÑADIR INFORMACIÓN RFM+ SI ESTÁ DISPONIBLE
        if client_rfm_details:
            categoria = client_rfm_details['categoria']
            scores = client_rfm_details['scores']
            tendencias = client_rfm_details['tendencias']

            # Línea con scores individuales
            scores_info = (
                f"<br><span style='font-size:11px; margin-top:5px; display:inline-block;'>"
                f"📊 RFM+T: R{scores['recency']} F{scores['frequency']} M{scores['monetary']} T{scores['trend']} | "
                f"🔄 CAGR 6M: {tendencias['cagr_6m']:+.1f}% | "
                f"📈 Var 3M: {tendencias['variacion_3m']:+.1f}% | "
                f"⚡ Reciente: {tendencias['variacion_reciente']:+.1f}%</span>"
            )

            titulo_completo = titulo_base + scores_info
        else:
            titulo_completo = titulo_base + (
                f"<br><span style='font-size:11px; margin-top:5px; display:inline-block; color:#f59e0b;'>"
                f"⚠️ Datos RFM+ no disponibles - Recarga los datos</span>"
            )

        # ✨ LAYOUT MEJORADO
        fig.update_layout(
            title=dict(
                text=titulo_completo,
                x=0.5,
                font=dict(color=theme_styles['text_color']),
                pad=dict(t=50)
            ),
            height=550,  # Aumentar altura para acomodar más información
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=12,
                      color=theme_styles['text_color']),
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
            # Más margen superior para el título expandido
            margin=dict(t=140, b=80, l=80, r=40)
        )

        # ✨ AÑADIR ANOTACIONES CONTEXTUALES si hay datos RFM+
        if client_rfm_details:
            tendencias = client_rfm_details['tendencias']

            # Añadir alerta visual si hay problemas críticos
            if tendencias['cagr_6m'] < -20:
                fig.add_annotation(
                    text="🚨 ALERTA: Decrecimiento severo",
                    xref="paper", yref="paper",
                    x=0.02, y=0.98,
                    showarrow=False,
                    font=dict(size=12, color="white"),
                    bgcolor="rgba(239, 68, 68, 0.9)",
                    bordercolor="rgba(239, 68, 68, 1)",
                    borderwidth=1,
                    borderpad=4
                )
            elif tendencias['cagr_6m'] > 30:
                fig.add_annotation(
                    text="🔥 OPORTUNIDAD: Crecimiento excepcional",
                    xref="paper", yref="paper",
                    x=0.02, y=0.98,
                    showarrow=False,
                    font=dict(size=12, color="white"),
                    bgcolor="rgba(34, 197, 94, 0.9)",
                    bordercolor="rgba(34, 197, 94, 1)",
                    borderwidth=1,
                    borderpad=4
                )

        return fig

    except Exception as e:
        print(f"❌ [update_evolucion_cliente_enhanced] Error: {e}")
        import traceback
        traceback.print_exc()

        # Figura de error mejorada
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error cargando evolución del cliente: {str(e)[:100]}...",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#ef4444")
        )
        fig.update_layout(
            height=400,
            plot_bgcolor='white' if 'theme_styles' not in locals(
            ) else theme_styles['plot_bg'],
            paper_bgcolor='white' if 'theme_styles' not in locals(
            ) else theme_styles['plot_bg']
        )
        return fig


@callback(
    Output('ventas-cliente-rfm-details', 'children'),
    [Input('ventas-dropdown-cliente', 'value'),
     Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-data-store', 'data'),
     Input('ventas-theme-store', 'data')]
)
def update_client_rfm_details_panel(cliente, session_data, dropdown_value, data_store, theme):
    """
    Panel lateral con detalles RFM+ del cliente seleccionado.
    """
    try:
        if cliente == 'Seleccione un cliente':
            return \
                html.Div(id='ventas-cliente-rfm-details', children=[
                    html.Div([
                        html.Div("📊", style={
                            'fontSize': '48px', 'textAlign': 'center', 'marginBottom': '15px'}),
                        html.P("Selecciona un cliente para ver su perfil RFM+ completo:",
                               style={'textAlign': 'center', 'color': '#6b7280', 'fontFamily': 'Inter', 'fontSize': '13px', 'marginBottom': '15px'}),
                        html.Ul([
                            html.Li("📈 Scores de Recency, Frequency, Monetary y Trend", style={
                                'fontSize': '11px', 'marginBottom': '5px'}),
                            html.Li("🎯 Categorización automática del cliente", style={
                                'fontSize': '11px', 'marginBottom': '5px'}),
                            html.Li("📊 Análisis de tendencias (CAGR, variaciones)", style={
                                'fontSize': '11px', 'marginBottom': '5px'}),
                            html.Li("💡 Recomendaciones personalizadas", style={
                                'fontSize': '11px', 'marginBottom': '5px'}),
                            html.Li("⚠️ Alertas de riesgo o oportunidad", style={
                                'fontSize': '11px', 'marginBottom': '0px'})
                        ], style={'color': '#6b7280', 'fontFamily': 'Inter', 'paddingLeft': '15px'})
                    ], style={
                        'textAlign': 'center',
                        'padding': '20px',
                        'color': '#9ca3af',
                        'backgroundColor': '#f9fafb',
                        'borderRadius': '8px',
                        'border': '2px dashed #e5e7eb'
                    })
                ])

        vendedor = get_selected_vendor(session_data, dropdown_value)
        theme_styles = get_theme_styles(theme)

        # Obtener detalles RFM+
        client_details = analyzer.get_client_rfm_details(cliente, vendedor)

        if not client_details:
            return \
                html.Div(id='ventas-cliente-rfm-details', children=[
                    html.Div([
                        html.Div("📊", style={
                            'fontSize': '48px', 'textAlign': 'center', 'marginBottom': '15px'}),
                        html.P("Selecciona un cliente para ver su perfil RFM+ completo:",
                               style={'textAlign': 'center', 'color': '#6b7280', 'fontFamily': 'Inter', 'fontSize': '13px', 'marginBottom': '15px'}),
                        html.Ul([
                            html.Li("📈 Scores de Recency, Frequency, Monetary y Trend", style={
                                'fontSize': '11px', 'marginBottom': '5px'}),
                            html.Li("🎯 Categorización automática del cliente", style={
                                'fontSize': '11px', 'marginBottom': '5px'}),
                            html.Li("📊 Análisis de tendencias (CAGR, variaciones)", style={
                                'fontSize': '11px', 'marginBottom': '5px'}),
                            html.Li("💡 Recomendaciones personalizadas", style={
                                'fontSize': '11px', 'marginBottom': '5px'}),
                            html.Li("⚠️ Alertas de riesgo o oportunidad", style={
                                'fontSize': '11px', 'marginBottom': '0px'})
                        ], style={'color': '#6b7280', 'fontFamily': 'Inter', 'paddingLeft': '15px'})
                    ], style={
                        'textAlign': 'center',
                        'padding': '20px',
                        'color': '#9ca3af',
                        'backgroundColor': '#f9fafb',
                        'borderRadius': '8px',
                        'border': '2px dashed #e5e7eb'
                    })
                ])

        # Construir panel de detalles
        categoria = client_details['categoria']
        scores = client_details['scores']
        metricas = client_details['metricas']
        tendencias = client_details['tendencias']
        recomendacion = client_details['recomendacion']

        # Determinar color de la categoría
        color_map = {
            "🏆 Campeones Ascendentes": "#22c55e",
            "⚠️ Campeones en Declive": "#f59e0b",
            "🚀 Clientes Estrella": "#3b82f6",
            "💎 Leales Estables": "#10b981",
            "📉 En Caída Libre": "#ef4444",
            "⭐ Potenciales con Momentum": "#84cc16",
            "🌱 Nuevos en Desarrollo": "#22c55e",
            "🔥 Oportunidades Calientes": "#f97316",
            "⚠️ Atención Urgente": "#ef4444",
            "🆘 Rescate Inmediato": "#dc2626",
            "😴 Hibernando Estables": "#6b7280",
            "💸 Perdidos": "#4b5563",
            "🔄 Comportamiento Irregular": "#8b5cf6"
        }

        category_color = color_map.get(categoria, "#6b7280")

        panel = html.Div([
            # Header con categoría
            html.Div([
                html.H4(categoria, style={
                    'margin': '0',
                    'color': 'white',
                    'fontFamily': 'Inter',
                    'fontSize': '16px',
                    'textAlign': 'center'
                })
            ], style={
                'backgroundColor': category_color,
                'padding': '15px',
                'borderRadius': '8px 8px 0 0',
                'marginBottom': '15px'
            }),

            # Scores RFM+
            html.Div([
                html.H5("📊 Scores RFM+", style={'fontFamily': 'Inter',
                        'fontSize': '14px', 'marginBottom': '10px'}),
                html.Div([
                    html.Div([
                        html.Span("R", style={'fontWeight': 'bold'}),
                        html.Span(f" {scores['recency']}/5",
                                  style={'color': category_color})
                    ], style={'margin': '5px 0'}),
                    html.Div([
                        html.Span("F", style={'fontWeight': 'bold'}),
                        html.Span(f" {scores['frequency']}/5",
                                  style={'color': category_color})
                    ], style={'margin': '5px 0'}),
                    html.Div([
                        html.Span("M", style={'fontWeight': 'bold'}),
                        html.Span(f" {scores['monetary']}/5",
                                  style={'color': category_color})
                    ], style={'margin': '5px 0'}),
                    html.Div([
                        html.Span("T", style={'fontWeight': 'bold'}),
                        html.Span(f" {scores['trend']}/5",
                                  style={'color': category_color})
                    ], style={'margin': '5px 0'})
                ])
            ], style={'marginBottom': '15px', 'marginLeft': '12px'}),

            # Métricas clave
            html.Div([
                html.H5("📈 Métricas Clave", style={
                        'fontFamily': 'Inter', 'fontSize': '14px', 'marginBottom': '10px'}),
                html.Div([
                    html.P(f"💰 Valor Total: {format_currency_int(metricas['valor_total'])}",
                           style={'margin': '3px 0', 'fontSize': '12px'}),
                    html.P(f"🔄 Total Compras: {metricas['total_compras']}",
                           style={'margin': '3px 0', 'fontSize': '12px'}),
                    html.P(f"📅 Última Compra: {metricas['dias_ultima_compra']} días",
                           style={'margin': '3px 0', 'fontSize': '12px'}),
                    html.P(f"💳 Valor Promedio: {format_currency_int(metricas['valor_promedio'])}",
                           style={'margin': '3px 0', 'fontSize': '12px'})
                ])
            ], style={'marginBottom': '15px', 'marginLeft': '12px'}),

            # Tendencias
            html.Div([
                html.H5("📊 Análisis de Tendencias", style={
                        'fontFamily': 'Inter', 'fontSize': '14px', 'marginBottom': '10px'}),
                html.Div([
                    html.P([
                        html.Span("CAGR 6M: "),
                        html.Span(f"{tendencias['cagr_6m']:+.1f}%",
                                  style={'color': '#22c55e' if tendencias['cagr_6m'] > 0 else '#ef4444', 'fontWeight': 'bold'})
                    ], style={'margin': '3px 0', 'fontSize': '12px'}),
                    html.P([
                        html.Span("Var 3M: "),
                        html.Span(f"{tendencias['variacion_3m']:+.1f}%",
                                  style={'color': '#22c55e' if tendencias['variacion_3m'] > 0 else '#ef4444', 'fontWeight': 'bold'})
                    ], style={'margin': '3px 0', 'fontSize': '12px'}),
                    html.P([
                        html.Span("Consistencia: "),
                        html.Span(f"{tendencias['consistencia']:.1f}%",
                                  style={'color': '#22c55e' if tendencias['consistencia'] > 70 else '#f59e0b' if tendencias['consistencia'] > 40 else '#ef4444'})
                    ], style={'margin': '3px 0', 'fontSize': '12px'})
                ])
            ], style={'marginBottom': '15px', 'marginLeft': '12px'}),

            # Recomendación
            html.Div([
                html.H5("💡 Recomendación", style={
                        'fontFamily': 'Inter', 'fontSize': '14px', 'marginBottom': '10px'}),
                html.P(recomendacion, style={
                    'fontSize': '12px',
                    'padding': '10px',
                    'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                    'borderRadius': '6px',
                    'lineHeight': '1.4'
                })
            ])

        ], style={
            'backgroundColor': theme_styles['paper_color'],
            'padding': '0',
            'borderRadius': '8px',
            'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
            'border': f'1px solid {theme_styles["line_color"]}'
        })

        return panel

    except Exception as e:
        print(f"❌ Error en panel RFM+ del cliente: {e}")
        return html.Div([
            html.P("Error cargando detalles RFM+",
                   style={'textAlign': 'center', 'color': '#ef4444', 'fontFamily': 'Inter'})
        ])


@callback(
    Output('ventas-grafico-comparativa-vendedores', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-data-store', 'data'),  #
     Input('ventas-theme-store', 'data')]
)
def update_comparativa_vendedores(session_data, data_store, theme):
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


@callback(
    [Output('ventas-row1-container', 'style'),
     Output('ventas-row1-2-container', 'style'),
     Output('ventas-row-cumplimiento-container', 'style'),
     Output('ventas-row-nueva-treemap', 'style'),
     Output('ventas-row1-5-container', 'style'),
     Output('ventas-row2-container', 'style'),
     Output('ventas-row2-5-container', 'style'),
     Output('ventas-row4-container', 'style'),
     Output('ventas-row5-container', 'style'),
     Output('ventas-row6-container', 'style')],
    [Input('ventas-theme-store', 'data'),
     Input('session-store', 'data')]
)
def update_container_styles_simple(theme, session_data):
    """
    Update styles for chart containers (versión simplificada sin controles de cumplimiento).
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

    # Estilo para COMPLETAMENTE OCULTO
    hidden_completely = {
        'display': 'none',
        'height': '0px',
        'padding': '0px',
        'margin': '0px',
        'border': 'none',
        'overflow': 'hidden',
        'visibility': 'hidden',
        'position': 'absolute',
        'top': '-9999px',
        'opacity': '0'
    }

    # Estilo especial para sección de cumplimiento (dos columnas)
    cumplimiento_style = base_style.copy()
    cumplimiento_style.update({
        'background': f'linear-gradient(135deg, {theme_styles["paper_color"]} 0%, rgba(59, 130, 246, 0.05) 100%)',
        'border': '1px solid rgba(59, 130, 246, 0.1)'
    })

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
        base_style,
        comparativa_style,             # ventas-row1-2-container (solo admin)
        cumplimiento_style,            # ventas-row-cumplimiento-container
        base_style,                    # ventas-row-nueva-treemap
        # ventas-row1-5-container (siempre visible)
        base_style,
        # ventas-row2-container (siempre visible)
        base_style,
        # ventas-row2-5-container (siempre visible)
        treemap_style,
        # ventas-row4-container (siempre visible)
        base_style,
        # ventas-row5-container (siempre visible)
        base_style,
        # ventas-row6-container (siempre visible)
        base_style
    ]


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
        ventas_reales = df[df['tipo'].str.contains(
            'Remision', case=False, na=False)]

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


@callback(
    Output('ventas-treemap-unificado', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-filtro-num-clientes', 'value'),
     Input('ventas-filtro-categoria-rfm', 'value'),
     Input('ventas-data-store', 'data'),
     Input('ventas-theme-store', 'data')]
)
def update_treemap_rfm_plus(
        session_data,
        dropdown_value,
        num_clientes,
        filtro_categoria,
        data_store,
        theme):
    """
    Treemap actualizado con RFM+ Score (incluye análisis de tendencias).
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        theme_styles = get_theme_styles(theme)

        # Obtener datos RFM+ completos
        # data = analyzer.calculate_enhanced_rfm_scores(vendedor)
        data = analyzer.calculate_enhanced_rfm_scores(vendedor, use_cache=True)

        if data.empty:
            return create_empty_figure("No hay datos RFM+ disponibles", theme_styles)

        # Aplicar filtro de categoría si se especifica
        if filtro_categoria and filtro_categoria != 'todas':
            data = data[data['categoria_rfm'] == filtro_categoria]

        # Ordenar por RFM Score numérico (mejores primero)
        data = data.sort_values('rfm_numeric', ascending=False)

        # Limitar número de clientes
        data = data.head(num_clientes)

        if data.empty:
            return create_empty_figure(f"No hay clientes con categoría '{filtro_categoria}'", theme_styles)

        # Define colors for each RFM+ category with transparency
        color_map_rfm_plus = {
            "🏆 Campeones Ascendentes": "rgba(6, 214, 160, 0.4)",
            "💎 Leales Estables": "rgba(52, 211, 153, 0.4)",
            "🚀 Clientes Estrella": "rgba(16, 185, 129, 0.4)",
            "⭐ Potenciales con Momentum": "rgba(163, 230, 53, 0.4)",
            "🌱 Nuevos en Desarrollo": "rgba(132, 204, 22, 0.4)",
            "🔥 Oportunidades Calientes": "rgba(250, 204, 21, 0.4)",
            "⚠️ Campeones en Declive": "rgba(251, 191, 36, 0.4)",
            "⚠️ Atención Urgente": "rgba(251, 146, 60, 0.4)",
            "🔄 Comportamiento Irregular": "rgba(249, 115, 22, 0.4)",
            "📉 En Caída Libre": "rgba(248, 113, 113, 0.4)",
            "🆘 Rescate Inmediato": "rgba(239, 68, 68, 0.4)",
            "😴 Hibernando Estables": "rgba(220, 38, 38, 0.4)",
            "💸 Perdidos": "rgba(185, 28, 28, 0.4)"
        }

        border_map_rfm_plus = {k: v.replace("0.4", "1.0").replace(
            "0.6", "1.0") for k, v in color_map_rfm_plus.items()}

        # Preparar datos para treemap
        ids = [f"C{i}" for i in range(len(data))]
        labels = []
        colors = []
        border_colors = []
        values = []
        text_labels = []

        for i, (_, row) in enumerate(data.iterrows()):
            cliente = str(row['cliente_completo'])[
                :60] + ("..." if len(str(row['cliente_completo'])) > 60 else "")
            categoria = row['categoria_rfm']
            valor = row['monetary']
            frequency = int(row['frequency'])
            recency = int(row['recency_days'])
            rfm_score = row['rfm_score']
            rfm_numeric = row['rfm_numeric']
            cagr_6m = row['cagr_6m']
            trend_score = int(row['T'])

            # Construir elementos
            labels.append(f"{categoria.split()[0]} {cliente}")
            colors.append(color_map_rfm_plus.get(
                categoria, "rgba(107, 114, 128, 0.6)"))
            border_colors.append(border_map_rfm_plus.get(
                categoria, "rgba(107, 114, 128, 1.0)"))
            values.append(valor)

            # Texto optimizado con información RFM+ y tendencias
            valor_fmt = f"${valor/1000000:.1f}M" if valor >= 1000000 else f"${valor/1000:.0f}K" if valor >= 1000 else f"${valor:,.0f}".replace(
                ',', '.')

            # Icono de tendencia
            if cagr_6m > 15:
                trend_icon = "🚀"
            elif cagr_6m > 5:
                trend_icon = "📈"
            elif cagr_6m > -5:
                trend_icon = "➡️"
            elif cagr_6m > -15:
                trend_icon = "📉"
            else:
                trend_icon = "⚠️"

            text_labels.append(
                f"<b>{categoria}</b><br>"
                f"<b>{cliente}</b><br>"
                f"<span style='font-size:14px;font-weight:bold'>{valor_fmt} {trend_icon}</span><br>"
                f"<span style='font-size:10px;opacity:0.9'>RFM+T: {rfm_score} | CAGR: {cagr_6m:+.1f}% | {frequency} compras</span>"
            )

        # Crear treemap mejorado
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
                line=dict(width=1.5, color=border_colors)
            ),
            hovertemplate="<b>%{customdata[0]}</b><br>" +
            "Cliente: <b>%{customdata[1]}<br></b>" +
            "Valor Total: %{customdata[2]}<br>" +
            "RFM+ Score: %{customdata[3]}<br>" +
            "CAGR 6M: %{customdata[4]}%<br>" +
            "Frecuencia: %{customdata[5]} compras<br>" +
            "Última compra: hace %{customdata[6]} días<br>" +
            "Score Numérico: %{customdata[7]:.2f}<br>" +
            "Trend Score: %{customdata[8]}/5<br>" +
            "<extra></extra>",
            customdata=[[
                row['categoria_rfm'],
                row['cliente_completo'],
                format_currency_int(row['monetary']),
                row['rfm_score'],
                f"{row['cagr_6m']:+.1f}",
                int(row['frequency']),
                int(row['recency_days']),
                row['rfm_numeric'],
                int(row['T'])
            ] for _, row in data.iterrows()],
            sort=True,
            tiling=dict(packing="binary", pad=2)
        ))

        # Layout mejorado
        categoria_filter = filtro_categoria if filtro_categoria != 'todas' else 'Todas las Categorías'

        fig.update_layout(
            height=650,
            margin=dict(t=70, b=10, l=5, r=5),
            font=dict(family="Inter", color=theme_styles['text_color']),
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            title=dict(
                text=f"Top {len(data)} Clientes - Análisis RFM+ con Tendencias - {categoria_filter}<br><sub>🏆 Ascendentes | ⚠️ En Declive | 🚀 Estrella | 💎 Estables | 📉 Caída | ⭐ Momentum | 🔥 Calientes</sub>",
                x=0.5, y=0.98,
                font=dict(size=16, color=theme_styles['text_color'])
            )
        )

        return fig

    except Exception as e:
        print(f"❌ Error en treemap RFM+: {e}")
        import traceback
        traceback.print_exc()
        return create_empty_figure("Error procesando datos RFM+", theme_styles)


@callback(
    Output('ventas-filtro-categoria-rfm', 'options'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-data-store', 'data')]
)
def update_categorias_rfm_plus_options(session_data, dropdown_value, data_store):
    """
    Actualizar opciones de categorías RFM+ disponibles (nuevas categorías con tendencias).
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)

        # Obtener datos RFM+ y extraer categorías únicas
        rfm_data = analyzer.calculate_enhanced_rfm_scores(vendedor)

        if rfm_data.empty:
            return [{'label': '📊 Todas las Categorías', 'value': 'todas'}]

        # Obtener categorías únicas presentes en los datos
        categorias_presentes = rfm_data['categoria_rfm'].unique().tolist()

        # Definir todas las categorías posibles con sus etiquetas
        all_categories = {
            "🏆 Campeones Ascendentes": "🏆 Campeones Ascendentes",
            "⚠️ Campeones en Declive": "⚠️ Campeones en Declive",
            "🚀 Clientes Estrella": "🚀 Clientes Estrella",
            "💎 Leales Estables": "💎 Leales Estables",
            "📉 En Caída Libre": "📉 En Caída Libre",
            "⭐ Potenciales con Momentum": "⭐ Potenciales con Momentum",
            "🌱 Nuevos en Desarrollo": "🌱 Nuevos en Desarrollo",
            "🔥 Oportunidades Calientes": "🔥 Oportunidades Calientes",
            "⚠️ Atención Urgente": "⚠️ Atención Urgente",
            "🆘 Rescate Inmediato": "🆘 Rescate Inmediato",
            "😴 Hibernando Estables": "😴 Hibernando Estables",
            "💸 Perdidos": "💸 Perdidos",
            "🔄 Comportamiento Irregular": "🔄 Comportamiento Irregular"
        }

        options = []

        # Añadir "Todas" siempre
        options.append({'label': '📊 Todas las Categorías', 'value': 'todas'})

        # Añadir solo las categorías que están presentes en los datos
        for categoria in categorias_presentes:
            if categoria in all_categories:
                options.append({
                    'label': all_categories[categoria],
                    'value': categoria
                })

        # Ordenar alfabéticamente (excepto "Todas" que va primero)
        options_sorted = [options[0]] + \
            sorted(options[1:], key=lambda x: x['label'])

        return options_sorted

    except Exception as e:
        print(f"❌ Error actualizando categorías RFM+: {e}")
        return [{'label': '📊 Todas las Categorías', 'value': 'todas'}]


@callback(
    [Output('ventas-dropdown-vendedor', 'style'),
     Output('ventas-dropdown-mes', 'style'),
     Output('ventas-dropdown-cliente', 'style'),
     Output('ventas-dropdown-tipo-evolucion', 'style'),
     Output('ventas-dropdown-vista-recaudo', 'style'),
     Output('ventas-filtro-categoria-rfm', 'style'),
     Output('ventas-dropdown-vendedor', 'className'),
     Output('ventas-dropdown-mes', 'className'),
     Output('ventas-dropdown-cliente', 'className'),
     Output('ventas-dropdown-tipo-evolucion', 'className'),
     Output('ventas-dropdown-vista-recaudo', 'className'),
     Output('ventas-filtro-categoria-rfm', 'className')],
    [Input('ventas-theme-store', 'data'),
     Input('session-store', 'data')]
)
def update_dropdown_styles_with_rfm(theme, session_data):
    """
    Update dropdown styles including new RFM category filter.
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

    return \
        (
            # Styles
            vendedor_style, dropdown_style, dropdown_style,
            dropdown_style, vista_style,
            dropdown_style,
            # Classes
            css_class, css_class, css_class, css_class,
            css_class, css_class
        )


@callback(
    Output('ventas-rfm-insights-panel', 'children'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-filtro-categoria-rfm', 'value'),
     Input('ventas-data-store', 'data'),
     Input('ventas-theme-store', 'data')]
)
def update_rfm_insights(
        session_data,
        dropdown_value,
        filtro_categoria,
        data_store,
        theme):
    """
    Generar panel de insights RFM+ dinámico con análisis de último mes finalizado.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        theme_styles = get_theme_styles(theme)

        # 📅 Información del período de análisis
        from utils import get_ultimo_mes_finalizado
        fecha_inicio, fecha_fin = get_ultimo_mes_finalizado()

        # Obtener datos RFM+ completos
        rfm_data = analyzer.calculate_enhanced_rfm_scores(vendedor)

        if rfm_data.empty:
            return html.Div([
                html.Div([
                    html.Span(
                        "📊", style={'fontSize': '48px', 'display': 'block', 'marginBottom': '15px'}),
                    html.P("No hay suficientes datos para generar insights RFM+.", style={
                        'textAlign': 'center', 'color': '#7f8c8d', 'fontFamily': 'Inter', 'fontSize': '14px'
                    }),
                    html.P("Asegúrate de que hay ventas registradas en los últimos meses.", style={
                        'textAlign': 'center', 'color': '#9ca3af', 'fontFamily': 'Inter', 'fontSize': '12px'
                    })
                ], style={
                    'textAlign': 'center',
                    'padding': '40px 20px',
                    'backgroundColor': theme_styles['paper_color'],
                    'borderRadius': '12px',
                    'border': f'2px dashed {theme_styles["line_color"]}'
                })
            ])

        # 📅 Banner informativo sobre el período de análisis
        periodo_info = html.Div([
            html.Div([
                html.Div([
                    html.Span(
                        "📅", style={'fontSize': '18px', 'marginRight': '10px'}),
                    html.Span("Período de Análisis RFM+", style={
                        'fontWeight': 'bold', 'fontSize': '14px', 'color': theme_styles['text_color']
                    })
                ], style={'marginBottom': '8px'}),
                html.Div([
                    html.Span(f"Datos analizados hasta: ",
                              style={'fontSize': '12px'}),
                    html.Strong(f"{fecha_fin.strftime('%d de %B, %Y')}", style={
                        'color': '#3b82f6', 'fontSize': '12px'
                    })
                ], style={'marginBottom': '4px'}),
                html.Div([
                    html.Span("(Último mes completamente finalizado para garantizar precisión)", style={
                        'fontSize': '10px', 'opacity': '0.8', 'fontStyle': 'italic'
                    })
                ])
            ], style={
                'backgroundColor': 'rgba(59, 130, 246, 0.08)',
                'padding': '15px',
                'borderRadius': '10px',
                'border': '1px solid rgba(59, 130, 246, 0.2)',
                'marginBottom': '25px',
                'color': theme_styles['text_color']
            })
        ])

        # Generar insights usando la función corregida
        insights = analyzer.get_rfm_plus_insights(rfm_data)

        # Crear componentes del panel
        components = [periodo_info]

        # 1. KPIs principales con análisis de tendencias
        kpis = insights["kpis"]

        kpi_cards = html.Div([
            # Card 1: Total Clientes
            html.Div([
                html.H4(f"{kpis['total_customers']:,}", style={
                    'margin': '0', 'fontSize': '28px', 'color': '#3b82f6', 'fontFamily': 'Inter', 'fontWeight': 'bold'
                }),
                html.P("Clientes Analizados", style={
                    'margin': '0', 'fontSize': '12px', 'color': '#6b7280', 'fontFamily': 'Inter'
                }),
                html.Div([
                    html.Span(f"↗️ {kpis['customers_growing']}", style={
                              'fontSize': '10px', 'color': '#22c55e', 'marginRight': '8px'}),
                    html.Span(f"↘️ {kpis['customers_declining']}", style={
                              'fontSize': '10px', 'color': '#ef4444'})
                ], style={'marginTop': '5px'})
            ], style={
                'textAlign': 'center', 'padding': '20px 15px', 'margin': '5px',
                'backgroundColor': theme_styles['paper_color'],
                'borderRadius': '12px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)',
                'border': f'1px solid {theme_styles["line_color"]}',
                'flex': '1', 'minWidth': '140px'
            }),

            # Card 2: Valor Promedio
            html.Div([
                html.H4(format_currency_int(kpis['avg_order_value']), style={
                    'margin': '0', 'fontSize': '28px', 'color': '#10b981', 'fontFamily': 'Inter', 'fontWeight': 'bold'
                }),
                html.P("Valor Promedio", style={
                    'margin': '0', 'fontSize': '12px', 'color': '#6b7280', 'fontFamily': 'Inter'
                }),
                html.Div([
                    html.Span("💰 Por transacción", style={
                              'fontSize': '10px', 'color': '#6b7280'})
                ], style={'marginTop': '5px'})
            ], style={
                'textAlign': 'center', 'padding': '20px 15px', 'margin': '5px',
                'backgroundColor': theme_styles['paper_color'],
                'borderRadius': '12px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)',
                'border': f'1px solid {theme_styles["line_color"]}',
                'flex': '1', 'minWidth': '140px'
            }),

            # Card 3: CAGR Promedio (NUEVO)
            html.Div([
                html.H4(f"{kpis['avg_cagr']:+.1f}%", style={
                    'margin': '0', 'fontSize': '28px',
                    'color': '#22c55e' if kpis['avg_cagr'] > 0 else '#ef4444',
                    'fontFamily': 'Inter', 'fontWeight': 'bold'
                }),
                html.P("CAGR Promedio", style={
                    'margin': '0', 'fontSize': '12px', 'color': '#6b7280', 'fontFamily': 'Inter'
                }),
                html.Div([
                    html.Span("📈 Últimos 6 meses", style={
                              'fontSize': '10px', 'color': '#6b7280'})
                ], style={'marginTop': '5px'})
            ], style={
                'textAlign': 'center', 'padding': '20px 15px', 'margin': '5px',
                'backgroundColor': theme_styles['paper_color'],
                'borderRadius': '12px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)',
                'border': f'1px solid {theme_styles["line_color"]}',
                'flex': '1', 'minWidth': '140px'
            }),

            # Card 4: Recencia Promedio
            html.Div([
                html.H4(f"{kpis['avg_recency']:.0f}", style={
                    'margin': '0', 'fontSize': '28px',
                    'color': '#ef4444' if kpis['avg_recency'] > 60 else '#f59e0b' if kpis['avg_recency'] > 30 else '#22c55e',
                    'fontFamily': 'Inter', 'fontWeight': 'bold'
                }),
                html.P("Días Prom. Última Compra", style={
                    'margin': '0', 'fontSize': '12px', 'color': '#6b7280', 'fontFamily': 'Inter'
                }),
                html.Div([
                    html.Span("⏱️ Desde el corte", style={
                              'fontSize': '10px', 'color': '#6b7280'})
                ], style={'marginTop': '5px'})
            ], style={
                'textAlign': 'center', 'padding': '20px 15px', 'margin': '5px',
                'backgroundColor': theme_styles['paper_color'],
                'borderRadius': '12px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.05)',
                'border': f'1px solid {theme_styles["line_color"]}',
                'flex': '1', 'minWidth': '140px'
            })
        ], style={
            'display': 'flex', 'gap': '10px', 'marginBottom': '25px',
            'flexWrap': 'wrap', 'justifyContent': 'space-around'
        })

        components.append(kpi_cards)

        # 2. Alertas críticas (si las hay)
        if insights.get("alerts"):
            alerts_section = html.Div([
                html.H4("🚨 Alertas Críticas", style={
                    'marginBottom': '15px', 'fontFamily': 'Inter', 'fontSize': '16px',
                    'color': theme_styles['text_color']
                }),
                html.Div([
                    html.Div([
                        html.Div([
                            html.Span("⚠️" if alert["level"] == "high" else "🚨", style={
                                'fontSize': '16px', 'marginRight': '10px'
                            }),
                            html.Span(alert["message"], style={
                                'fontSize': '13px', 'fontFamily': 'Inter', 'fontWeight': '500'
                            })
                        ], style={
                            'padding': '12px 15px',
                            'backgroundColor': 'rgba(239, 68, 68, 0.1)' if alert["level"] == "critical" else 'rgba(245, 158, 11, 0.1)',
                            'border': '1px solid rgba(239, 68, 68, 0.3)' if alert["level"] == "critical" else '1px solid rgba(245, 158, 11, 0.3)',
                            'borderRadius': '8px',
                            'marginBottom': '8px'
                        })
                    ]) for alert in insights["alerts"]
                ])
            ], style={'marginBottom': '25px'})

            components.append(alerts_section)

        # 3. Distribución por categorías (gráfico horizontal compacto)
        distribution_data = insights["distribution"]
        if distribution_data:
            categories = list(distribution_data.keys())
            percentages = [distribution_data[cat]["percentage"]
                           for cat in categories]

            # Colores por categoría
            color_map_rfm_plus = {
                "🏆 Campeones Ascendentes": "#22c55e",
                "⚠️ Campeones en Declive": "#f59e0b",
                "🚀 Clientes Estrella": "#3b82f6",
                "💎 Leales Estables": "#10b981",
                "📉 En Caída Libre": "#ef4444",
                "⭐ Potenciales con Momentum": "#84cc16",
                "🌱 Nuevos en Desarrollo": "#22c55e",
                "🔥 Oportunidades Calientes": "#f97316",
                "⚠️ Atención Urgente": "#ef4444",
                "🆘 Rescate Inmediato": "#dc2626",
                "😴 Hibernando Estables": "#6b7280",
                "💸 Perdidos": "#4b5563",
                "🔄 Comportamiento Irregular": "#8b5cf6"
            }

            colors = [color_map_rfm_plus.get(
                cat, "#6b7280") for cat in categories]

            distribution_chart = dcc.Graph(
                figure=go.Figure(
                    data=[go.Bar(
                        y=categories,
                        x=percentages,
                        orientation='h',
                        marker=dict(color=colors, opacity=0.8),
                        text=[f"{p}% ({distribution_data[cat]['count']} clientes)" for p, cat in zip(
                            percentages, categories)],
                        textposition='inside',
                        textfont=dict(color='white', size=10, family='Inter'),
                        hovertemplate="<b>%{y}</b><br>%{x}% de clientes<br>Ingresos: " +
                        "<br>".join([f"{format_currency_int(distribution_data[cat]['revenue'])}" for cat in categories]) +
                        "<extra></extra>"
                    )]
                ).update_layout(
                    height=max(350, len(categories) * 35),
                    margin=dict(t=20, b=20, l=250, r=80),
                    plot_bgcolor=theme_styles['plot_bg'],
                    paper_bgcolor=theme_styles['plot_bg'],
                    font=dict(family="Inter",
                              color=theme_styles['text_color']),
                    xaxis=dict(title="% de Clientes", showgrid=True,
                               gridcolor=theme_styles['grid_color']),
                    yaxis=dict(title="", showgrid=False),
                    showlegend=False
                ),
                style={'height': f"{max(350, len(categories) * 35)}px"},
                config={'displayModeBar': False}
            )

            components.append(html.Div([
                html.H4("📊 Distribución por Categorías RFM+", style={
                    'marginBottom': '15px', 'fontFamily': 'Inter', 'fontSize': '16px',
                    'color': theme_styles['text_color']
                }),
                distribution_chart
            ], style={'marginBottom': '25px'}))

        # 4. Análisis de tendencias (NUEVO)
        trend_analysis = insights.get("trend_analysis", {})
        if trend_analysis:
            trend_section = html.Div([
                html.H4("📈 Análisis de Tendencias", style={
                    'marginBottom': '15px', 'fontFamily': 'Inter', 'fontSize': '16px',
                    'color': theme_styles['text_color']
                }),

                html.Div([
                    # Clientes en crecimiento
                    html.Div([
                        html.Div([
                            html.H5(f"{trend_analysis['growing_count']}", style={
                                'margin': '0', 'fontSize': '24px', 'color': '#22c55e', 'fontFamily': 'Inter'
                            }),
                            html.P("Clientes Creciendo", style={
                                'margin': '0', 'fontSize': '12px', 'color': '#6b7280', 'fontFamily': 'Inter'
                            }),
                            html.P(f"💰 {format_currency_int(trend_analysis['growing_revenue'])}", style={
                                'margin': '5px 0 0 0', 'fontSize': '11px', 'color': '#22c55e', 'fontFamily': 'Inter'
                            })
                        ], style={
                            'textAlign': 'center', 'padding': '15px',
                            'backgroundColor': 'rgba(34, 197, 94, 0.1)',
                            'borderRadius': '10px', 'border': '1px solid rgba(34, 197, 94, 0.3)'
                        })
                    ], style={'flex': '1', 'margin': '5px'}),

                    # Clientes en declive
                    html.Div([
                        html.Div([
                            html.H5(f"{trend_analysis['declining_count']}", style={
                                'margin': '0', 'fontSize': '24px', 'color': '#ef4444', 'fontFamily': 'Inter'
                            }),
                            html.P("Clientes en Declive", style={
                                'margin': '0', 'fontSize': '12px', 'color': '#6b7280', 'fontFamily': 'Inter'
                            }),
                            html.P(f"⚠️ {format_currency_int(trend_analysis['declining_revenue'])}", style={
                                'margin': '5px 0 0 0', 'fontSize': '11px', 'color': '#ef4444', 'fontFamily': 'Inter'
                            })
                        ], style={
                            'textAlign': 'center', 'padding': '15px',
                            'backgroundColor': 'rgba(239, 68, 68, 0.1)',
                            'borderRadius': '10px', 'border': '1px solid rgba(239, 68, 68, 0.3)'
                        })
                    ], style={'flex': '1', 'margin': '5px'})

                ], style={'display': 'flex', 'gap': '10px'})

            ], style={'marginBottom': '25px'})

            components.append(trend_section)

        # 5. Oportunidades de alto impacto
        opportunities = insights.get("opportunities", [])
        if opportunities:
            opp_section = html.Div([
                html.H4("🔥 Oportunidades de Alto Impacto", style={
                    'marginBottom': '15px', 'fontFamily': 'Inter', 'fontSize': '16px',
                    'color': theme_styles['text_color']
                }),

                html.Div([
                    html.Div([
                        html.Div([
                            html.Strong(opp['customer'][:50] + "..." if len(opp['customer']) > 50 else opp['customer'], style={
                                'fontSize': '13px', 'fontFamily': 'Inter', 'display': 'block', 'marginBottom': '5px'
                            }),
                            html.Div([
                                html.Span(opp['category'], style={
                                          'fontSize': '11px', 'color': '#6b7280', 'marginRight': '10px'}),
                                html.Span(f"CAGR: {opp['cagr']:+.1f}%", style={
                                    'fontSize': '11px', 'fontWeight': 'bold',
                                    'color': '#22c55e' if opp['cagr'] > 0 else '#ef4444'
                                })
                            ], style={'marginBottom': '5px'}),
                            html.Div([
                                html.Span(f"💰 {format_currency_int(opp['revenue'])}", style={
                                    'fontSize': '12px', 'fontWeight': 'bold', 'color': '#3b82f6'
                                })
                            ])
                        ], style={
                            'padding': '12px',
                            'backgroundColor': theme_styles['paper_color'],
                            'borderRadius': '8px',
                            'border': f'1px solid {theme_styles["line_color"]}',
                            'margin': '5px 0'
                        })
                    ]) for opp in opportunities[:5]
                ])

            ], style={'marginBottom': '25px'})

            components.append(opp_section)

        # 6. Recomendaciones prioritarias
        recommendations = insights.get("recommendations", [])
        if recommendations:
            rec_section = html.Div([
                html.H4("🎯 Recomendaciones Prioritarias", style={
                    'marginBottom': '15px', 'fontFamily': 'Inter', 'fontSize': '16px',
                    'color': theme_styles['text_color']
                }),

                html.Div([
                    html.Div([
                        html.Div([
                            html.Span(f"{rec['priority']}", style={
                                'backgroundColor': '#ef4444' if rec['priority'] == 'Urgente' else '#f59e0b' if rec['priority'] == 'Alta' else '#3b82f6',
                                'color': 'white', 'padding': '4px 8px', 'borderRadius': '12px',
                                'fontSize': '10px', 'fontWeight': 'bold', 'fontFamily': 'Inter'
                            })
                        ], style={'marginBottom': '8px'}),

                        html.H5(rec['action'], style={
                            'margin': '0 0 8px 0', 'fontFamily': 'Inter', 'fontSize': '14px',
                            'color': theme_styles['text_color']
                        }),

                        html.P([
                            html.Strong("Categoría: "), rec['category']
                        ], style={
                            'margin': '0 0 5px 0', 'fontSize': '12px', 'color': '#6b7280',
                            'fontFamily': 'Inter'
                        }),

                        html.P([
                            html.Strong("Impacto: "), rec['impact']
                        ], style={
                            'margin': '0', 'fontSize': '12px', 'color': '#6b7280',
                            'fontFamily': 'Inter'
                        })
                    ], style={
                        'backgroundColor': theme_styles['paper_color'],
                        'padding': '15px', 'borderRadius': '8px',
                        'boxShadow': '0 2px 4px rgba(0,0,0,0.05)',
                        'border': f'1px solid {theme_styles["line_color"]}',
                        'margin': '5px', 'flex': '1', 'minWidth': '280px'
                    })
                    for rec in recommendations[:4]], style={
                    'display': 'flex', 'gap': '10px', 'flexWrap': 'wrap'
                })
            ])

            components.append(rec_section)

        return components

    except Exception as e:
        print(f"❌ Error generando insights RFM: {e}")
        import traceback
        traceback.print_exc()

        return html.Div([
            html.Div([
                html.Span(
                    "⚠️", style={'fontSize': '48px', 'display': 'block', 'marginBottom': '15px'}),
                html.P("Error generando insights RFM+", style={
                    'textAlign': 'center', 'color': '#ef4444', 'fontFamily': 'Inter', 'fontSize': '16px',
                    'marginBottom': '10px'
                }),
                html.P(f"Detalles: {str(e)[:100]}...", style={
                    'textAlign': 'center', 'color': '#6b7280', 'fontFamily': 'Inter', 'fontSize': '12px'
                }),
                html.P("Intenta recargar los datos usando el botón 'Actualizar Datos'.", style={
                    'textAlign': 'center', 'color': '#6b7280', 'fontFamily': 'Inter', 'fontSize': '12px'
                })
            ], style={
                'textAlign': 'center',
                'padding': '40px 20px',
                'backgroundColor': 'rgba(239, 68, 68, 0.05)',
                'borderRadius': '12px',
                'border': '2px solid rgba(239, 68, 68, 0.2)'
            })
        ])


@callback(
    Output('ventas-rfm-cache-status', 'data'),
    Input('ventas-dropdown-vendedor', 'value'),
    prevent_initial_call=True
)
def clear_cache_on_vendor_change(vendedor):
    """
    Opcional: Limpiar cache cuando cambie el vendedor principal
    """
    try:
        analyzer = VentasAnalyzer()
        analyzer.clear_rfm_cache()
        return {'status': 'cache_cleared', 'vendor': vendedor}
    except:
        return {'status': 'error'}


@callback(
    Output('ventas-grafico-cumplimiento-cuotas', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-data-store', 'data'),
     Input('ventas-theme-store', 'data')]
)
def update_cumplimiento_cuotas_chart(
        session_data,
        dropdown_value,
        mes,
        data_store,
        theme):
    """
    Gráfico corregido con mejor visualización y días hábiles.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        theme_styles = get_theme_styles(theme)

        data = analyzer.get_cumplimiento_cuotas(vendedor, mes)

        if data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos de cuotas disponibles para el período seleccionado",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False,
                font=dict(size=16, color=theme_styles['text_color'])
            )
            fig.update_layout(
                height=450,
                plot_bgcolor=theme_styles['plot_bg'],
                paper_bgcolor=theme_styles['plot_bg']
            )
            return fig

        fig = go.Figure()

        vendedores = data['vendedor'].tolist()
        cumplimiento_pct = data['cumplimiento_pct'].tolist()
        estados = data['estado'].tolist()
        colores = data['color'].tolist()
        progreso_esperado = data['progreso_esperado_pct'].iloc[0] if len(
            data) > 0 else 0
        mes_finalizado = data['mes_finalizado'].iloc[0] if len(
            data) > 0 else True

        # Para un vendedor individual - Gauge mejorado
        if len(vendedores) == 1:
            cumplimiento_actual = cumplimiento_pct[0]
            estado_actual = estados[0]
            color_actual = colores[0]

            fig.add_trace(go.Indicator(
                mode="gauge+number+delta",
                value=cumplimiento_actual,
                domain={'x': [0, 1], 'y': [0.1, 0.9]},
                delta={
                    'reference': progreso_esperado,
                    'suffix': '%',
                    'valueformat': '.1f',
                    'font': {'size': 14}
                },
                number={'suffix': '%', 'font': {'size': 24}},
                gauge={
                    'axis': {
                        'range': [None, max(150, cumplimiento_actual + 20)],
                        'tickcolor': theme_styles['text_color'],
                        'tickfont': {'color': theme_styles['text_color']}
                    },
                    'bar': {'color': color_actual, 'thickness': 0.8},
                    'bgcolor': theme_styles['plot_bg'],
                    'borderwidth': 2,
                    'bordercolor': theme_styles['line_color'],
                    'steps': [
                        {'range': [0, progreso_esperado],
                            'color': 'rgba(156, 163, 175, 0.3)'},
                        {'range': [progreso_esperado, 100],
                            'color': 'rgba(156, 163, 175, 0.5)'},
                        {'range': [
                            100, max(150, cumplimiento_actual + 20)], 'color': 'rgba(34, 197, 94, 0.2)'}
                    ],
                    'threshold': {
                        'line': {'color': '#ef4444', 'width': 3},
                        'thickness': 0.75,
                        'value': 100
                    }
                }
            ))

        else:
            min_y = max(0, min(cumplimiento_pct) - 15)
            max_y = max(cumplimiento_pct) + 15

            fig.add_trace(go.Scatter(
                name='Cumplimiento',
                x=vendedores,
                y=cumplimiento_pct,
                mode='lines+markers',
                line=dict(color='#3b82f6', width=4, shape='spline'),
                marker=dict(
                    size=14,
                    color=colores,
                    line=dict(color='white', width=3),
                    symbol='circle'
                ),
                text=[f"{p:.1f}%" for p in cumplimiento_pct],
                textposition='top center',
                textfont=dict(
                    size=11, color=theme_styles['text_color'], family='Inter'),
                hovertemplate="<b>%{x}</b><br>" +
                "Cumplimiento: %{y:.1f}%<br>" +
                "Estado: %{customdata[0]}<br>" +
                "Ventas: %{customdata[1]}<br>" +
                "Objetivo: %{customdata[2]}<br>" +
                "<extra></extra>",
                customdata=[[
                    estado,
                    format_currency_int(ventas_reales),
                    format_currency_int(cuota)
                ] for estado, ventas_reales, cuota in zip(
                    data['estado'].tolist(),
                    data['ventas_reales'].tolist(),
                    data['cuota'].tolist()
                )]
            ))

            # Línea de referencia del 100% (objetivo)
            fig.add_hline(
                y=100,
                line_dash="dash",
                line_color="#ef4444",
                line_width=2,
                annotation_text="Objetivo 100%",
                annotation_position="top right",
                annotation_font={'color': '#ef4444', 'size': 12}
            )

            # Línea de progreso esperado solo si el mes no está finalizado
            if not mes_finalizado:
                fig.add_hline(
                    y=progreso_esperado,
                    line_dash="dot",
                    line_color="#f59e0b",
                    line_width=2,
                    annotation_text=f"Progreso Esperado {progreso_esperado:.1f}%",
                    annotation_position="top left",
                    annotation_font={'color': '#f59e0b', 'size': 12}
                )

            # Anotaciones de estado
            text_mapping = {
                "Cumplido": "CUMPLIDO",
                "No Cumplió": "NO CUMPLIÓ",
                "Cumpliendo": "CUMPLIENDO",
                "Adelantado": "ADELANTADO",
                "Atrasado": "ATRASADO",
                "En Progreso": "EN PROGRESO"
            }

            for i, (vendedor_name, estado, cumpl) in enumerate(zip(vendedores, estados, cumplimiento_pct)):
                fig.add_annotation(
                    x=vendedor_name,
                    y=cumpl + (max_y * 0.06),
                    text=estado,
                    showarrow=False,
                    font=dict(size=11, weight='bold'),
                    xanchor='center',
                    yanchor='bottom'
                )

            # Configurar rango Y mejorado
            fig.update_yaxes(range=[min_y, max_y])

        fig.update_layout(
            height=450,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=12,
                      color=theme_styles['text_color']),
            showlegend=False,
            xaxis=dict(
                title="Vendedor" if len(vendedores) > 1 else "",
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                tickangle=-45 if len(vendedores) > 4 else 0,
                tickfont=dict(
                    color=theme_styles['text_color'],
                    size=10,
                    family='Inter'
                )
            ),
            yaxis=dict(
                title="Cumplimiento (%)" if len(vendedores) > 1 else "",
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                tickformat='.1f',
                tickfont=dict(
                    color=theme_styles['text_color'],
                    size=10,
                    family='Inter'
                )
            ),
            margin=dict(t=60, b=80, l=80, r=40)
        )

        return fig

    except Exception as e:
        print(f"Error en gráfico de cumplimiento: {e}")
        import traceback
        traceback.print_exc()

        fig = go.Figure()
        fig.add_annotation(
            text=f"Error cargando datos de cumplimiento: {str(e)[:100]}...",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#ef4444")
        )
        fig.update_layout(height=450)
        return fig


@callback(
    Output('ventas-panel-info-cumplimiento', 'children'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-data-store', 'data'),
     Input('ventas-theme-store', 'data')]
)
def update_panel_info_cumplimiento(
        session_data,
        dropdown_value,
        mes,
        data_store,
        theme):
    """
    Panel corregido con lógica de mes finalizado y días hábiles.
    """
    try:
        vendedor = get_selected_vendor(session_data, dropdown_value)
        theme_styles = get_theme_styles(theme)

        data = analyzer.get_cumplimiento_cuotas(vendedor, mes)

        if data.empty:
            return html.Div([
                html.Div([
                    html.P("No hay datos de cumplimiento disponibles", style={
                        'textAlign': 'center',
                        'color': '#6b7280',
                        'fontFamily': 'Inter',
                        'fontSize': '14px',
                        'margin': '50px 0'
                    })
                ])
            ])

        mes_finalizado = data['mes_finalizado'].iloc[0] if len(
            data) > 0 else True

        # Panel para múltiples vendedores
        if len(data) > 1:
            # CORREGIDO: Excluir vendedores con cumplimiento 0 del resumen
            data_activos = data[data['cumplimiento_pct'] > 0]

            if data_activos.empty:
                return html.Div([
                    html.P("No hay vendedores activos en este período", style={
                        'textAlign': 'center', 'color': '#6b7280', 'fontFamily': 'Inter'
                    })
                ])

            cumplimiento_promedio = data_activos['cumplimiento_pct'].mean()

            if mes_finalizado:
                vendedores_cumpliendo = (
                    data_activos['cumplimiento_pct'] >= 100).sum()
                vendedores_no_cumplieron = (
                    data_activos['cumplimiento_pct'] < 100).sum()
                stats_adicionales = [
                    html.Div([
                        html.Span(f"{vendedores_cumpliendo}", style={
                            'fontSize': '16px', 'color': '#22c55e', 'fontWeight': 'bold'
                        }),
                        html.Span(" Cumplieron", style={
                            'fontSize': '11px', 'color': '#6b7280', 'marginLeft': '5px'
                        })
                    ], style={'marginBottom': '8px'}),

                    html.Div([
                        html.Span(f"{vendedores_no_cumplieron}", style={
                            'fontSize': '16px', 'color': '#ef4444', 'fontWeight': 'bold'
                        }),
                        html.Span(" No Cumplieron", style={
                            'fontSize': '11px', 'color': '#6b7280', 'marginLeft': '5px'
                        })
                    ])
                ]
            else:
                vendedores_cumpliendo = (
                    data_activos['cumplimiento_pct'] >= 100).sum()
                vendedores_adelantados = (
                    data_activos['cumplimiento_pct'] >= data_activos['progreso_esperado_pct']).sum() - vendedores_cumpliendo
                vendedores_atrasados = (data_activos['cumplimiento_pct'] < (
                    data_activos['progreso_esperado_pct'] - 10)).sum()

                stats_adicionales = [
                    html.Div([
                        html.Span(f"{vendedores_cumpliendo}", style={
                            'fontSize': '16px', 'color': '#22c55e', 'fontWeight': 'bold'
                        }),
                        html.Span(" Cumpliendo", style={
                            'fontSize': '11px', 'color': '#6b7280', 'marginLeft': '5px'
                        })
                    ], style={'marginBottom': '8px'}),

                    html.Div([
                        html.Span(f"{vendedores_adelantados}", style={
                            'fontSize': '16px', 'color': '#3b82f6', 'fontWeight': 'bold'
                        }),
                        html.Span(" Adelantados", style={
                            'fontSize': '11px', 'color': '#6b7280', 'marginLeft': '5px'
                        })
                    ], style={'marginBottom': '8px'}),

                    html.Div([
                        html.Span(f"{vendedores_atrasados}", style={
                            'fontSize': '16px', 'color': '#ef4444', 'fontWeight': 'bold'
                        }),
                        html.Span(" Atrasados", style={
                            'fontSize': '11px', 'color': '#6b7280', 'marginLeft': '5px'
                        })
                    ])
                ]

            mejor_vendedor = data_activos.loc[data_activos['cumplimiento_pct'].idxmax(
            )]
            peor_vendedor = data_activos.loc[data_activos['cumplimiento_pct'].idxmin(
            )]

            panel_content = html.Div([
                html.H4("Resumen General", style={
                    'marginBottom': '20px',
                    'fontFamily': 'Inter',
                    'fontSize': '16px',
                    'color': theme_styles['text_color'],
                    'textAlign': 'center'
                }),

                html.Div([
                    html.Div([
                        html.H5(f"{cumplimiento_promedio:.1f}%", style={
                            'margin': '0', 'fontSize': '20px', 'color': '#3b82f6', 'fontFamily': 'Inter'
                        }),
                        html.P("Promedio", style={
                            'margin': '5px 0 0 0', 'fontSize': '11px', 'color': '#6b7280', 'fontFamily': 'Inter'
                        })
                    ], style={'textAlign': 'center', 'marginBottom': '15px'}),

                    html.Div(stats_adicionales, style={'textAlign': 'left'})
                ], style={'marginBottom': '20px'}),

                # Información de progreso usando días hábiles
                html.Div([
                    html.P([
                        f"Día hábil {data['dias_transcurridos'].iloc[0]} de {data['dias_mes'].iloc[0]} del mes" +
                        (" (Finalizado)" if mes_finalizado else "")
                    ], style={
                        'fontSize': '12px',
                        'color': '#6b7280',
                        'fontFamily': 'Inter',
                        'textAlign': 'center',
                        'marginBottom': '5px'
                    }),
                    html.P([
                        f"Progreso esperado: {data['progreso_esperado_pct'].iloc[0]:.1f}%" if not mes_finalizado else "Mes completado"
                    ], style={
                        'fontSize': '11px',
                        'color': '#f59e0b' if not mes_finalizado else '#6b7280',
                        'fontFamily': 'Inter',
                        'textAlign': 'center',
                        'fontWeight': 'bold'
                    })
                ], style={
                    'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                    'padding': '10px',
                    'borderRadius': '6px',
                    'marginBottom': '20px'
                }),

                # Mejores y peores (solo vendedores con cumplimiento > 0)
                html.Div([
                    html.H5("Destacados", style={
                        'marginBottom': '10px',
                        'fontFamily': 'Inter',
                        'fontSize': '14px',
                        'color': theme_styles['text_color']
                    }),

                    html.Div([
                        html.P([
                            html.Span("🏆 ", style={'marginRight': '5px'}),
                            html.Strong(mejor_vendedor['vendedor'][:50] + "..." if len(
                                mejor_vendedor['vendedor']) > 50 else mejor_vendedor['vendedor']),
                            html.Br(),
                            html.Span(f"{mejor_vendedor['cumplimiento_pct']:.1f}%", style={
                                'color': '#22c55e', 'fontWeight': 'bold', 'fontSize': '14px'
                            })
                        ], style={'fontSize': '12px', 'marginBottom': '10px', 'fontFamily': 'Inter'}),

                        html.P([
                            html.Span("⚠️ ", style={'marginRight': '5px'}),
                            html.Strong(peor_vendedor['vendedor'][:50] + "..." if len(
                                peor_vendedor['vendedor']) > 50 else peor_vendedor['vendedor']),
                            html.Br(),
                            html.Span(f"{peor_vendedor['cumplimiento_pct']:.1f}%", style={
                                'color': '#ef4444', 'fontWeight': 'bold', 'fontSize': '14px'
                            })
                        ], style={'fontSize': '12px', 'fontFamily': 'Inter'})
                    ])
                ])
            ])

        else:  # Vendedor individual
            row = data.iloc[0]
            panel_content = html.Div([
                html.H4(f"{row['vendedor'][:40]}{'...' if len(row['vendedor']) > 40 else ''}", style={
                    'marginBottom': '12px',
                    'fontFamily': 'Inter',
                    'fontSize': '15px',
                    'color': theme_styles['text_color'],
                    'textAlign': 'center'
                }),

                # Métricas principales
                html.Div([
                    html.Div([
                        html.P("Cumplimiento Actual", style={
                            'margin': '0', 'fontSize': '11px', 'color': '#6b7280', 'fontFamily': 'Inter'
                        }),
                        html.H5(f"{row['cumplimiento_pct']:.1f}%", style={
                            'margin': '5px 0', 'fontSize': '28px', 'color': row['color'], 'fontFamily': 'Inter'
                        }),
                        html.P(row['estado'], style={
                            'margin': '0', 'fontSize': '14px', 'color': row['color'],
                            'fontFamily': 'Inter', 'fontWeight': 'bold'
                        })
                    ], style={'textAlign': 'center', 'marginBottom': '12px'})
                ]),

                # Detalles financieros
                html.Div([
                    html.Div([
                        html.P("Ventas Realizadas", style={
                               'fontSize': '11px', 'color': '#6b7280', 'margin': '0'}),
                        html.P(format_currency_int(row['ventas_reales']), style={
                            'fontSize': '14px', 'color': '#3b82f6', 'fontWeight': 'bold', 'margin': '2px 0 10px 0'
                        })
                    ]),

                    html.Div([
                        html.P("Objetivo Mensual", style={
                               'fontSize': '11px', 'color': '#6b7280', 'margin': '0'}),
                        html.P(format_currency_int(row['cuota']), style={
                            'fontSize': '14px', 'color': '#ef4444', 'fontWeight': 'bold', 'margin': '2px 0 10px 0'
                        })
                    ]),

                    html.Div([
                        html.P("Meta Esperada", style={
                               'fontSize': '11px', 'color': '#6b7280', 'margin': '0'}),
                        html.P([
                            format_currency_int(row['meta_esperada']),
                            html.Br(),
                            html.Span(f"({row['progreso_esperado_pct']:.1f}% de la cuota total)", style={
                                      'fontSize': '10px', 'color': '#6b7280'})
                        ], style={
                            'fontSize': '14px', 'color': '#f59e0b', 'fontWeight': 'bold', 'margin': '2px 0 10px 0'
                        })
                    ])
                ], style={'marginBottom': '20px'}),

                # CORREGIDO: Análisis de progreso vs cuota total
                html.Div([
                    html.P([
                        "Vs Cuota Total: ",
                        html.Span(
                            f"+{format_currency_int(row['diferencia_cuota'])}" if row['diferencia_cuota'] >= 0
                            else format_currency_int(row['diferencia_cuota']),
                            style={
                                'color': '#22c55e' if row['diferencia_cuota'] >= 0 else '#ef4444',
                                'fontWeight': 'bold'
                            }
                        )
                    ], style={'fontSize': '13px', 'fontFamily': 'Inter', 'marginBottom': '8px'}),

                    html.P([
                        f"Faltan {row['dias_mes'] - row['dias_transcurridos']} días hábiles" if not mes_finalizado else "Mes finalizado"
                    ], style={'fontSize': '12px', 'color': '#6b7280', 'fontFamily': 'Inter', 'marginBottom': '8px'}),

                    html.P([
                        "Ritmo necesario:" if not mes_finalizado else "Resultado final:",
                        html.Br(),
                        html.Strong(
                            format_currency_int((row['cuota'] - row['ventas_reales']) / max(
                                1, row['dias_mes'] - row['dias_transcurridos'])) + "/día hábil"
                            if row['ventas_reales'] < row['cuota'] and not mes_finalizado else
                            "¡Objetivo cumplido!" if row[
                                'diferencia_cuota'] >= 0 else f"Faltaron {format_currency_int(-row['diferencia_cuota'])}"
                        )
                    ], style={'fontSize': '11px', 'fontFamily': 'Inter', 'color': '#6b7280'})
                ])
            ])

        return panel_content

    except Exception as e:
        print(f"Error en panel de cumplimiento: {e}")
        return html.Div([
            html.P(f"Error: {str(e)}", style={
                'textAlign': 'center',
                'color': '#ef4444',
                'fontFamily': 'Inter',
                'fontSize': '12px'
            })
        ])


@callback(
    Output('ventas-panel-info-cumplimiento', 'style'),
    [Input('ventas-theme-store', 'data')]
)
def update_panel_cumplimiento_style(theme):
    """
    Actualizar estilo del panel de cumplimiento según tema.
    """
    theme_styles = get_theme_styles(theme)

    return {
        'height': '450px',
        'overflowY': 'auto',
        'padding': '20px',
        'backgroundColor': theme_styles['paper_color'],
        'borderRadius': '12px',
        'border': f'1px solid {theme_styles["line_color"]}',
        'color': theme_styles['text_color']  # Asegurar color de texto correcto
    }


@callback(
    Output('ventas-metrics-cards', 'children'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-dropdown-mes', 'value'),
     Input('ventas-data-store', 'data'),
     Input('ventas-theme-store', 'data')]
)
def update_summary_panel(session_data, dropdown_value, mes, data_store, theme):
    """
    Panel de resumen mejorado con efectividad al final
    """
    vendedor = get_selected_vendor(session_data, dropdown_value)
    theme_styles = get_theme_styles(theme)
    resumen = analyzer.get_resumen_ventas(vendedor, mes)

    # Calcular efectividad
    efectividad = ((resumen['total_ventas'] - resumen['total_devoluciones']) /
                   resumen['total_ventas'] * 100) if resumen['total_ventas'] > 0 else 0
    tasa_devolucion = (resumen['total_devoluciones'] / resumen['total_ventas']
                       * 100) if resumen['total_ventas'] > 0 else 0

    # Calcular variación ajustada
    variacion_ajustada = 0

    if mes != 'Todos':
        try:
            from datetime import datetime
            import pandas as pd

            fecha_mes = pd.to_datetime(mes + '-01')
            mes_anterior = (fecha_mes - pd.DateOffset(months=1)
                            ).strftime('%Y-%m')
            resumen_anterior = analyzer.get_resumen_ventas(
                vendedor, mes_anterior)

            hoy = datetime.now()

            if fecha_mes.year == hoy.year and fecha_mes.month == hoy.month:
                from utils import calcular_dias_habiles_colombia

                dias_mes, dias_transcurridos = calcular_dias_habiles_colombia(
                    fecha_mes.year, fecha_mes.month)

                variacion_ajustada = VentasAnalysisHelper.calcular_variacion_ajustada(
                    resumen['ventas_netas'],
                    resumen_anterior['ventas_netas'],
                    dias_transcurridos,
                    dias_mes
                )
            else:
                if resumen_anterior['ventas_netas'] > 0:
                    variacion_ajustada = ((resumen['ventas_netas'] - resumen_anterior['ventas_netas']) /
                                          resumen_anterior['ventas_netas'] * 100)
        except Exception as e:
            print(f"Error calculando variación: {e}")

    # Generar análisis
    analisis_items = VentasAnalysisHelper.generar_analisis_rapido(
        resumen, variacion_ajustada)

    return html.Div([
        html.Div([
            # Columna 1: Ventas Netas
            html.Div([
                html.Div([
                    html.H4(format_currency_int(resumen['ventas_netas']), style={
                        'margin': '0',
                        'fontSize': '32px',
                        'fontWeight': 'bold',
                        'color': '#22c55e' if variacion_ajustada >= 0 else '#ef4444'
                    }),
                    html.P("Ventas Netas", style={
                        'margin': '5px 0',
                        'fontSize': '13px',
                        'color': '#6b7280'
                    }),
                    html.Div([
                        html.Span(f"{'↑' if variacion_ajustada >= 0 else '↓'} {abs(variacion_ajustada):.1f}%", style={
                            'fontSize': '12px',
                            'color': '#22c55e' if variacion_ajustada >= 0 else '#ef4444',
                            'fontWeight': 'bold'
                        }),
                        html.Span(" proyectado", style={
                            'fontSize': '11px',
                            'color': '#6b7280',
                            'marginLeft': '5px'
                        })
                    ]) if mes != 'Todos' and variacion_ajustada != 0 else None
                ], style={'textAlign': 'center'})
            ], style={
                'flex': '1',
                'padding': '20px',
                'display': 'flex',
                'alignItems': 'center',
                'justifyContent': 'center',
                'borderRight': f'1px solid {theme_styles["line_color"]}'
            }),

            # Columna 2: Efectividad (ahora al final)
            html.Div([
                html.Div([
                    html.Div([
                        html.H2(f"{efectividad:.1f}%", style={
                            'margin': '0',
                            'fontSize': '36px',
                            'fontWeight': 'bold',
                            'color': '#22c55e' if efectividad > 95 else '#f59e0b' if efectividad > 90 else '#ef4444',
                            'textAlign': 'center'
                        }),
                        html.P("Efectividad", style={
                            'margin': '5px 0 0 0',
                            'fontSize': '13px',
                            'color': '#6b7280',
                            'textAlign': 'center'
                        })
                    ]),
                    html.Div([
                        html.Div(style={
                            'width': '100%',
                            'height': '8px',
                            'backgroundColor': '#e5e7eb',
                            'borderRadius': '4px',
                            'overflow': 'hidden',
                            'margin': '15px 0'
                        }, children=[
                            html.Div(style={
                                'width': f"{efectividad:.1f}%",
                                'height': '100%',
                                'backgroundColor': '#22c55e' if efectividad > 95 else '#f59e0b' if efectividad > 90 else '#ef4444',
                                'transition': 'width 0.5s ease'
                            })
                        ]),
                        html.P(f"Devoluciones: {tasa_devolucion:.1f}%", style={
                            'fontSize': '11px',
                            'color': '#ef4444' if tasa_devolucion > 10 else '#f59e0b' if tasa_devolucion > 5 else '#22c55e',
                            'textAlign': 'center',
                            'margin': '0'
                        })
                    ])
                ])
            ], style={
                'flex': '1',
                'padding': '20px',
                'display': 'flex',
                'alignItems': 'center',
                'justifyContent': 'center',
                'borderRight': f'1px solid {theme_styles["line_color"]}'
            }),

            # Columna 3: Métricas Clave
            html.Div([
                html.H5("Métricas Clave", style={
                    'fontSize': '14px',
                    'marginBottom': '15px',
                    'color': theme_styles['text_color'],
                    'fontWeight': 'bold'
                }),
                html.Div([
                    html.Div([
                        html.Div([
                            html.Span(f"{resumen['num_facturas']:,}", style={
                                'fontSize': '24px',
                                'fontWeight': 'bold',
                                'color': '#3b82f6'
                            }),
                            html.Span(" Facturas", style={
                                'fontSize': '12px',
                                'color': '#6b7280',
                                'marginLeft': '8px'
                            })
                        ], style={'display': 'flex', 'alignItems': 'baseline'})
                    ], style={'marginBottom': '12px'}),

                    html.Div([
                        html.Div([
                            html.Span(f"{resumen['num_clientes']:,}", style={
                                'fontSize': '24px',
                                'fontWeight': 'bold',
                                'color': '#10b981'
                            }),
                            html.Span(" Clientes", style={
                                'fontSize': '12px',
                                'color': '#6b7280',
                                'marginLeft': '8px'
                            })
                        ], style={'display': 'flex', 'alignItems': 'baseline'})
                    ], style={'marginBottom': '12px'}),

                    html.Div([
                        html.Div([
                            html.Span(format_currency_int(resumen['ticket_promedio']), style={
                                'fontSize': '20px',
                                'fontWeight': 'bold',
                                'color': '#8b5cf6'
                            })
                        ]),
                        html.Span("Ticket Promedio", style={
                            'fontSize': '11px',
                            'color': '#6b7280'
                        })
                    ])
                ])
            ], style={
                'flex': '0 0 250px',
                'padding': '20px',
                'borderRight': f'1px solid {theme_styles["line_color"]}'
            }),

            # Columna 4: Análisis automático
            html.Div([
                html.H5("Análisis Rápido", style={
                    'fontSize': '14px',
                    'marginBottom': '12px',
                    'color': theme_styles['text_color'],
                    'fontWeight': 'bold'
                }),
                html.Div([
                    html.Div([
                        html.Span(item['icon'], style={
                            'marginRight': '8px',
                            'fontSize': '14px'
                        }),
                        html.Span(item['texto'], style={
                            'fontSize': '11px',
                            'lineHeight': '1.4'
                        })
                    ], style={
                        'marginBottom': '8px',
                        'display': 'flex',
                        'alignItems': 'flex-start'
                    }) for item in analisis_items[:4]
                ]) if analisis_items else html.P("Sin observaciones relevantes", style={
                    'fontSize': '12px',
                    'color': '#6b7280',
                    'fontStyle': 'italic'
                })
            ], style={
                'flex': '1.5',
                'padding': '20px',
                'borderRight': f'1px solid {theme_styles["line_color"]}'
            }),

        ], style={
            'display': 'flex',
            'backgroundColor': theme_styles['paper_color'],
            'borderRadius': '12px',
            'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)',
            'border': f'1px solid {theme_styles["line_color"]}',
            'marginBottom': '24px',
            'minHeight': '160px'
        })
    ])


@callback(
    Output('ventas-eval-container', 'style'),
    [Input('session-store', 'data'),
     Input('ventas-theme-store', 'data')]
)
def show_evaluation_container(session_data, theme):
    """
    Show evaluation container ONLY for super admins (not individual vendors)
    """
    from utils import can_see_all_vendors

    theme_styles = get_theme_styles(theme)

    # Verificar que NO sea un vendedor individual
    if not session_data:
        return {'display': 'none'}

    # Solo mostrar si puede ver todos los vendedores Y no es un vendedor específico
    user_role = session_data.get('role', '')
    is_vendor = 'vendedor' in user_role.lower() or 'admin' in user_role.lower()

    # Si es un vendedor individual (admin pero con acceso limitado), no mostrar
    if is_vendor and not can_see_all_vendors(session_data):
        return {'display': 'none'}

    # Solo mostrar para super admins que pueden ver todo
    if not can_see_all_vendors(session_data):
        return {'display': 'none'}

    return {
        'borderRadius': '20px',
        'padding': '30px',
        'marginBottom': '24px',
        'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
        'width': '100%',
        'backgroundColor': theme_styles['paper_color'],
        'display': 'block'
    }


@callback(
    Output('ventas-eval-podium', 'children'),
    [Input('session-store', 'data'),
     Input('ventas-eval-metric-selector', 'value'),
     Input('ventas-data-store', 'data'),
     Input('ventas-theme-store', 'data')]
)
def update_evaluation_podium(session_data, metric, data_store, theme):
    """
    Update podium display with new Score.
    """
    try:
        from utils import can_see_all_vendors

        # If you are an individual seller (admin but with limited access), not show
        if not can_see_all_vendors(session_data):
            return \
                html.Div("Gráfico no disponible para vendedores",
                         style={'textAlign': 'center'})

        analyzer = EvaluacionAnalyzer()
        df_ranking = analyzer.get_vendor_ranking(metric)

        if df_ranking.empty:
            return \
                html.Div("No hay datos disponibles",
                         style={'textAlign': 'center'})

        # Get top 3
        top3 = df_ranking.head(3)

        podium_cards = []
        medal_emojis = ['🥇', '🥈', '🥉']
        card_colors = [
            'linear-gradient(135deg, #FFD700, #FFA500)',
            'linear-gradient(135deg, #C0C0C0, #808080)',
            'linear-gradient(135deg, #CD7F32, #8B4513)'
        ]

        for i, (_, row) in enumerate(top3.iterrows()):
            card = html.Div([
                html.Div(medal_emojis[i], style={
                    'fontSize': '48px',
                    'textAlign': 'center',
                    'marginBottom': '10px'
                }),
                html.H4(row['vendedor'], style={
                    'color': 'white',
                    'textAlign': 'center',
                    'marginBottom': '10px',
                    'fontSize': '16px'
                }),
                html.Div([
                    html.Div(f"{row[metric]:.1f}", style={
                        'fontSize': '32px',
                        'fontWeight': 'bold',
                        'color': 'white',
                        'textAlign': 'center'
                    }),
                    html.Div([
                        html.Span(f"Eficiencia: {row['eficiencia']:.1f}", style={
                            'fontSize': '11px',
                            'color': 'rgba(255,255,255,0.9)',
                            'marginRight': '10px'
                        }),
                        html.Span(f"Calidad: {row['calidad']:.1f}", style={
                            'fontSize': '11px',
                            'color': 'rgba(255,255,255,0.9)',
                            'marginRight': '10px'
                        }),
                        html.Span(f"Score: {row['score']:.1f}", style={
                            'fontSize': '11px',
                            'color': 'rgba(255,255,255,0.9)',
                            'fontWeight': 'bold'
                        })
                    ], style={'textAlign': 'center', 'marginTop': '5px'})
                ])
            ], style={
                'background': card_colors[i],
                'borderRadius': '15px',
                'padding': '20px',
                'width': '30%',
                'display': 'inline-block',
                'margin': '0 1.5%',
                'boxShadow': '0 4px 15px rgba(0,0,0,0.2)',
                'transform': f'translateY({20 if i == 1 else 0}px)' if i > 0 else ''
            })
            podium_cards.append(card)

        return html.Div(podium_cards, style={
            'textAlign': 'center',
            'marginTop': '20px'
        })

    except Exception as e:
        print(f"Error updating podium: {e}")
        return html.Div(f"Error: {str(e)}", style={'color': 'red'})


@callback(
    Output('ventas-eval-table-container', 'children'),
    [Input('session-store', 'data'),
     Input('ventas-eval-metric-selector', 'value'),
     Input('ventas-eval-show-details', 'value'),
     Input('ventas-data-store', 'data'),
     Input('ventas-theme-store', 'data')]
)
def update_evaluation_table(session_data, metric, show_details, data_store, theme):
    """
    Update evaluation table with Score column.
    """
    try:
        from utils import can_see_all_vendors

        # If you are an individual seller (admin but with limited access), not show
        if not can_see_all_vendors(session_data):
            return \
                html.Div("Gráfico no disponible para vendedores",
                         style={'textAlign': 'center'})

        analyzer = EvaluacionAnalyzer()
        df_ranking = analyzer.get_vendor_ranking(metric)

        if df_ranking.empty:
            return html.Div("No hay datos disponibles")

        # Create table rows
        table_rows = []

        # Header
        header_cells = [
            html.Th("#", style={'width': '5%'}),
            html.Th("Vendedor", style={'width': '18%'}),
            html.Th("Score Total", style={'width': '8%'}),
            html.Th("Eficiencia", style={'width': '8%'}),
            html.Th("Calidad", style={'width': '8%'}),
            html.Th("Score Dist.", style={'width': '8%'}),
            html.Th("Categoría", style={'width': '12%'}),
            html.Th("Análisis", style={'width': '33%'})
        ]

        table_rows.append(html.Thead([html.Tr(header_cells)]))

        # Data rows
        tbody_rows = []

        for _, row in df_ranking.iterrows():
            # Main row
            main_row = html.Tr([
                html.Td(str(row['ranking'])),
                html.Td(row['vendedor'], style={'fontWeight': 'bold'}),
                html.Td(f"{row['score_total']:.1f}"),
                html.Td(f"{row['eficiencia']:.1f}"),
                html.Td(f"{row['calidad']:.1f}"),
                html.Td(f"{row['score']:.1f}", style={
                    'fontWeight': 'bold',
                    'color': '#10b981' if row['score'] > 70 else '#f59e0b' if row['score'] > 50 else '#ef4444'
                }),
                html.Td(row['categoria_desempeno']),
                html.Td(row['analisis_breve'], style={'fontSize': '11px'})
            ])
            tbody_rows.append(main_row)

            # Expandable detail row
            if 'show' in show_details:
                eff_breakdown = analyzer.get_metric_breakdown(
                    row['vendedor'], 'eficiencia')
                cal_breakdown = analyzer.get_metric_breakdown(
                    row['vendedor'], 'calidad')

                detail_content = html.Div([
                    html.Div([
                        # Efficiency breakdown
                        html.Div([
                            html.H5("⚡ Desglose de Eficiencia",
                                    style={'marginBottom': '10px'}),
                            html.Div([
                                html.Div([
                                    html.Span(comp['name'], style={
                                              'fontSize': '11px'}),
                                    html.Div([
                                        html.Div(style={
                                            'width': f"{max(min(comp['value'], 100) - 20, 5)}%",
                                            'backgroundColor': '#3b82f6' if comp['value'] >= 0 else '#f63b82',
                                            'height': '15px',
                                            'borderRadius': '3px',
                                            'display': 'inline-block'
                                        }),
                                        html.Span(f" {comp['value']:.1f}% (peso: {comp['weight']}%)",
                                                  style={'fontSize': '10px', 'marginLeft': '10px'})
                                    ], style={'width': '100%'})
                                ], style={'marginBottom': '5px'})
                                for comp in eff_breakdown.get('components', [])
                            ])
                        ], style={'width': '32%', 'display': 'inline-block', 'marginRight': '1%', 'verticalAlign': 'top'}),

                        # Quality breakdown
                        html.Div([
                            html.H5("💎 Desglose de Calidad", style={
                                    'marginBottom': '10px'}),
                            html.Div([
                                html.Div([
                                    html.Span(comp['name'], style={
                                              'fontSize': '11px'}),
                                    html.Div([
                                        html.Div(style={
                                            'width': f"{min(comp['value'], 100)}%",
                                            'backgroundColor': '#10b981',
                                            'height': '15px',
                                            'borderRadius': '3px',
                                            'display': 'inline-block'
                                        }),
                                        html.Span(f" {comp['value']:.1f}% (peso: {comp['weight']}%)",
                                                  style={'fontSize': '10px', 'marginLeft': '10px'})
                                    ], style={'width': '100%'})
                                ], style={'marginBottom': '5px'})
                                for comp in cal_breakdown.get('components', [])
                            ])
                        ], style={'width': '32%', 'display': 'inline-block', 'marginRight': '1%'}),

                        # Score breakdown
                        html.Div([
                            html.H5("📊 Desglose Score Distribución",
                                    style={'marginBottom': '10px'}),
                            html.Div([
                                html.Div([
                                    html.Span("Diversidad Productos",
                                              style={'fontSize': '11px'}),
                                    html.Div([
                                        html.Div(style={
                                            'width': f"{row.get('score_productos', 0)}%",
                                            'backgroundColor': '#8b5cf6',
                                            'height': '15px',
                                            'borderRadius': '3px',
                                            'display': 'inline-block'
                                        }),
                                        html.Span(f" {row.get('score_productos', 0):.1f}% (peso: 35%)",
                                                  style={'fontSize': '10px', 'marginLeft': '10px'})
                                    ], style={'width': '100%'})
                                ], style={'marginBottom': '5px'}),
                                html.Div([
                                    html.Span("Diversidad Clientes",
                                              style={'fontSize': '11px'}),
                                    html.Div([
                                        html.Div(style={
                                            'width': f"{row.get('score_clientes', 0)}%",
                                            'backgroundColor': '#8b5cf6',
                                            'height': '15px',
                                            'borderRadius': '3px',
                                            'display': 'inline-block'
                                        }),
                                        html.Span(f" {row.get('score_clientes', 0):.1f}% (peso: 30%)",
                                                  style={'fontSize': '10px', 'marginLeft': '10px'})
                                    ], style={'width': '100%'})
                                ], style={'marginBottom': '5px'}),
                                html.Div([
                                    html.Span("Diversidad Proveedores",
                                              style={'fontSize': '11px'}),
                                    html.Div([
                                        html.Div(style={
                                            'width': f"{row.get('score_proveedores', 0)}%",
                                            'backgroundColor': '#8b5cf6',
                                            'height': '15px',
                                            'borderRadius': '3px',
                                            'display': 'inline-block'
                                        }),
                                        html.Span(f" {row.get('score_proveedores', 0):.1f}% (peso: 15%)",
                                                  style={'fontSize': '10px', 'marginLeft': '10px'})
                                    ], style={'width': '100%'})
                                ], style={'marginBottom': '5px'}),
                                html.Div([
                                    html.Span("Volumen de Ventas",
                                              style={'fontSize': '11px'}),
                                    html.Div([
                                        html.Div(style={
                                            'width': f"{row.get('volume_percentile', 0)}%",
                                            'backgroundColor': '#8b5cf6',
                                            'height': '15px',
                                            'borderRadius': '3px',
                                            'display': 'inline-block'
                                        }),
                                        html.Span(f" {row.get('volume_percentile', 0):.1f}% (peso: 20%)",
                                                  style={'fontSize': '10px', 'marginLeft': '10px'})
                                    ], style={'width': '100%'})
                                ], style={'marginBottom': '5px'})
                            ])
                        ], style={'width': '32%', 'display': 'inline-block', 'verticalAlign': 'top'})
                    ])
                ], style={
                    'padding': '15px',
                    'backgroundColor': 'rgba(59, 130, 246, 0.05)',
                    'borderRadius': '8px',
                    'margin': '10px 20px'
                })

                detail_row = html.Tr([
                    # Actualizado a 8 columnas
                    html.Td(detail_content, colSpan=8)
                ])
                tbody_rows.append(detail_row)

        table_rows.append(html.Tbody(tbody_rows))

        return html.Table(table_rows, style={
            'width': '100%',
            'borderCollapse': 'collapse',
            'fontSize': '12px'
        })

    except Exception as e:
        print(f"Error updating table: {e}")
        return html.Div(f"Error: {str(e)}", style={'color': 'red'})


@callback(
    Output('ventas-efficiency-chart', 'figure'),
    [Input('session-store', 'data'),
     Input('ventas-dropdown-vendedor', 'value'),
     Input('ventas-data-store', 'data'),
     Input('ventas-theme-store', 'data')]
)
def update_efficiency_chart(session_data, dropdown_value, data_store, theme):
    """
    Bars chart grouped with average ticket.
    """
    try:
        vendedor = \
            get_selected_vendor(session_data, dropdown_value)

        theme_styles = get_theme_styles(theme)
        analyzer = VentasAnalyzer()

        df = analyzer.get_resumen_mensual(vendedor)

        if df.empty:
            return go.Figure()

        df = df.tail(6)
        x_data = df['mes']
        y1_data = df['ventas_netas']
        y2_data = df['clientes_unicos']
        ticket_promedio = df['venta_por_cliente']

        # Normalizar datos para visualización (escalar clientes para que sean visibles)
        max_ventas = y1_data.max() if len(y1_data) > 0 else 1
        max_clientes = y2_data.max() if len(y2_data) > 0 else 1
        factor_escala = max_ventas / max_clientes if max_clientes > 0 else 1

        fig = go.Figure()

        # Barras de ventas (más anchas, con opacidad)
        fig.add_trace(
            go.Bar(
                x=x_data,
                y=y1_data,
                name='Ventas ($)',
                marker=dict(
                    color='rgba(59, 130, 246, 0.6)',
                    line=dict(
                        color='rgba(59, 130, 246, 0.9)',
                        width=2
                    )
                ),
                width=0.4,  # Barras más anchas
                hovertemplate='<b>%{x}</b><br>Ventas: $%{y:,.0f}<extra></extra>'
            )
        )

        # Barras de clientes (superpuestas, escaladas)
        fig.add_trace(
            go.Bar(
                x=x_data,
                y=y2_data * factor_escala,  # Escalar para visualización
                name='Clientes (escalado)',
                marker=dict(
                    color='rgba(16, 185, 129, 0.5)',  # Verde con opacidad
                    line=dict(
                        color='rgba(16, 185, 129, 0.8)',  # Borde más oscuro
                        width=2
                    )
                ),
                width=0.4,  # Barras más delgadas
                customdata=y2_data,  # Valores reales para hover
                hovertemplate='<b>%{x}</b><br>Clientes: %{customdata}<extra></extra>'
            )
        )

        # Línea de ticket promedio
        fig.add_trace(
            go.Scatter(
                x=x_data,
                y=ticket_promedio *
                (max_ventas / ticket_promedio.max()
                 if ticket_promedio.max() > 0 else 1),
                mode='lines+markers+text',
                name='Ticket Promedio',
                line=dict(
                    color='rgba(245, 158, 11, 0.8)',
                    width=3,
                    dash='dot'
                ),
                marker=dict(
                    size=8,
                    color='rgba(245, 158, 11, 0.9)',
                    line=dict(color='white', width=2)
                ),
                text=[f'${val:,.0f}' for val in ticket_promedio],
                textposition='top center',
                textfont=dict(
                    size=10,
                    color=theme_styles['text_color']
                ),
                customdata=ticket_promedio,
                hovertemplate='<b>%{x}</b><br>Ticket: $%{customdata:,.0f}<extra></extra>'
            )
        )

        # Actualizar layout sin grid
        fig.update_layout(
            height=400,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['paper_color'],
            font=dict(family="Inter", size=12,
                      color=theme_styles['text_color']),
            xaxis=dict(
                showgrid=False,
                showline=True,
                linecolor=theme_styles['border_color'],
                tickfont=dict(size=11)
            ),
            yaxis=dict(
                showgrid=False,
                showline=True,
                linecolor=theme_styles['border_color'],
                tickformat='$,.0f',
                tickfont=dict(size=11)
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                bgcolor='rgba(0,0,0,0)',
                bordercolor='rgba(0,0,0,0)',
                font=dict(size=11)
            ),
            margin=dict(t=60, b=80, l=80, r=40),
            hovermode='x unified',
            bargap=0.15,
            bargroupgap=0.1
        )

        return fig

    except Exception as e:
        print(f"Error in efficiency chart: {e}")
        import traceback
        traceback.print_exc()
        return go.Figure()


@callback(
    [Output('ventas-efficiency-container', 'style'),
     Output('ventas-efficiency-title', 'style')],
    Input('ventas-theme-store', 'data')
)
def update_efficiency_container_theme(theme: str):
    """
    Update efficiency container styles.
    """
    theme_styles = get_theme_styles(theme)

    container_style = {
        'borderRadius': '15px',
        'padding': '25px',
        'marginBottom': '20px',
        'backgroundColor': theme_styles['plot_bg'],
        'border': f'1px solid {theme_styles["border_color"]}'
    }

    title_style = {
        'textAlign': 'center',
        'marginBottom': '20px',
        'color': theme_styles['text_color'],
        'fontFamily': 'Inter'
    }

    return container_style, title_style

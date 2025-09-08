import time
from datetime import datetime, date
import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import locale

try:
    # Intentar configurar locale en español
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Linux/Mac
except:
    try:
        locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')  # Windows
    except:
        try:
            locale.setlocale(locale.LC_TIME, 'es_ES')  # Alternativo
        except:
            print("⚠️ No se pudo configurar locale en español")

from components import (
    create_metrics_grid,
    create_empty_metrics,
    METRIC_COLORS
)
from utils import (
    format_currency_int,
    get_theme_styles,
    get_dropdown_style
)

try:
    from analyzers import ProveedoresVentasAnalyzer
    analyzer = ProveedoresVentasAnalyzer()
    print("✅ ProveedoresVentasAnalyzer inicializado correctamente")
except Exception as e:
    print(
        f"⚠️ [ProveedoresVentasPage] Carga inicial falló (se recargará on-demand): {e}")
    df = pd.DataFrame()


def get_default_laboratorio():
    """
    Obtener el primer laboratorio que no sea 'Todos'.
    """
    try:
        laboratorios = getattr(analyzer, 'laboratorios_list', ['Todos'])

        if len(laboratorios) > 1 and laboratorios[0] == 'Todos':
            return laboratorios[1]
        elif len(laboratorios) > 0 and laboratorios[0] != 'Todos':
            return laboratorios[0]
        else:
            return 'Todos'
    except:
        return 'Todos'


# Layout de la página
layout = html.Div([
    # Stores
    dcc.Store(id='proveedores-ventas-theme-store', data='light'),
    dcc.Store(id='proveedores-ventas-data-store', data={'last_update': 0}),

    # Notification area
    html.Div(id='proveedores-ventas-notification-area', children=[], style={
        'position': 'fixed',
        'top': '20px',
        'right': '20px',
        'zIndex': '1000',
        'maxWidth': '300px'
    }),

    html.Div([
        # Header
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
            ], className="logo-left-container"),

            html.Div([
                html.H1(
                    "Proveedores - Ventas",
                    className="main-title",
                    id='proveedores-ventas-titulo-principal'
                ),
                html.P(
                    "Análisis de ventas por laboratorio",
                    className="main-subtitle",
                    id='proveedores-ventas-subtitulo'
                )
            ], className="center-title-section"),

            html.Div([
                html.Button(
                    "🌙",
                    id="proveedores-ventas-theme-toggle",
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
            ], className="logout-right-container")
        ], className="top-header", id='proveedores-ventas-header-container'),

        # Controls
        html.Div([
            html.Div([
                html.Label("Laboratorio:", style={
                    'fontWeight': '600',
                    'fontSize': '14px',
                    'marginBottom': '8px',
                    'display': 'block'
                }),
                dcc.Dropdown(
                    id='proveedores-ventas-dropdown-laboratorio',
                    options=[{'label': lab, 'value': lab} for lab in getattr(
                        analyzer, 'laboratorios_list', ['Todos'])],
                    value=get_default_laboratorio(),
                    placeholder="Seleccionar laboratorio...",
                    clearable=True,
                    style={'height': '44px',
                           'borderRadius': '12px', 'fontSize': '14px'},
                    maxHeight=150
                )
            ], style={'flex': '1', 'minWidth': '250px'}),

            html.Div([
                html.Label("Período:", style={
                    'fontWeight': '600',
                    'fontSize': '14px',
                    'marginBottom': '8px',
                    'display': 'block'
                }),
                dcc.Dropdown(
                    id='proveedores-ventas-dropdown-periodo',
                    options=[{'label': p, 'value': p}
                             for p in getattr(analyzer, 'periodos_list', ['Todos'])],
                    value='Todos',
                    placeholder="Seleccionar período...",
                    clearable=True,
                    style={'height': '44px',
                           'borderRadius': '12px', 'fontSize': '14px'}
                )
            ], style={'flex': '1', 'minWidth': '200px'}),

            html.Div([
                html.Button(
                    "🔄 Actualizar",
                    id="proveedores-ventas-btn-actualizar",
                    n_clicks=0,
                    style={
                        'background': 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
                        'color': '#ffffff',
                        'border': 'none',
                        'padding': '12px 20px',
                        'borderRadius': '25px',
                        'fontWeight': '600',
                        'fontSize': '14px',
                        'cursor': 'pointer',
                        'boxShadow': '0 4px 12px rgba(59, 130, 246, 0.3)',
                        'transition': 'all 0.3s ease',
                        'height': '44px',
                        'marginRight': '8px'
                    }
                )
            ], style={'display': 'flex', 'alignItems': 'flex-end'})
        ], id='proveedores-ventas-controls-container', style={
            'display': 'flex',
            'gap': '24px',
            'alignItems': 'stretch',
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'flexWrap': 'wrap'
        }),

        # Metrics Cards
        html.Div(id="proveedores-ventas-metrics-cards",
                 children=[], style={'marginBottom': '24px'}),

        # Gráfico de evolución de ventas
        html.Div([
            html.H3("Evolución de Ventas", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'
            }),
            html.Div([
                html.Label("Tipo de período:", style={
                    'fontWeight': 'bold', 'marginBottom': '8px', 'fontFamily': 'Inter', 'fontSize': '14px'
                }),
                dcc.Dropdown(
                    id='proveedores-ventas-dropdown-tipo-periodo',
                    options=[
                        {'label': 'Mensual', 'value': 'mensual'},
                        {'label': 'Trimestral', 'value': 'trimestral'},
                        {'label': 'Anual', 'value': 'anual'}
                    ],
                    value='mensual',
                    style={'fontFamily': 'Inter',
                           'height': '44px', 'width': '200px'}
                )
            ], style={'marginBottom': '20px'}),
            dcc.Graph(id='proveedores-ventas-grafico-evolucion')
        ], id='proveedores-ventas-row1-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)'
        }),

        # Estacionalidad por semana
        html.Div([
            html.H3("Análisis de Estacionalidad", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'
            }),
            html.Div([
                html.Div([
                    html.H4("Por Semana del Año", style={
                        'textAlign': 'center', 'marginBottom': '15px', 'fontFamily': 'Inter', 'fontSize': '16px'
                    }),
                    dcc.Graph(id='proveedores-ventas-grafico-estacionalidad')
                ], style={'width': '66%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingRight': '10px'}),

                html.Div([
                    html.H4("Por Día de Semana", style={
                        'textAlign': 'center', 'marginBottom': '15px', 'fontFamily': 'Inter', 'fontSize': '16px'
                    }),
                    dcc.Graph(id='proveedores-ventas-grafico-dia-semana')
                ], style={'width': '33%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingLeft': '10px'})
            ])
        ], id='proveedores-ventas-row2-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)'
        }),

        # Matriz de ventas por clientes
        html.Div([
            html.H3("Matriz de Ventas por Cliente", style={
                'textAlign': 'center', 'marginBottom': '25px', 'fontFamily': 'Inter'
            }),
            html.Div([
                html.Div([
                    html.Label("Rango de fechas:", style={
                        'fontWeight': 'bold', 'marginBottom': '10px', 'fontFamily': 'Inter', 'fontSize': '14px'
                    }),
                    dcc.DatePickerRange(
                        id='proveedores-ventas-date-range',
                        start_date=date(2025, 1, 1),
                        end_date=date.today(),
                        display_format='DD/MM/YYYY',
                        style={
                            'fontFamily': 'Inter',
                            'fontSize': '14px',
                            'width': '100%'
                        },
                        calendar_orientation='horizontal',
                        start_date_placeholder_text='Fecha inicio',
                        end_date_placeholder_text='Fecha fin',
                        number_of_months_shown=2,
                        clearable=True,
                        className='custom-datepicker'
                    )
                ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),

                html.Div([
                    html.Label("Clientes (máx 10):", style={
                        'fontWeight': 'bold', 'marginBottom': '10px', 'fontFamily': 'Inter', 'fontSize': '14px'
                    }),
                    dcc.Dropdown(
                        id='proveedores-ventas-dropdown-clientes-matriz',
                        options=[],
                        value=[],
                        multi=True,
                        placeholder="Seleccionar clientes...",
                        style={'fontFamily': 'Inter'}
                    )
                ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '4%'})
            ], style={'marginBottom': '20px'}),
            dcc.Graph(id='proveedores-ventas-grafico-matriz')
        ], id='proveedores-ventas-row3-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)'
        }),

        # Top 10 Clientes y Productos
        html.Div([
            html.Div([
                html.H3("Top 10 - Clientes", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'
                }),
                dcc.Graph(id='proveedores-ventas-top-clientes')
            ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'}),

            html.Div([
                html.H3("Top 10 - Productos", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'
                }),
                dcc.Graph(id='proveedores-ventas-top-productos')
            ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'})
        ], id='proveedores-ventas-row4-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)'
        }),

        # Evolución por cliente
        html.Div([
            html.H3("Evolución de Ventas por Cliente", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'
            }),
            html.Div([
                html.Label("Cliente:", style={
                    'fontWeight': 'bold', 'marginBottom': '8px', 'fontFamily': 'Inter', 'fontSize': '14px'
                }),
                dcc.Dropdown(
                    id='proveedores-ventas-dropdown-cliente',
                    options=[{'label': 'Seleccione un cliente',
                              'value': 'Seleccione un cliente'}],
                    value='Seleccione un cliente',
                    style={'fontFamily': 'Inter', 'height': '44px'}
                )
            ], style={'marginBottom': '20px', 'width': '70%'}),
            dcc.Graph(id='proveedores-ventas-grafico-evolucion-cliente')
        ], id='proveedores-ventas-row5-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)'
        })

    ], style={
        'margin': '0 auto',
        'padding': '0 40px',
    }),

], id='proveedores-ventas-main-container', style={
    'width': '100%',
    'minHeight': '100vh',
    'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
    'transition': 'all 0.3s ease',
    'padding': '20px 0',
    'background': 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 25%, #f8fafc 50%, #f1f5f9 100%)',
    'backgroundSize': '400% 400%',
    'animation': 'gradientShift 15s ease infinite'
})


# ==================== CALLBACKS ====================

# Helper function
def create_empty_figure(message, theme):
    """Crear figura vacía con mensaje"""
    theme_styles = get_theme_styles(theme)
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color=theme_styles['text_color'])
    )
    fig.update_layout(
        height=400,
        paper_bgcolor=theme_styles['plot_bg'],
        plot_bgcolor=theme_styles['plot_bg']
    )
    return fig


@callback(
    Output('proveedores-ventas-data-store', 'data'),
    [Input('proveedores-ventas-btn-actualizar', 'n_clicks')],
    prevent_initial_call=True
)
def update_data_optimized(n_clicks):
    """
    Callback para recargar datos con modo de carga seleccionado.
    """
    if n_clicks > 0:
        try:
            start_time = time.time()

            if hasattr(analyzer, 'reload_data'):
                analyzer.reload_data(year=2025, limit_records=None)
                records_count = len(
                    getattr(analyzer, 'df_ventas', pd.DataFrame()))
            else:
                records_count = 0

            load_time = time.time() - start_time

            data_summary = {}

            if hasattr(analyzer, 'get_data_summary'):
                data_summary = analyzer.get_data_summary()

            return {
                'last_update': n_clicks,
                'timestamp': datetime.now().isoformat(),
                'success': True,
                'load_time': load_time,
                'records_count': records_count,
                'data_summary': data_summary  # NUEVO
            }
        except Exception as e:
            print(f"❌ Error en actualización: {e}")
            return {
                'last_update': n_clicks,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'success': False
            }

    return dash.no_update


@callback(
    Output('proveedores-ventas-notification-area', 'children'),
    [Input('proveedores-ventas-data-store', 'data')],
    prevent_initial_call=True
)
def show_notification(data_store):
    """Mostrar notificación de actualización"""
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
                    'fontSize': '12px'
                })
            ])
    return []


@callback(
    Output('proveedores-ventas-metrics-cards', 'children'),
    [Input('proveedores-ventas-dropdown-laboratorio', 'value'),
     Input('proveedores-ventas-dropdown-periodo', 'value'),
     Input('proveedores-ventas-data-store', 'data'),
     Input('proveedores-ventas-theme-store', 'data')]
)
def update_metrics_cards(laboratorio, periodo, data_store, theme):
    """Actualizar cards de métricas"""
    try:
        is_dark = theme == 'dark'

        # Obtener resumen de datos con manejo de errores
        try:
            resumen = analyzer.get_resumen_ventas(
                laboratorio or 'Todos', periodo or 'Todos')
        except Exception as e:
            print(f"❌ Error obteniendo resumen: {e}")
            resumen = {
                'total_ventas': 0, 'total_utilidad': 0, 'margen_promedio': 0,
                'total_descuentos': 0, 'total_costo': 0, 'num_facturas': 0,
                'num_productos': 0, 'num_clientes': 0
            }

        # Datos de métricas usando los colores disponibles en METRIC_COLORS
        metrics_data = [
            {
                'title': 'Ventas Totales',
                'value': format_currency_int(resumen['total_ventas']),
                'icon': '',
                'color': METRIC_COLORS['success'],
                'card_id': 'prov-card-1'
            },
            {
                'title': 'Utilidad Total',
                'value': format_currency_int(resumen['total_utilidad']),
                'icon': '',
                'color': METRIC_COLORS['primary'],
                'card_id': 'prov-card-2'
            },
            {
                'title': 'Margen Promedio',
                'value': f"{resumen['margen_promedio']:.1f}%",
                'icon': '',
                'color': METRIC_COLORS['indigo'],
                'card_id': 'prov-card-3'
            },
            {
                'title': 'Descuentos',
                'value': format_currency_int(resumen['total_descuentos']),
                'icon': '',
                'color': METRIC_COLORS['warning'],
                'card_id': 'prov-card-4'
            },
            {
                'title': 'Costo Total',
                'value': format_currency_int(resumen['total_costo']),
                'icon': '',
                'color': METRIC_COLORS['danger'],
                'card_id': 'prov-card-5'
            },
            {
                'title': '# Facturas',
                'value': f"{resumen['num_facturas']:,}",
                'icon': '',
                'color': METRIC_COLORS['purple'],
                'card_id': 'prov-card-6'
            },
            {
                'title': '# Productos',
                'value': f"{resumen['num_productos']:,}",
                'icon': '',
                'color': METRIC_COLORS['teal'],
                'card_id': 'prov-card-7'
            },
            {
                'title': '# Clientes',
                'value': f"{resumen['num_clientes']:,}",
                'icon': '',
                'color': METRIC_COLORS['orange'],
                'card_id': 'prov-card-8'
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
        print(f"❌ Error actualizando metrics cards: {e}")
        import traceback
        traceback.print_exc()

        # Crear métricas vacías como fallback
        try:
            return create_empty_metrics(is_dark=theme == 'dark', count=8)
        except Exception as e2:
            print(f"❌ Error creando métricas vacías: {e2}")
            # Fallback manual si todo falla
            return html.Div([
                html.P("Error cargando métricas", style={
                    'textAlign': 'center',
                    'color': '#e74c3c',
                    'padding': '20px',
                    'fontFamily': 'Inter'
                })
            ])

# Evolución de ventas callback


@callback(
    Output('proveedores-ventas-grafico-evolucion', 'figure'),
    [Input('proveedores-ventas-dropdown-laboratorio', 'value'),
     Input('proveedores-ventas-dropdown-tipo-periodo', 'value'),
     Input('proveedores-ventas-data-store', 'data'),
     Input('proveedores-ventas-theme-store', 'data')]
)
def update_grafico_evolucion(laboratorio, tipo_periodo, data_store, theme):
    """Actualizar gráfico de evolución de ventas"""
    try:
        # Verificar que el analyzer tenga el método
        if not hasattr(analyzer, 'get_ventas_por_periodo'):
            return create_empty_figure("Analyzer no disponible", theme)

        data = analyzer.get_ventas_por_periodo(
            laboratorio or 'Todos', tipo_periodo or 'mensual')
        theme_styles = get_theme_styles(theme)

        if data.empty:
            return create_empty_figure("No hay datos disponibles para el período seleccionado", theme)

        # Determinar columna de período
        periodo_col = data.columns[0]

        fig = go.Figure()

        # Línea de ventas
        fig.add_trace(go.Scatter(
            x=data[periodo_col],
            y=data['ventas_netas'],
            mode='lines+markers',
            name='Ventas Netas',
            line=dict(color='rgba(0, 119, 182, 0.9)', width=4, shape='spline'),
            marker=dict(size=10, color='rgba(0, 119, 182, 1.0)',
                        line=dict(color='white', width=3)),
            fill='tozeroy',
            fillcolor='rgba(0, 119, 182, 0.2)',
            hovertemplate="<b>%{x}</b><br>Ventas: %{customdata}<br>Facturas: %{text}<extra></extra>",
            customdata=[format_currency_int(val)
                        for val in data['ventas_netas']],
            text=data['num_facturas']
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
                title="Período",
                linecolor=theme_styles['line_color']
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                tickformat='$,.0f',
                title="Ventas ($)",
                linecolor=theme_styles['line_color']
            ),
            showlegend=False,
            margin=dict(t=20, b=80, l=80, r=20)
        )

        return fig
    except Exception as e:
        print(f"❌ Error en gráfico de evolución: {e}")
        return create_empty_figure("Error cargando datos", theme)

# Estacionalidad callback


@callback(
    Output('proveedores-ventas-grafico-estacionalidad', 'figure'),
    [Input('proveedores-ventas-dropdown-laboratorio', 'value'),
     Input('proveedores-ventas-dropdown-periodo', 'value'),
     Input('proveedores-ventas-data-store', 'data'),
     Input('proveedores-ventas-theme-store', 'data')]
)
def update_grafico_estacionalidad(laboratorio, periodo, data_store, theme):
    """Actualizar gráfico de estacionalidad por semana"""
    try:
        if not hasattr(analyzer, 'get_estacionalidad_semana'):
            return create_empty_figure("Analyzer no disponible", theme)

        data = analyzer.get_estacionalidad_semana(
            laboratorio or 'Todos', periodo or 'Todos')
        theme_styles = get_theme_styles(theme)

        if data.empty:
            return create_empty_figure("No hay datos disponibles para estacionalidad", theme)

        # Colores para las barras
        colors = ['rgba(0, 119, 182, 0.3)' for _ in range(len(data))]
        border_colors = ['rgba(0, 119, 182, 0.9)' for _ in range(len(data))]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=data['semana'],
            y=data['ventas_netas'],
            marker=dict(
                color=colors,
                line=dict(color=border_colors, width=1),
                opacity=0.8
            ),
            text=[format_currency_int(
                val) if val > 0 else '' for val in data['ventas_netas']],
            textposition='outside',
            textfont=dict(size=10, color=theme_styles['text_color']),
            hovertemplate="<b>Semana %{x}</b><br>Ventas: %{customdata}<br>Facturas: %{text}<extra></extra>",
            customdata=[format_currency_int(val)
                        for val in data['ventas_netas']],
            texttemplate='%{text}'
        ))

        fig.update_layout(
            height=400,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=12,
                      color=theme_styles['text_color']),
            xaxis=dict(
                title="Semana del Año",
                showgrid=False
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
        print(f"❌ Error en gráfico de estacionalidad: {e}")
        return create_empty_figure("Error cargando datos", theme)

# Matriz de ventas callback


@callback(
    Output('proveedores-ventas-grafico-matriz', 'figure'),
    [Input('proveedores-ventas-dropdown-laboratorio', 'value'),
     Input('proveedores-ventas-date-range', 'start_date'),
     Input('proveedores-ventas-date-range', 'end_date'),
     Input('proveedores-ventas-dropdown-clientes-matriz', 'value'),
     Input('proveedores-ventas-data-store', 'data'),
     Input('proveedores-ventas-theme-store', 'data')]
)
def update_grafico_matriz(laboratorio, start_date, end_date, clientes_seleccionados, data_store, theme):
    """Actualizar matriz de ventas por cliente"""
    try:
        theme_styles = get_theme_styles(theme)

        # Limitar a 10 clientes
        if clientes_seleccionados and len(clientes_seleccionados) > 10:
            clientes_seleccionados = clientes_seleccionados[:10]

        if not clientes_seleccionados:
            return create_empty_figure("Seleccione clientes para mostrar la matriz", theme)

        if not hasattr(analyzer, 'get_matriz_ventas_clientes'):
            return create_empty_figure("Función no disponible", theme)

        matriz = analyzer.get_matriz_ventas_clientes(
            laboratorio or 'Todos', start_date, end_date, clientes_seleccionados
        )

        if matriz.empty:
            return create_empty_figure("No hay datos para el rango seleccionado", theme)

        # Crear heatmap
        text_values = []
        for i in range(len(matriz.index)):
            row_text = []
            for j in range(len(matriz.columns)):
                value = matriz.values[i, j]
                if value > 0:
                    row_text.append(format_currency_int(value))
                else:
                    row_text.append('')
            text_values.append(row_text)

        fig = go.Figure(data=go.Heatmap(
            z=matriz.values,
            x=matriz.columns,
            y=[cliente[:40] + "..." if len(cliente) >
               40 else cliente for cliente in matriz.index],
            text=text_values,
            texttemplate="%{text}",
            textfont={"size": 9, "color": "white"},
            colorscale='Blues',
            showscale=True,
            hovertemplate="<b>%{y}</b><br>%{x}<br>Ventas: %{text}<extra></extra>"
        ))

        fig.update_layout(
            height=max(400, len(matriz) * 40),
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=10,
                      color=theme_styles['text_color']),
            xaxis=dict(
                title="Período",
                tickangle=-45
            ),
            yaxis=dict(
                title="Cliente"
            ),
            margin=dict(t=20, b=80, l=200, r=20)
        )

        return fig
    except Exception as e:
        print(f"❌ Error en matriz de ventas: {e}")
        return create_empty_figure("Error cargando datos", theme)

# Top clientes callback


@callback(
    Output('proveedores-ventas-top-clientes', 'figure'),
    [Input('proveedores-ventas-dropdown-laboratorio', 'value'),
     Input('proveedores-ventas-dropdown-periodo', 'value'),
     Input('proveedores-ventas-data-store', 'data'),
     Input('proveedores-ventas-theme-store', 'data')]
)
def update_top_clientes(laboratorio, periodo, data_store, theme):
    """Actualizar top 10 clientes"""
    try:
        if not hasattr(analyzer, 'get_top_clientes'):
            return create_empty_figure("Función no disponible", theme)

        data = analyzer.get_top_clientes(
            laboratorio or 'Todos', periodo or 'Todos', 10)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            return create_empty_figure("No hay datos de clientes disponibles", theme)

        # Ordenar de menor a mayor para gráfico horizontal
        data_sorted = data.sort_values('ventas_netas', ascending=True)

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=data_sorted['ventas_netas'],
            y=[cliente[:30] + "..." if len(cliente) >
               30 else cliente for cliente in data_sorted['cliente']],
            orientation='h',
            marker=dict(
                color='rgba(0, 119, 182, 0.6)',
                line=dict(color='rgba(0, 119, 182, 0.9)', width=1)
            ),
            text=[format_currency_int(val)
                  for val in data_sorted['ventas_netas']],
            textposition='inside',
            textfont=dict(color='white', size=10),
            hovertemplate="<b>%{y}</b><br>Ventas: %{text}<br>Facturas: %{customdata}<extra></extra>",
            customdata=data_sorted['num_facturas']
        ))

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
                title="Cliente",  # o "Producto"
                tickfont=dict(size=10)  # AGREGAR ESTA LÍNEA
            ),
            margin=dict(t=20, b=40, l=150, r=80),
            showlegend=False
        )

        return fig
    except Exception as e:
        print(f"❌ Error en top clientes: {e}")
        return create_empty_figure("Error cargando datos", theme)

# Top productos callback


@callback(
    Output('proveedores-ventas-top-productos', 'figure'),
    [Input('proveedores-ventas-dropdown-laboratorio', 'value'),
     Input('proveedores-ventas-dropdown-periodo', 'value'),
     Input('proveedores-ventas-data-store', 'data'),
     Input('proveedores-ventas-theme-store', 'data')]
)
def update_top_productos(laboratorio, periodo, data_store, theme):
    """Actualizar top 10 productos"""
    try:
        if not hasattr(analyzer, 'get_top_productos'):
            return create_empty_figure("Función no disponible", theme)

        data = analyzer.get_top_productos(
            laboratorio or 'Todos', periodo or 'Todos', 10)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            return create_empty_figure("No hay datos de productos disponibles", theme)

        # Ordenar de menor a mayor para gráfico horizontal
        data_sorted = data.sort_values('ventas_netas', ascending=True)

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=data_sorted['ventas_netas'],
            y=[desc[:35] + "..." if len(desc) >
               35 else desc for desc in data_sorted['descripcion']],
            orientation='h',
            marker=dict(
                color='rgba(34, 197, 94, 0.6)',
                line=dict(color='rgba(34, 197, 94, 0.9)', width=1)
            ),
            text=[format_currency_int(val)
                  for val in data_sorted['ventas_netas']],
            textposition='inside',
            textfont=dict(color='white', size=10),
            hovertemplate="<b>%{y}</b><br>Ventas: %{text}<br>Cantidad: %{customdata}<extra></extra>",
            customdata=data_sorted['cantidad_total']
        ))

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
                title="Producto",  # o "Producto"
                tickfont=dict(size=10)  # AGREGAR ESTA LÍNEA
            ),
            margin=dict(t=20, b=40, l=200, r=80),
            showlegend=False
        )

        return fig
    except Exception as e:
        print(f"❌ Error en top productos: {e}")
        return create_empty_figure("Error cargando datos", theme)

# Evolución cliente callback


@callback(
    Output('proveedores-ventas-grafico-evolucion-cliente', 'figure'),
    [Input('proveedores-ventas-dropdown-cliente', 'value'),
     Input('proveedores-ventas-dropdown-laboratorio', 'value'),
     Input('proveedores-ventas-data-store', 'data'),
     Input('proveedores-ventas-theme-store', 'data')]
)
def update_evolucion_cliente(cliente, laboratorio, data_store, theme):
    """Actualizar evolución de ventas por cliente"""
    try:
        theme_styles = get_theme_styles(theme)

        if cliente == 'Seleccione un cliente':
            return create_empty_figure("Seleccione un cliente para ver su evolución", theme)

        if not hasattr(analyzer, 'get_evolucion_cliente'):
            return create_empty_figure("Función no disponible", theme)

        data = analyzer.get_evolucion_cliente(cliente, laboratorio or 'Todos')

        if data.empty:
            return create_empty_figure(f"No hay datos para {cliente}", theme)

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=data['mes_nombre'],
            y=data['ventas_netas'],
            marker=dict(
                color='rgba(139, 92, 246, 0.6)',
                line=dict(color='rgba(139, 92, 246, 0.9)', width=1)
            ),
            text=[format_currency_int(
                val) if val > 50000 else '' for val in data['ventas_netas']],
            textposition='outside',
            textfont=dict(size=9, color=theme_styles['text_color']),
            hovertemplate="<b>%{x}</b><br>Ventas: %{customdata}<br>Facturas: %{text}<extra></extra>",
            customdata=[format_currency_int(val)
                        for val in data['ventas_netas']],
            texttemplate='%{text}'
        ))

        # Calcular totales para el título
        total_ventas = data['ventas_netas'].sum()
        num_meses = len(data)
        promedio_mensual = total_ventas / num_meses if num_meses > 0 else 0

        titulo = (
            f"<span style='font-size:16px; font-weight:bold;'>"
            f"Total: {format_currency_int(total_ventas)} ({num_meses} meses)</span>"
            f"<br><span style='font-size:13px;'>"
            f"Promedio mensual: {format_currency_int(promedio_mensual)}</span>"
            f"<br><span style='font-size:10px;'>{cliente[:60]}{'...' if len(cliente) > 60 else ''}</span>"
        )

        fig.update_layout(
            title=dict(
                text=titulo,
                x=0.5,
                font=dict(color=theme_styles['text_color'])
            ),
            height=480,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=12,
                      color=theme_styles['text_color']),
            xaxis=dict(
                title="Mes",
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                tickangle=-45
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                tickformat='$,.0f',
                title="Ventas ($)"
            ),
            showlegend=False,
            margin=dict(t=110, b=80, l=80, r=40)
        )

        return fig
    except Exception as e:
        print(f"❌ Error en evolución de cliente: {e}")
        return create_empty_figure("Error cargando datos", theme)

# Dropdown clientes matriz callback


@callback(
    Output('proveedores-ventas-dropdown-clientes-matriz', 'options'),
    [Input('proveedores-ventas-dropdown-laboratorio', 'value'),
     Input('proveedores-ventas-data-store', 'data')]
)
def update_clientes_matriz_options(laboratorio, data_store):
    """Actualizar opciones de clientes para la matriz"""
    try:
        if not hasattr(analyzer, 'get_clientes_list'):
            return []

        clientes = analyzer.get_clientes_list(laboratorio or 'Todos')
        # Remover 'Seleccione un cliente' para multi-select
        clientes_filtrados = [
            c for c in clientes if c != 'Seleccione un cliente']
        return [{'label': cliente, 'value': cliente} for cliente in clientes_filtrados]
    except Exception as e:
        print(f"❌ Error actualizando opciones de clientes: {e}")
        return []

# Dropdown cliente callback


@callback(
    Output('proveedores-ventas-dropdown-cliente', 'options'),
    [Input('proveedores-ventas-dropdown-laboratorio', 'value'),
     Input('proveedores-ventas-data-store', 'data')]
)
def update_cliente_options(laboratorio, data_store):
    """Actualizar opciones de cliente para evolución"""
    try:
        if not hasattr(analyzer, 'get_clientes_list'):
            return [{'label': 'Seleccione un cliente', 'value': 'Seleccione un cliente'}]

        clientes = analyzer.get_clientes_list(laboratorio or 'Todos')
        return [{'label': cliente, 'value': cliente} for cliente in clientes]
    except Exception as e:
        print(f"❌ Error actualizando opciones de cliente: {e}")
        return [{'label': 'Seleccione un cliente', 'value': 'Seleccione un cliente'}]

# Reset cliente callback


@callback(
    Output('proveedores-ventas-dropdown-cliente', 'value'),
    [Input('proveedores-ventas-dropdown-laboratorio', 'value')]
)
def reset_cliente_selection(laboratorio):
    """Reiniciar selección de cliente cuando cambia laboratorio"""
    return 'Seleccione un cliente'

# Limit clientes matriz callback


@callback(
    Output('proveedores-ventas-dropdown-clientes-matriz', 'value'),
    [Input('proveedores-ventas-dropdown-clientes-matriz', 'value')],
    prevent_initial_call=True
)
def limit_cliente_selection(selected_clientes):
    """Limitar selección a máximo 10 clientes"""
    if selected_clientes and len(selected_clientes) > 10:
        return selected_clientes[:10]
    return selected_clientes

# Subtitle callback


@callback(
    Output('proveedores-ventas-subtitulo', 'children'),
    [Input('proveedores-ventas-dropdown-laboratorio', 'value'),
     Input('proveedores-ventas-dropdown-periodo', 'value')]
)
def update_subtitle(laboratorio, periodo):
    """Actualizar subtítulo dinámico según filtros"""
    try:
        parts = []

        if laboratorio and laboratorio != 'Todos':
            parts.append(f"Laboratorio: {laboratorio}")
        else:
            parts.append("Todos los Laboratorios")

        if periodo and periodo != 'Todos':
            parts.append(f"Período: {periodo}")
        else:
            parts.append("Todos los períodos")

        return " • ".join(parts)

    except Exception as e:
        print(f"❌ Error actualizando subtítulo: {e}")
        return "Análisis de ventas por laboratorio"

# Theme callbacks


@callback(
    [Output('proveedores-ventas-theme-store', 'data'),
     Output('proveedores-ventas-theme-toggle', 'children'),
     Output('proveedores-ventas-main-container', 'style')],
    [Input('proveedores-ventas-theme-toggle', 'n_clicks')],
    [State('proveedores-ventas-theme-store', 'data')]
)
def toggle_theme(n_clicks, current_theme):
    """Toggle entre tema claro y oscuro"""
    if not n_clicks:
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

# Dropdown styles callback


@callback(
    [Output('proveedores-ventas-dropdown-laboratorio', 'style'),
     Output('proveedores-ventas-dropdown-periodo', 'style'),
     Output('proveedores-ventas-dropdown-tipo-periodo', 'style'),
     Output('proveedores-ventas-dropdown-clientes-matriz', 'style'),
     Output('proveedores-ventas-dropdown-cliente', 'style'),
     Output('proveedores-ventas-dropdown-laboratorio', 'className'),
     Output('proveedores-ventas-dropdown-periodo', 'className'),
     Output('proveedores-ventas-dropdown-tipo-periodo', 'className'),
     Output('proveedores-ventas-dropdown-clientes-matriz', 'className'),
     Output('proveedores-ventas-dropdown-cliente', 'className')],
    [Input('proveedores-ventas-theme-store', 'data')]
)
def update_dropdown_styles(theme):
    """Actualizar estilos de dropdowns según tema"""
    dropdown_style = get_dropdown_style(theme)
    dropdown_style['fontFamily'] = 'Inter'

    css_class = 'dash-dropdown dark-theme' if theme == 'dark' else 'dash-dropdown'

    return [dropdown_style] * 5 + [css_class] * 5


@callback(
    [Output('proveedores-ventas-row1-container', 'style'),
     Output('proveedores-ventas-row2-container', 'style'),
     Output('proveedores-ventas-row3-container', 'style'),
     Output('proveedores-ventas-row4-container', 'style'),
     Output('proveedores-ventas-row5-container', 'style'),
     Output('proveedores-ventas-controls-container', 'style'),
     Output('proveedores-ventas-header-container', 'style')],
    [Input('proveedores-ventas-theme-store', 'data')]
)
def update_container_styles(theme):
    """
    Actualizar estilos de contenedores según tema.
    """
    theme_styles = get_theme_styles(theme)

    base_style = {
        'backgroundColor': theme_styles['paper_color'],
        'padding': '24px',
        'borderRadius': '16px',
        'boxShadow': theme_styles['card_shadow'],
        'marginBottom': '24px',
        'color': theme_styles['text_color'],
        'transition': 'all 0.3s ease'
    }

    controls_style = {
        'display': 'flex',
        'gap': '24px',
        'alignItems': 'stretch',
        'backgroundColor': theme_styles['paper_color'],
        'borderRadius': '16px',
        'padding': '24px',
        'marginBottom': '24px',
        'boxShadow': theme_styles['card_shadow'],
        'flexWrap': 'wrap',
        'color': theme_styles['text_color']
    }

    header_style = {
        'display': 'flex',
        'alignItems': 'center',
        'justifyContent': 'space-between',
        'backgroundColor': theme_styles['paper_color'] if theme == 'dark' else 'linear-gradient(135deg, rgba(209, 213, 219, 0.75) 0%, rgba(156, 163, 175, 0.8) 25%, rgba(107, 114, 128, 0.85) 50%, rgba(75, 85, 99, 0.9) 75%, rgba(55, 65, 81, 0.95) 100%)',
        'borderRadius': '20px',
        'padding': '32px 40px',
        'marginBottom': '24px',
        'boxShadow': theme_styles['card_shadow'],
        'position': 'relative',
        'minHeight': '80px',
        'color': '#ffffff'
    }

    return [base_style] * 5 + [controls_style, header_style]


@callback(
    Output('proveedores-ventas-grafico-dia-semana', 'figure'),
    [Input('proveedores-ventas-dropdown-laboratorio', 'value'),
     Input('proveedores-ventas-dropdown-periodo', 'value'),
     Input('proveedores-ventas-data-store', 'data'),
     Input('proveedores-ventas-theme-store', 'data')]
)
def update_grafico_dia_semana(laboratorio, periodo, data_store, theme):
    """Actualizar gráfico de estacionalidad por día de semana"""
    try:
        df = analyzer.filter_data(laboratorio or 'Todos', periodo or 'Todos')
        theme_styles = get_theme_styles(theme)

        if df.empty:
            return create_empty_figure("Sin datos", theme)

        # Orden correcto de días de semana
        dias_orden = ['Lunes', 'Martes', 'Miércoles',
                      'Jueves', 'Viernes', 'Sábado', 'Domingo']

        resultado = df.groupby('dia_semana_es').agg({
            'precio_neto': 'sum',
            'numero': 'nunique'
        }).reset_index()

        # Asegurar orden correcto
        resultado['dia_semana_es'] = pd.Categorical(
            resultado['dia_semana_es'], categories=dias_orden, ordered=True)
        resultado = resultado.sort_values('dia_semana_es')

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=resultado['dia_semana_es'],
            y=resultado['precio_neto'],
            marker=dict(
                color='rgba(34, 197, 94, 0.6)',
                line=dict(color='rgba(34, 197, 94, 0.9)', width=1)
            ),
            text=[format_currency_int(
                val) if val > 0 else '' for val in resultado['precio_neto']],
            textposition='outside',
            textfont=dict(size=8, color=theme_styles['text_color']),
            hovertemplate="<b>%{x}</b><br>Ventas: %{customdata}<extra></extra>",
            customdata=[format_currency_int(val)
                        for val in resultado['precio_neto']]
        ))

        fig.update_layout(
            height=400,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=10,
                      color=theme_styles['text_color']),
            xaxis=dict(
                title="Día",
                showgrid=False,
                tickangle=-45
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                tickformat='$,.0f',
                title="Ventas"
            ),
            showlegend=False,
            margin=dict(t=20, b=60, l=60, r=20)
        )

        return fig
    except Exception as e:
        print(f"❌ Error en gráfico día semana: {e}")
        return create_empty_figure("Error", theme)

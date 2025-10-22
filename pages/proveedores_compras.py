# pages/proveedores_compras.py - SECCIÓN 1: IMPORTACIONES Y LAYOUT

import time
from datetime import datetime, date
import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import locale

# Configurar locale para español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Linux/Mac
except:
    try:
        locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')  # Windows
    except:
        try:
            locale.setlocale(locale.LC_TIME, 'es_ES')  # Alternativo
        except:
            print("⚠️ No se pudo configurar locale en español")

# Importar componentes
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

# # Importar analyzer
# try:
#     from analyzers import ProveedoresComprasAnalyzer
#     analyzer = ProveedoresComprasAnalyzer()
#     print("✅ ProveedoresComprasAnalyzer inicializado correctamente")
# except Exception as e:
#     print(
#         f"⚠️ [ProveedoresComprasPage] Carga inicial falló (se recargará on-demand): {e}")
#     analyzer = None


# # FUNCIONES AUXILIARES

# def get_default_laboratorio():
#     """Obtener el primer laboratorio que no sea 'Todos'."""
#     try:
#         if analyzer and hasattr(analyzer, 'laboratorios_list'):
#             laboratorios = analyzer.laboratorios_list
#             if len(laboratorios) > 1 and laboratorios[0] == 'Todos':
#                 return laboratorios[1]
#             elif len(laboratorios) > 0 and laboratorios[0] != 'Todos':
#                 return laboratorios[0]
#         return 'Todos'
#     except:
#         return 'Todos'


# def create_data_table(df, columns_config, theme='light', max_rows=10):
#     """Crear tabla de datos estilizada"""
#     if df.empty:
#         return html.Div("No hay datos disponibles", style={
#             'textAlign': 'center',
#             'padding': '20px',
#             'color': '#6b7280',
#             'fontStyle': 'italic'
#         })

#     theme_styles = get_theme_styles(theme)
#     df_display = df.head(max_rows)

#     # Crear encabezados
#     headers = [
#         html.Th(config['title'], style={
#             'padding': '12px 8px',
#             'backgroundColor': theme_styles['paper_color'],
#             'color': theme_styles['text_color'],
#             'fontWeight': 'bold',
#             'fontSize': '12px',
#             'borderBottom': f'2px solid {theme_styles["grid_color"]}',
#             'textAlign': config.get('align', 'left')
#         }) for config in columns_config
#     ]

#     # Crear filas
#     rows = []
#     for _, row in df_display.iterrows():
#         cells = []
#         for config in columns_config:
#             col = config['column']
#             value = row[col]

#             # Formatear valor según tipo
#             if config.get('format') == 'currency':
#                 formatted_value = format_currency_int(value)
#             elif config.get('format') == 'number':
#                 formatted_value = f"{value:,.0f}" if pd.notna(value) else '0'
#             elif config.get('format') == 'decimal':
#                 formatted_value = f"{value:.2f}" if pd.notna(value) else '0.00'
#             else:
#                 formatted_value = str(value) if pd.notna(value) else '-'

#             # Aplicar colores según valor
#             cell_style = {
#                 'padding': '8px',
#                 'fontSize': '11px',
#                 'borderBottom': f'1px solid {theme_styles["grid_color"]}',
#                 'textAlign': config.get('align', 'left'),
#                 'color': theme_styles['text_color']
#             }

#             if config.get('highlight'):
#                 if isinstance(value, (int, float)) and value <= config.get('highlight_threshold', 0):
#                     cell_style['backgroundColor'] = '#fef3c7'
#                     cell_style['fontWeight'] = 'bold'

#             cells.append(html.Td(formatted_value, style=cell_style))

#         rows.append(html.Tr(cells))

#     return html.Table([
#         html.Thead([html.Tr(headers)]),
#         html.Tbody(rows)
#     ], style={
#         'width': '100%',
#         'borderCollapse': 'collapse',
#         'backgroundColor': theme_styles['paper_color'],
#         'boxShadow': theme_styles['card_shadow'],
#         'borderRadius': '8px',
#         'overflow': 'hidden'
#     })


# def create_empty_figure(message, theme):
#     """Crear figura vacía con mensaje"""
#     theme_styles = get_theme_styles(theme)
#     fig = go.Figure()
#     fig.add_annotation(
#         text=message,
#         xref="paper", yref="paper",
#         x=0.5, y=0.5, showarrow=False,
#         font=dict(size=16, color=theme_styles['text_color'])
#     )
#     fig.update_layout(
#         height=400,
#         paper_bgcolor=theme_styles['plot_bg'],
#         plot_bgcolor=theme_styles['plot_bg']
#     )
#     return fig


# # LAYOUT DE LA PÁGINA

# layout = html.Div([
#     # Stores
#     dcc.Store(id='proveedores-compras-theme-store', data='light'),
#     dcc.Store(id='proveedores-compras-data-store', data={'last_update': 0}),

#     # Área de notificaciones
#     html.Div(id='proveedores-compras-notification-area', children=[], style={
#         'position': 'fixed',
#         'top': '20px',
#         'right': '20px',
#         'zIndex': '1000',
#         'maxWidth': '300px'
#     }),

#     html.Div([
#         # HEADER
#         html.Div([
#             # Logo
#             html.Div([
#                 html.Img(
#                     src='/assets/logo.png',
#                     className="top-left-logo",
#                     alt="Logo de la empresa",
#                     style={
#                         'maxWidth': '160px',
#                         'height': 'auto',
#                         'filter': 'drop-shadow(0 8px 16px rgba(30, 58, 138, 0.3))',
#                         'transition': 'all 0.3s ease'
#                     }
#                 )
#             ], className="logo-left-container"),

#             # Título central
#             html.Div([
#                 html.H1(
#                     "Proveedores - Compras",
#                     className="main-title",
#                     id='proveedores-compras-titulo-principal'
#                 ),
#                 html.P(
#                     "Análisis de compras y gestión de inventarios",
#                     className="main-subtitle",
#                     id='proveedores-compras-subtitulo'
#                 )
#             ], className="center-title-section"),

#             # Toggle de tema
#             html.Div([
#                 html.Button(
#                     "🌙",
#                     id="proveedores-compras-theme-toggle",
#                     title="Cambiar tema",
#                     n_clicks=0,
#                     style={
#                         'background': 'transparent',
#                         'border': '2px solid rgba(255, 255, 255, 0.3)',
#                         'borderRadius': '50%',
#                         'width': '44px',
#                         'height': '44px',
#                         'fontSize': '18px',
#                         'cursor': 'pointer',
#                         'transition': 'all 0.3s ease',
#                         'display': 'flex',
#                         'alignItems': 'center',
#                         'justifyContent': 'center'
#                     }
#                 )
#             ], className="logout-right-container")
#         ], className="top-header", id='proveedores-compras-header-container'),

#         # CONTROLES
#         html.Div([
#             # Dropdown Laboratorio
#             html.Div([
#                 html.Label("Laboratorio:", style={
#                     'fontWeight': '600',
#                     'fontSize': '14px',
#                     'marginBottom': '8px',
#                     'display': 'block'
#                 }),
#                 dcc.Dropdown(
#                     id='proveedores-compras-dropdown-laboratorio',
#                     options=[{'label': lab, 'value': lab} for lab in (
#                         analyzer.laboratorios_list if analyzer else ['Todos'])],
#                     value=get_default_laboratorio(),
#                     placeholder="Seleccionar laboratorio...",
#                     clearable=True,
#                     style={'height': '44px',
#                            'borderRadius': '12px', 'fontSize': '14px'},
#                     maxHeight=150
#                 )
#             ], style={'flex': '1', 'minWidth': '250px'}),

#             # Dropdown Período
#             html.Div([
#                 html.Label("Período:", style={
#                     'fontWeight': '600',
#                     'fontSize': '14px',
#                     'marginBottom': '8px',
#                     'display': 'block'
#                 }),
#                 dcc.Dropdown(
#                     id='proveedores-compras-dropdown-periodo',
#                     options=[{'label': p, 'value': p} for p in (
#                         analyzer.periodos_list if analyzer else ['Todos'])],
#                     value='Todos',
#                     placeholder="Seleccionar período...",
#                     clearable=True,
#                     style={'height': '44px',
#                            'borderRadius': '12px', 'fontSize': '14px'}
#                 )
#             ], style={'flex': '1', 'minWidth': '200px'}),

#             # Botón actualizar
#             html.Div([
#                 html.Button(
#                     "🔄 Actualizar",
#                     id="proveedores-compras-btn-actualizar",
#                     n_clicks=0,
#                     style={
#                         'background': 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
#                         'color': '#ffffff',
#                         'border': 'none',
#                         'padding': '12px 20px',
#                         'borderRadius': '25px',
#                         'fontWeight': '600',
#                         'fontSize': '14px',
#                         'cursor': 'pointer',
#                         'boxShadow': '0 4px 12px rgba(59, 130, 246, 0.3)',
#                         'transition': 'all 0.3s ease',
#                         'height': '44px',
#                         'marginRight': '8px'
#                     }
#                 )
#             ], style={'display': 'flex', 'alignItems': 'flex-end'})
#         ], id='proveedores-compras-controls-container', style={
#             'display': 'flex',
#             'gap': '24px',
#             'alignItems': 'stretch',
#             'borderRadius': '16px',
#             'padding': '24px',
#             'marginBottom': '24px',
#             'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
#             'flexWrap': 'wrap'
#         }),

#         # CARDS DE MÉTRICAS
#         html.Div(id="proveedores-compras-metrics-cards",
#                  children=[], style={'marginBottom': '24px'}),

#         # SECCIÓN 1: PRODUCTOS CRÍTICOS
#         html.Div([
#             html.H3("🚨 Productos Críticos - Requieren Reabastecimiento Urgente", style={
#                 'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter',
#                 'color': '#dc2626'
#             }),
#             html.Div(id='proveedores-compras-tabla-criticos', children=[])
#         ], id='proveedores-compras-row0-container', style={
#             'borderRadius': '16px',
#             'padding': '24px',
#             'marginBottom': '24px',
#             'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
#             'border': '2px solid #fecaca'
#         }),

#         # SECCIÓN 2: ANÁLISIS DE ROTACIÓN
#         html.Div([
#             html.H3("📊 Análisis de Rotación de Inventarios", style={
#                 'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'
#             }),
#             html.Div([
#                 html.Div([
#                     dcc.Graph(id='proveedores-compras-grafico-rotacion')
#                 ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingRight': '10px'}),

#                 html.Div([
#                     dcc.Graph(id='proveedores-compras-grafico-dias-inventario')
#                 ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'paddingLeft': '10px'})
#             ])
#         ], id='proveedores-compras-row1-container', style={
#             'borderRadius': '16px',
#             'padding': '24px',
#             'marginBottom': '24px',
#             'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)'
#         }),

#         # SECCIÓN 3: TOP PROVEEDORES (SOLO)
#         html.Div([
#             html.H3("🏭 Top 10 - Proveedores por Compras (General)", style={
#                 'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'
#             }),
#             dcc.Graph(id='proveedores-compras-top-proveedores')
#         ], id='proveedores-compras-row2-container', style={
#             'borderRadius': '16px',
#             'padding': '24px',
#             'marginBottom': '24px',
#             'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)'
#         }),

#         # SECCIÓN 3.5: COMPARACIÓN LABORATORIOS (NUEVA FILA)
#         html.Div([
#             html.H3("⚖️ Comparación entre Laboratorios", style={
#                 'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'
#             }),
#             dcc.Graph(id='proveedores-compras-comparacion-labs')
#         ], id='proveedores-compras-row2-5-container', style={
#             'borderRadius': '16px',
#             'padding': '24px',
#             'marginBottom': '24px',
#             'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)'
#         }),

#         # SECCIÓN 4: OPORTUNIDADES Y STOCK MUERTO
#         html.Div([
#             html.Div([
#                 html.H3("💡 Oportunidades de Compra", style={
#                     'textAlign': 'center', 'marginBottom': '15px', 'fontFamily': 'Inter',
#                     'color': '#059669'
#                 }),
#                 html.P("Productos con alta rotación y stock bajo", style={
#                     'textAlign': 'center', 'fontSize': '12px', 'color': '#6b7280',
#                     'marginBottom': '15px'
#                 }),
#                 html.Div(id='proveedores-compras-tabla-oportunidades', children=[])
#             ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%', 'verticalAlign': 'top'}),

#             html.Div([
#                 html.H3("⚠️ Inventario Sin Rotación", style={
#                     'textAlign': 'center', 'marginBottom': '15px', 'fontFamily': 'Inter',
#                     'color': '#dc2626'
#                 }),
#                 html.P("Productos con stock pero sin ventas", style={
#                     'textAlign': 'center', 'fontSize': '12px', 'color': '#6b7280',
#                     'marginBottom': '15px'
#                 }),
#                 html.Div(id='proveedores-compras-tabla-sin-rotacion', children=[])
#             ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%', 'verticalAlign': 'top'})
#         ], id='proveedores-compras-row3-container', style={
#             'borderRadius': '16px',
#             'padding': '24px',
#             'marginBottom': '24px',
#             'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)'
#         }),

#         # SECCIÓN 5: MATRIZ DE GESTIÓN
#         html.Div([
#             html.H3("🎯 Matriz de Gestión de Inventarios", style={
#                 'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter'
#             }),
#             html.P("Análisis estratégico: Rotación vs Valor de Inventario", style={
#                 'textAlign': 'center', 'fontSize': '14px', 'color': '#6b7280',
#                 'marginBottom': '20px'
#             }),
#             dcc.Graph(id='proveedores-compras-matriz-gestion')
#         ], id='proveedores-compras-row4-container', style={
#             'borderRadius': '16px',
#             'padding': '24px',
#             'marginBottom': '24px',
#             'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)'
#         }),

#         # SECCIÓN 6: PREDICCIONES CON IA
#         html.Div([
#             html.Div([
#                 html.H2("🤖 Predicciones con Inteligencia Artificial", style={
#                     'textAlign': 'center', 'marginBottom': '10px', 'fontFamily': 'Inter',
#                     'background': 'linear-gradient(45deg, #667eea 0%, #764ba2 100%)',
#                     'background-clip': 'text',
#                     '-webkit-background-clip': 'text',
#                     '-webkit-text-fill-color': 'transparent',
#                     'fontSize': '24px'
#                 }),
#                 html.P("Recomendaciones inteligentes basadas en análisis predictivo", style={
#                     'textAlign': 'center', 'fontSize': '14px', 'color': '#6b7280',
#                     'marginBottom': '30px'
#                 }),

#                 # Toggle para entrenar modelo
#                 html.Div([
#                     html.Button(
#                         "🔄 Entrenar/Actualizar Modelo IA",
#                         id="proveedores-compras-btn-entrenar-modelo",
#                         n_clicks=0,
#                         style={
#                             'background': 'linear-gradient(45deg, #667eea 0%, #764ba2 100%)',
#                             'color': '#ffffff',
#                             'border': 'none',
#                             'padding': '12px 24px',
#                             'borderRadius': '25px',
#                             'fontWeight': '600',
#                             'fontSize': '14px',
#                             'cursor': 'pointer',
#                             'boxShadow': '0 4px 15px rgba(102, 126, 234, 0.4)',
#                             'transition': 'all 0.3s ease',
#                             'marginBottom': '20px'
#                         }
#                     ),
#                     html.Div(id='proveedores-compras-modelo-status', children=[], style={
#                         'textAlign': 'center', 'marginBottom': '20px'
#                     })
#                 ], style={'textAlign': 'center'}),

#             ]),

#             # Métricas de predicciones
#             html.Div(id="proveedores-compras-prediccion-metrics", children=[],
#                      style={'marginBottom': '20px'}),

#             # Gráficos de predicciones
#             html.Div([
#                 html.Div([
#                     html.H4("📊 Análisis de Urgencia - Predicciones", style={
#                         'textAlign': 'center', 'marginBottom': '15px', 'fontFamily': 'Inter'
#                     }),
#                     dcc.Graph(id='proveedores-compras-grafico-urgencia-pred')
#                 ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'}),

#                 html.Div([
#                     html.H4("🏭 Compras Sugeridas por Proveedor", style={
#                         'textAlign': 'center', 'marginBottom': '15px', 'fontFamily': 'Inter'
#                     }),
#                     dcc.Graph(id='proveedores-compras-grafico-proveedores-pred')
#                 ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'})
#             ]),

#             # Tabla de recomendaciones
#             html.Div([
#                 html.H4("💡 Recomendaciones de Compra Prioritarias", style={
#                     'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter',
#                     'color': '#667eea'
#                 }),
#                 html.Div(id='proveedores-compras-tabla-predicciones', children=[])
#             ])

#         ], id='proveedores-compras-row-predicciones', style={
#             'borderRadius': '16px',
#             'padding': '30px',
#             'marginBottom': '24px',
#             'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
#             'background': 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)',
#             'border': '1px solid rgba(102, 126, 234, 0.2)'
#         }),

#         html.Div([
#             html.H4("🔍 Interpretabilidad del Modelo", style={
#                 'textAlign': 'center', 'marginBottom': '15px', 'fontFamily': 'Inter'
#             }),
#             dcc.Graph(id='proveedores-compras-feature-importance')
#         ], style={'marginTop': '20px'})

#     ], style={
#         'margin': '0 auto',
#         'padding': '0 40px',
#     }),

# ], id='proveedores-compras-main-container', style={
#     'width': '100%',
#     'minHeight': '100vh',
#     'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
#     'transition': 'all 0.3s ease',
#     'padding': '20px 0',
#     'background': 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 25%, #f8fafc 50%, #f1f5f9 100%)',
#     'backgroundSize': '400% 400%',
#     'animation': 'gradientShift 15s ease infinite'
# })


# @callback(
#     Output('proveedores-compras-data-store', 'data'),
#     [Input('proveedores-compras-btn-actualizar', 'n_clicks')],
#     prevent_initial_call=True
# )
# def update_data_optimized(n_clicks):
#     """Callback para recargar datos desde la base de datos"""
#     if n_clicks > 0:
#         try:
#             start_time = time.time()

#             if analyzer and hasattr(analyzer, 'reload_data'):
#                 analyzer.reload_data(year=2025, limit_records=None)
#                 records_count = len(
#                     getattr(analyzer, 'df_compras', pd.DataFrame()))
#             else:
#                 records_count = 0

#             load_time = time.time() - start_time

#             return {
#                 'last_update': n_clicks,
#                 'timestamp': datetime.now().isoformat(),
#                 'success': True,
#                 'load_time': load_time,
#                 'records_count': records_count
#             }
#         except Exception as e:
#             print(f"❌ Error en actualización de compras: {e}")
#             return {
#                 'last_update': n_clicks,
#                 'timestamp': datetime.now().isoformat(),
#                 'error': str(e),
#                 'success': False
#             }

#     return dash.no_update


# @callback(
#     Output('proveedores-compras-notification-area', 'children'),
#     [Input('proveedores-compras-data-store', 'data')],
#     prevent_initial_call=True
# )
# def show_notification(data_store):
#     """Mostrar notificación de actualización de datos"""
#     if data_store and data_store.get('last_update', 0) > 0:
#         if data_store.get('error'):
#             return html.Div([
#                 html.Div([
#                     html.Span("❌", style={'marginRight': '8px'}),
#                     html.Span("Error al actualizar datos"),
#                     html.Br(),
#                     html.Small(str(data_store.get('error', ''))[:100] + "...",
#                                style={'fontSize': '10px', 'opacity': '0.8'})
#                 ], style={
#                     'backgroundColor': '#e74c3c',
#                     'color': 'white',
#                     'padding': '12px 16px',
#                     'borderRadius': '6px',
#                     'marginBottom': '10px',
#                     'boxShadow': '0 4px 8px rgba(0,0,0,0.2)',
#                     'fontSize': '12px'
#                 })
#             ])
#         else:
#             load_time = data_store.get('load_time', 0)
#             records_count = data_store.get('records_count', 0)

#             return html.Div([
#                 html.Div([
#                     html.Span("✅", style={'marginRight': '8px'}),
#                     html.Span("Datos actualizados correctamente"),
#                     html.Br(),
#                     html.Small(f"{records_count} registros en {load_time:.1f}s",
#                                style={'fontSize': '10px', 'opacity': '0.8'})
#                 ], style={
#                     'backgroundColor': '#27ae60',
#                     'color': 'white',
#                     'padding': '12px 16px',
#                     'borderRadius': '6px',
#                     'marginBottom': '10px',
#                     'boxShadow': '0 4px 8px rgba(0,0,0,0.2)',
#                     'fontSize': '12px'
#                 })
#             ])
#     return []


# @callback(
#     Output('proveedores-compras-metrics-cards', 'children'),
#     [Input('proveedores-compras-dropdown-laboratorio', 'value'),
#      Input('proveedores-compras-dropdown-periodo', 'value'),
#      Input('proveedores-compras-data-store', 'data'),
#      Input('proveedores-compras-theme-store', 'data')]
# )
# def update_metrics_cards(laboratorio, periodo, data_store, theme):
#     """Actualizar cards de métricas principales"""
#     try:
#         is_dark = theme == 'dark'

#         # Obtener resumen de datos con manejo de errores
#         if not analyzer:
#             resumen = {
#                 'total_compras': 0, 'total_costo_compras': 0, 'total_stock': 0,
#                 'valor_inventario': 0, 'productos_criticos': 0, 'num_productos': 0,
#                 'rotacion_promedio': 0, 'dias_inventario_promedio': 0
#             }
#         else:
#             try:
#                 resumen = analyzer.get_resumen_compras(
#                     laboratorio or 'Todos', periodo or 'Todos')
#             except Exception as e:
#                 print(f"❌ Error obteniendo resumen: {e}")
#                 resumen = {
#                     'total_compras': 0, 'total_costo_compras': 0, 'total_stock': 0,
#                     'valor_inventario': 0, 'productos_criticos': 0, 'num_productos': 0,
#                     'rotacion_promedio': 0, 'dias_inventario_promedio': 0
#                 }

#         # Configurar datos de métricas
#         metrics_data = [
#             {
#                 'title': 'Valor Compras',
#                 'value': format_currency_int(resumen['total_costo_compras']),
#                 'icon': '💰',
#                 'color': METRIC_COLORS['success'],
#                 'card_id': 'comp-card-1'
#             },
#             {
#                 'title': 'Valor Inventario',
#                 'value': format_currency_int(resumen['valor_inventario']),
#                 'icon': '📦',
#                 'color': METRIC_COLORS['primary'],
#                 'card_id': 'comp-card-2'
#             },
#             {
#                 'title': 'Rotación Promedio',
#                 'value': f"{resumen['rotacion_promedio']:.1f}x",
#                 'icon': '🔄',
#                 'color': METRIC_COLORS['indigo'],
#                 'card_id': 'comp-card-3'
#             },
#             {
#                 'title': 'Días Inventario',
#                 'value': f"{resumen['dias_inventario_promedio']:.0f} días",
#                 'icon': '📅',
#                 'color': METRIC_COLORS['warning'],
#                 'card_id': 'comp-card-4'
#             },
#             {
#                 'title': 'Stock Total',
#                 'value': f"{resumen['total_stock']:,.0f}",
#                 'icon': '📊',
#                 'color': METRIC_COLORS['teal'],
#                 'card_id': 'comp-card-5'
#             },
#             {
#                 'title': 'Productos Críticos',
#                 'value': f"{resumen['productos_criticos']:,}",
#                 'icon': '🚨',
#                 'color': METRIC_COLORS['danger'],
#                 'card_id': 'comp-card-6'
#             },
#             {
#                 'title': '# Productos',
#                 'value': f"{resumen['num_productos']:,}",
#                 'icon': '🔢',
#                 'color': METRIC_COLORS['purple'],
#                 'card_id': 'comp-card-7'
#             },
#             {
#                 'title': 'Unidades Compradas',
#                 'value': f"{resumen['total_compras']:,.0f}",
#                 'icon': '📈',
#                 'color': METRIC_COLORS['orange'],
#                 'card_id': 'comp-card-8'
#             }
#         ]

#         # Crear grid de métricas con 4 columnas
#         return create_metrics_grid(
#             metrics=metrics_data,
#             is_dark=is_dark,
#             columns=4,
#             gap="20px"
#         )

#     except Exception as e:
#         print(f"❌ Error actualizando metrics cards: {e}")
#         import traceback
#         traceback.print_exc()

#         # Crear métricas vacías como fallback
#         try:
#             return create_empty_metrics(is_dark=theme == 'dark', count=8)
#         except Exception as e2:
#             print(f"❌ Error creando métricas vacías: {e2}")
#             return html.Div([
#                 html.P("Error cargando métricas", style={
#                     'textAlign': 'center',
#                     'color': '#e74c3c',
#                     'padding': '20px',
#                     'fontFamily': 'Inter'
#                 })
#             ])


# @callback(
#     Output('proveedores-compras-subtitulo', 'children'),
#     [Input('proveedores-compras-dropdown-laboratorio', 'value'),
#      Input('proveedores-compras-dropdown-periodo', 'value')]
# )
# def update_subtitle(laboratorio, periodo):
#     """Actualizar subtítulo dinámico según filtros"""
#     try:
#         parts = []

#         if laboratorio and laboratorio != 'Todos':
#             parts.append(f"Laboratorio: {laboratorio}")
#         else:
#             parts.append("Todos los Laboratorios")

#         if periodo and periodo != 'Todos':
#             parts.append(f"Período: {periodo}")
#         else:
#             parts.append("Todos los períodos")

#         return " • ".join(parts)

#     except Exception as e:
#         print(f"❌ Error actualizando subtítulo: {e}")
#         return "Análisis de compras y gestión de inventarios"


# # ==================== CALLBACKS DE TEMA ====================

# @callback(
#     [Output('proveedores-compras-theme-store', 'data'),
#      Output('proveedores-compras-theme-toggle', 'children'),
#      Output('proveedores-compras-main-container', 'style')],
#     [Input('proveedores-compras-theme-toggle', 'n_clicks')],
#     [State('proveedores-compras-theme-store', 'data')]
# )
# def toggle_theme(n_clicks, current_theme):
#     """Toggle entre tema claro y oscuro"""
#     if not n_clicks:
#         return (
#             "light",
#             "🌙",
#             {
#                 'width': '100%', 'minHeight': '100vh',
#                 'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
#                 'transition': 'all 0.3s ease', 'padding': '20px 0',
#                 'background': 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 25%, #f8fafc 50%, #f1f5f9 100%)',
#                 'backgroundSize': '400% 400%',
#                 'animation': 'gradientShift 15s ease infinite',
#                 'color': '#111827'
#             }
#         )

#     is_dark = current_theme != 'dark'
#     icon = "☀️" if is_dark else "🌙"
#     new_theme = 'dark' if is_dark else 'light'

#     if is_dark:
#         return (
#             new_theme,
#             icon,
#             {
#                 'width': '100%', 'minHeight': '100vh',
#                 'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
#                 'transition': 'all 0.3s ease', 'padding': '20px 0',
#                 'background': 'linear-gradient(135deg, #0f172a 0%, #1e293b 25%, #334155 50%, #475569 100%)',
#                 'backgroundSize': '400% 400%',
#                 'animation': 'gradientShift 15s ease infinite',
#                 'color': '#f8fafc'
#             }
#         )
#     else:
#         return (
#             new_theme,
#             icon,
#             {
#                 'width': '100%', 'minHeight': '100vh',
#                 'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
#                 'transition': 'all 0.3s ease', 'padding': '20px 0',
#                 'background': 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 25%, #f8fafc 50%, #f1f5f9 100%)',
#                 'backgroundSize': '400% 400%',
#                 'animation': 'gradientShift 15s ease infinite',
#                 'color': '#111827'
#             }
#         )


# @callback(
#     [Output('proveedores-compras-dropdown-laboratorio', 'style'),
#      Output('proveedores-compras-dropdown-periodo', 'style'),
#      Output('proveedores-compras-dropdown-laboratorio', 'className'),
#      Output('proveedores-compras-dropdown-periodo', 'className')],
#     [Input('proveedores-compras-theme-store', 'data')]
# )
# def update_dropdown_styles(theme):
#     """Actualizar estilos de dropdowns según tema"""
#     dropdown_style = get_dropdown_style(theme)
#     dropdown_style['fontFamily'] = 'Inter'

#     css_class = 'dash-dropdown dark-theme' if theme == 'dark' else 'dash-dropdown'

#     return [dropdown_style] * 2 + [css_class] * 2


# @callback(
#     [Output('proveedores-compras-row0-container', 'style'),
#      Output('proveedores-compras-row1-container', 'style'),
#      Output('proveedores-compras-row2-container', 'style'),
#      Output('proveedores-compras-row2-5-container', 'style'),
#      Output('proveedores-compras-row3-container', 'style'),
#      Output('proveedores-compras-row4-container', 'style'),
#      Output('proveedores-compras-row-predicciones', 'style'),
#      Output('proveedores-compras-controls-container', 'style'),
#      Output('proveedores-compras-header-container', 'style')],
#     [Input('proveedores-compras-theme-store', 'data')]
# )
# def update_container_styles(theme):
#     """Actualizar estilos de contenedores según tema"""
#     theme_styles = get_theme_styles(theme)

#     base_style = {
#         'backgroundColor': theme_styles['paper_color'],
#         'padding': '24px',
#         'borderRadius': '16px',
#         'boxShadow': theme_styles['card_shadow'],
#         'marginBottom': '24px',
#         'color': theme_styles['text_color'],
#         'transition': 'all 0.3s ease'
#     }

#     # Estilo especial para contenedor de críticos (con borde rojo)
#     criticos_style = base_style.copy()
#     criticos_style['border'] = '2px solid #fecaca'

#     controls_style = {
#         'display': 'flex',
#         'gap': '24px',
#         'alignItems': 'stretch',
#         'backgroundColor': theme_styles['paper_color'],
#         'borderRadius': '16px',
#         'padding': '24px',
#         'marginBottom': '24px',
#         'boxShadow': theme_styles['card_shadow'],
#         'flexWrap': 'wrap',
#         'color': theme_styles['text_color']
#     }

#     header_style = {
#         'display': 'flex',
#         'alignItems': 'center',
#         'justifyContent': 'space-between',
#         'backgroundColor': theme_styles['paper_color'] if theme == 'dark' else 'linear-gradient(135deg, rgba(209, 213, 219, 0.75) 0%, rgba(156, 163, 175, 0.8) 25%, rgba(107, 114, 128, 0.85) 50%, rgba(75, 85, 99, 0.9) 75%, rgba(55, 65, 81, 0.95) 100%)',
#         'borderRadius': '20px',
#         'padding': '32px 40px',
#         'marginBottom': '24px',
#         'boxShadow': theme_styles['card_shadow'],
#         'position': 'relative',
#         'minHeight': '80px',
#         'color': '#ffffff'
#     }

#     predicciones_style = base_style.copy()
#     predicciones_style.update({
#         # 'background': 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)',
#         'border': '1px solid rgba(102, 126, 234, 0.2)',
#         'padding': '30px'
#     })

#     return [criticos_style] + [base_style] * 5 + [predicciones_style] + [controls_style, header_style]


# @callback(
#     Output('proveedores-compras-tabla-criticos', 'children'),
#     [Input('proveedores-compras-dropdown-laboratorio', 'value'),
#      Input('proveedores-compras-dropdown-periodo', 'value'),
#      Input('proveedores-compras-data-store', 'data'),
#      Input('proveedores-compras-theme-store', 'data')]
# )
# def update_tabla_criticos(laboratorio, periodo, data_store, theme):
#     """Actualizar tabla de productos críticos"""
#     try:
#         if not analyzer:
#             return html.Div("Analyzer no disponible", style={
#                 'textAlign': 'center', 'color': '#dc2626', 'padding': '20px'
#             })

#         data = analyzer.get_productos_criticos(
#             laboratorio or 'Todos', periodo or 'Todos', top_n=15)

#         if data.empty:
#             return html.Div("✅ No hay productos críticos en este momento", style={
#                 'textAlign': 'center',
#                 'padding': '20px',
#                 'color': '#059669',
#                 'fontWeight': 'bold',
#                 'backgroundColor': '#ecfdf5',
#                 'borderRadius': '8px'
#             })

#         columns_config = [
#             {'column': 'codigo', 'title': 'Código', 'align': 'left'},
#             {'column': 'descripcion', 'title': 'Producto', 'align': 'left'},
#             {'column': 'razon', 'title': 'Proveedor', 'align': 'left'},
#             {'column': 'stock', 'title': 'Stock', 'align': 'right', 'format': 'number',
#              'highlight': True, 'highlight_threshold': 10},
#             {'column': 'ventas_netas', 'title': 'Ventas',
#                 'align': 'right', 'format': 'number'},
#             {'column': 'rotacion_inventario', 'title': 'Rotación',
#                 'align': 'right', 'format': 'decimal'},
#             {'column': 'dias_inventario', 'title': 'Días Inv.',
#                 'align': 'right', 'format': 'number'},
#             {'column': 'costo_ultimo', 'title': 'Costo Unit.',
#                 'align': 'right', 'format': 'currency'}
#         ]

#         return create_data_table(data, columns_config, theme, max_rows=15)

#     except Exception as e:
#         print(f"❌ Error actualizando tabla críticos: {e}")
#         return html.Div("Error cargando datos", style={'textAlign': 'center', 'color': '#dc2626'})


# @callback(
#     Output('proveedores-compras-tabla-oportunidades', 'children'),
#     [Input('proveedores-compras-dropdown-laboratorio', 'value'),
#      Input('proveedores-compras-dropdown-periodo', 'value'),
#      Input('proveedores-compras-data-store', 'data'),
#      Input('proveedores-compras-theme-store', 'data')]
# )
# def update_tabla_oportunidades(laboratorio, periodo, data_store, theme):
#     """Actualizar tabla de oportunidades de compra"""
#     try:
#         if not analyzer:
#             return html.Div("Analyzer no disponible", style={
#                 'textAlign': 'center', 'color': '#dc2626', 'padding': '20px'
#             })

#         data = analyzer.get_oportunidades_compra(
#             laboratorio or 'Todos', periodo or 'Todos', top_n=12)

#         if data.empty:
#             return html.Div("No se encontraron oportunidades de compra", style={
#                 'textAlign': 'center',
#                 'padding': '20px',
#                 'color': '#6b7280',
#                 'fontStyle': 'italic'
#             })

#         columns_config = [
#             {'column': 'codigo', 'title': 'Código', 'align': 'left'},
#             {'column': 'descripcion', 'title': 'Producto', 'align': 'left'},
#             {'column': 'stock', 'title': 'Stock',
#                 'align': 'right', 'format': 'number'},
#             {'column': 'ventas_netas', 'title': 'Ventas',
#                 'align': 'right', 'format': 'number'},
#             {'column': 'rotacion_inventario', 'title': 'Rotación',
#                 'align': 'right', 'format': 'decimal'},
#             {'column': 'dias_inventario', 'title': 'Días',
#                 'align': 'right', 'format': 'number'},
#             {'column': 'costo_ultimo', 'title': 'Costo',
#                 'align': 'right', 'format': 'currency'}
#         ]

#         return create_data_table(data, columns_config, theme, max_rows=12)

#     except Exception as e:
#         print(f"❌ Error actualizando tabla oportunidades: {e}")
#         return html.Div("Error cargando datos", style={'textAlign': 'center', 'color': '#dc2626'})


# @callback(
#     Output('proveedores-compras-tabla-sin-rotacion', 'children'),
#     [Input('proveedores-compras-dropdown-laboratorio', 'value'),
#      Input('proveedores-compras-dropdown-periodo', 'value'),
#      Input('proveedores-compras-data-store', 'data'),
#      Input('proveedores-compras-theme-store', 'data')]
# )
# def update_tabla_sin_rotacion(laboratorio, periodo, data_store, theme):
#     """Actualizar tabla de productos sin rotación"""
#     try:
#         if not analyzer:
#             return html.Div("Analyzer no disponible", style={
#                 'textAlign': 'center', 'color': '#dc2626', 'padding': '20px'
#             })

#         data = analyzer.get_productos_sin_rotacion(
#             laboratorio or 'Todos', periodo or 'Todos', top_n=12)

#         if data.empty:
#             return html.Div("✅ No hay inventario sin rotación", style={
#                 'textAlign': 'center',
#                 'padding': '20px',
#                 'color': '#059669',
#                 'fontWeight': 'bold',
#                 'backgroundColor': '#ecfdf5',
#                 'borderRadius': '8px'
#             })

#         columns_config = [
#             {'column': 'codigo', 'title': 'Código', 'align': 'left'},
#             {'column': 'descripcion', 'title': 'Producto', 'align': 'left'},
#             {'column': 'stock', 'title': 'Stock',
#                 'align': 'right', 'format': 'number'},
#             {'column': 'costo_stock', 'title': 'Valor Stock',
#                 'align': 'right', 'format': 'currency'},
#             {'column': 'costo_ultimo', 'title': 'Costo Unit.',
#                 'align': 'right', 'format': 'currency'}
#         ]

#         return create_data_table(data, columns_config, theme, max_rows=12)

#     except Exception as e:
#         print(f"❌ Error actualizando tabla sin rotación: {e}")
#         return html.Div("Error cargando datos", style={'textAlign': 'center', 'color': '#dc2626'})


# # ==================== CALLBACKS DE GRÁFICOS ====================

# @callback(
#     Output('proveedores-compras-grafico-rotacion', 'figure'),
#     [Input('proveedores-compras-dropdown-laboratorio', 'value'),
#      Input('proveedores-compras-dropdown-periodo', 'value'),
#      Input('proveedores-compras-data-store', 'data'),
#      Input('proveedores-compras-theme-store', 'data')]
# )
# def update_grafico_rotacion(laboratorio, periodo, data_store, theme):
#     """Actualizar gráfico de análisis de rotación"""
#     try:
#         if not analyzer:
#             return create_empty_figure("Analyzer no disponible", theme)

#         data = analyzer.get_analisis_rotacion(
#             laboratorio or 'Todos', periodo or 'Todos')
#         theme_styles = get_theme_styles(theme)

#         if data.empty:
#             return create_empty_figure("No hay datos de rotación disponibles", theme)

#         # Colores para cada categoría
#         colors = {
#             'Alta': '#059669',      # Verde
#             'Media': '#d97706',     # Naranja
#             'Baja': '#dc2626',      # Rojo
#             'Muy Baja': '#7c2d12'   # Rojo oscuro
#         }

#         fig = go.Figure()

#         for _, row in data.iterrows():
#             fig.add_trace(go.Bar(
#                 x=[row['categoria']],
#                 y=[row['num_productos']],
#                 name=row['categoria'],
#                 marker_color=colors.get(row['categoria'], '#6b7280'),
#                 text=[f"{row['num_productos']} productos"],
#                 textposition='outside',
#                 hovertemplate=(
#                     f"<b>{row['categoria']}</b><br>"
#                     f"Productos: {row['num_productos']}<br>"
#                     f"Valor Inventario: {format_currency_int(row['valor_inventario'])}<br>"
#                     f"Rotación Promedio: {row['rotacion_promedio']:.2f}x<br>"
#                     "<extra></extra>"
#                 ),
#                 showlegend=False
#             ))

#         fig.update_layout(
#             title="Distribución por Categoría de Rotación",
#             height=400,
#             plot_bgcolor=theme_styles['plot_bg'],
#             paper_bgcolor=theme_styles['plot_bg'],
#             font=dict(family="Inter", size=12,
#                       color=theme_styles['text_color']),
#             xaxis=dict(
#                 title="Categoría de Rotación",
#                 showgrid=False,
#                 linecolor=theme_styles['line_color']
#             ),
#             yaxis=dict(
#                 title="Número de Productos",
#                 showgrid=True,
#                 gridcolor=theme_styles['grid_color'],
#                 linecolor=theme_styles['line_color']
#             ),
#             margin=dict(t=60, b=60, l=60, r=20)
#         )

#         return fig

#     except Exception as e:
#         print(f"❌ Error en gráfico de rotación: {e}")
#         return create_empty_figure("Error cargando datos", theme)


# @callback(
#     Output('proveedores-compras-grafico-dias-inventario', 'figure'),
#     [Input('proveedores-compras-dropdown-laboratorio', 'value'),
#      Input('proveedores-compras-dropdown-periodo', 'value'),
#      Input('proveedores-compras-data-store', 'data'),
#      Input('proveedores-compras-theme-store', 'data')]
# )
# def update_grafico_dias_inventario(laboratorio, periodo, data_store, theme):
#     """Actualizar gráfico de días de inventario"""
#     try:
#         if not analyzer:
#             return create_empty_figure("Analyzer no disponible", theme)

#         df = analyzer.filter_data(laboratorio or 'Todos', periodo or 'Todos')
#         theme_styles = get_theme_styles(theme)

#         if df.empty:
#             return create_empty_figure("No hay datos disponibles", theme)

#         # Filtrar datos válidos
#         df_valid = df[df['dias_inventario'] < 365].copy()

#         if df_valid.empty:
#             return create_empty_figure("No hay datos válidos de días de inventario", theme)

#         # Crear histograma
#         fig = go.Figure()

#         fig.add_trace(go.Histogram(
#             x=df_valid['dias_inventario'],
#             nbinsx=20,
#             marker_color='rgba(59, 130, 246, 0.7)',
#             marker_line_color='rgba(59, 130, 246, 1.0)',
#             marker_line_width=1,
#             name='Distribución'
#         ))

#         # Añadir líneas de referencia
#         promedio = df_valid['dias_inventario'].mean()
#         fig.add_vline(x=promedio, line_dash="dash", line_color="red",
#                       annotation_text=f"Promedio: {promedio:.0f} días")

#         fig.update_layout(
#             title="Distribución de Días de Inventario",
#             height=400,
#             plot_bgcolor=theme_styles['plot_bg'],
#             paper_bgcolor=theme_styles['plot_bg'],
#             font=dict(family="Inter", size=12,
#                       color=theme_styles['text_color']),
#             xaxis=dict(
#                 title="Días de Inventario",
#                 showgrid=True,
#                 gridcolor=theme_styles['grid_color'],
#                 linecolor=theme_styles['line_color']
#             ),
#             yaxis=dict(
#                 title="Número de Productos",
#                 showgrid=True,
#                 gridcolor=theme_styles['grid_color'],
#                 linecolor=theme_styles['line_color']
#             ),
#             showlegend=False,
#             margin=dict(t=60, b=60, l=60, r=20)
#         )

#         return fig

#     except Exception as e:
#         print(f"❌ Error en gráfico de días inventario: {e}")
#         return create_empty_figure("Error cargando datos", theme)


# @callback(
#     Output('proveedores-compras-top-proveedores', 'figure'),
#     [Input('proveedores-compras-dropdown-laboratorio', 'value'),
#      Input('proveedores-compras-dropdown-periodo', 'value'),
#      Input('proveedores-compras-data-store', 'data'),
#      Input('proveedores-compras-theme-store', 'data')]
# )
# def update_top_proveedores(laboratorio, periodo, data_store, theme):
#     """Actualizar top proveedores"""
#     try:
#         if not analyzer:
#             return create_empty_figure("Analyzer no disponible", theme)

#         data = analyzer.get_top_proveedores(
#             'Todos', periodo or 'Todos', top_n=10)
#         theme_styles = get_theme_styles(theme)

#         if data.empty:
#             return create_empty_figure("No hay datos de proveedores disponibles", theme)

#         # Ordenar de menor a mayor para gráfico horizontal
#         data_sorted = data.sort_values('valor_compras', ascending=True)

#         fig = go.Figure()

#         fig.add_trace(go.Bar(
#             x=data_sorted['valor_compras'],
#             y=[proveedor[:30] + "..." if len(proveedor) > 30 else proveedor
#                for proveedor in data_sorted['proveedor']],
#             orientation='h',
#             marker=dict(
#                 color='rgba(16, 185, 129, 0.6)',
#                 line=dict(color='rgba(16, 185, 129, 0.9)', width=1)
#             ),
#             text=[format_currency_int(val)
#                   for val in data_sorted['valor_compras']],
#             textposition='inside',
#             textfont=dict(color='white', size=10),
#             hovertemplate="<b>%{y}</b><br>Compras: %{text}<br>Productos: %{customdata}<extra></extra>",
#             customdata=data_sorted['num_productos']
#         ))

#         fig.update_layout(
#             height=400,
#             plot_bgcolor=theme_styles['plot_bg'],
#             paper_bgcolor=theme_styles['plot_bg'],
#             font=dict(family="Inter", size=12,
#                       color=theme_styles['text_color']),
#             xaxis=dict(
#                 tickformat='$,.0f',
#                 showgrid=True,
#                 gridcolor=theme_styles['grid_color'],
#                 title="Valor Compras",
#                 linecolor=theme_styles['line_color']
#             ),
#             yaxis=dict(
#                 title="Proveedor",
#                 tickfont=dict(size=10),
#                 linecolor=theme_styles['line_color']
#             ),
#             margin=dict(t=20, b=40, l=150, r=80),
#             showlegend=False
#         )

#         return fig

#     except Exception as e:
#         print(f"❌ Error en top proveedores: {e}")
#         return create_empty_figure("Error cargando datos", theme)


# @callback(
#     Output('proveedores-compras-comparacion-labs', 'figure'),
#     [Input('proveedores-compras-dropdown-periodo', 'value'),
#      Input('proveedores-compras-data-store', 'data'),
#      Input('proveedores-compras-theme-store', 'data')]
# )
# def update_comparacion_labs(periodo, data_store, theme):
#     """Actualizar comparación entre laboratorios"""
#     try:
#         if not analyzer:
#             return create_empty_figure("Analyzer no disponible", theme)

#         data = analyzer.get_comparacion_laboratorios(periodo or 'Todos')
#         theme_styles = get_theme_styles(theme)

#         if data.empty:
#             return create_empty_figure("No hay datos para comparar laboratorios", theme)

#         # Crear gráfico de burbujas
#         fig = go.Figure()

#         # Normalizar tamaño de burbujas
#         size_values = data['valor_inventario']
#         max_size = size_values.max()
#         min_size = size_values.min()

#         # Escalar tamaños entre 20 y 80
#         if max_size != min_size:
#             normalized_sizes = ((size_values - min_size) /
#                                 (max_size - min_size) * 60) + 20
#         else:
#             normalized_sizes = [40] * len(size_values)

#         fig.add_trace(go.Scatter(
#             x=data['rotacion_promedio'],
#             y=data['eficiencia_inventario'],
#             mode='markers',
#             marker=dict(
#                 size=normalized_sizes,
#                 color=data['valor_compras'],
#                 colorscale='Viridis',
#                 opacity=0.7,
#                 line=dict(width=2, color='white'),
#                 colorbar=dict(title="Valor Compras")
#             ),
#             hovertemplate=(
#                 "<b>%{text}</b><br>"
#                 "Rotación: %{x:.2f}x<br>"
#                 "Eficiencia: %{y:.2f}<br>"
#                 "Valor Compras: %{customdata}<br>"
#                 "<extra></extra>"
#             ),
#             customdata=[format_currency_int(val)
#                         for val in data['valor_compras']]
#         ))

#         fig.update_layout(
#             title="Análisis Comparativo: Rotación vs Eficiencia de Inventario",
#             height=400,
#             plot_bgcolor=theme_styles['plot_bg'],
#             paper_bgcolor=theme_styles['plot_bg'],
#             font=dict(family="Inter", size=12,
#                       color=theme_styles['text_color']),
#             xaxis=dict(
#                 title="Rotación Promedio (veces)",
#                 showgrid=True,
#                 gridcolor=theme_styles['grid_color'],
#                 linecolor=theme_styles['line_color']
#             ),
#             yaxis=dict(
#                 title="Eficiencia de Inventario",
#                 showgrid=True,
#                 gridcolor=theme_styles['grid_color'],
#                 linecolor=theme_styles['line_color']
#             ),
#             showlegend=False,
#             margin=dict(t=60, b=60, l=80, r=120)
#         )

#         return fig

#     except Exception as e:
#         print(f"❌ Error en comparación laboratorios: {e}")
#         return create_empty_figure("Error cargando datos", theme)


# @callback(
#     Output('proveedores-compras-matriz-gestion', 'figure'),
#     [Input('proveedores-compras-dropdown-laboratorio', 'value'),
#      Input('proveedores-compras-dropdown-periodo', 'value'),
#      Input('proveedores-compras-data-store', 'data'),
#      Input('proveedores-compras-theme-store', 'data')]
# )
# def update_matriz_gestion(laboratorio, periodo, data_store, theme):
#     """Actualizar matriz de gestión de inventarios"""
#     try:
#         if not analyzer:
#             return create_empty_figure("Analyzer no disponible", theme)

#         df = analyzer.filter_data(laboratorio or 'Todos', periodo or 'Todos')
#         theme_styles = get_theme_styles(theme)

#         if df.empty:
#             return create_empty_figure("No hay datos para la matriz de gestión", theme)

#         # Filtrar datos válidos
#         df_valid = df[
#             (df['costo_stock'] > 0) &
#             (df['rotacion_inventario'] >= 0) &
#             (df['rotacion_inventario'] < 50)  # Filtrar valores extremos
#         ].copy()

#         if df_valid.empty:
#             return create_empty_figure("No hay datos válidos para la matriz", theme)

#         # Crear categorías para colores
#         def get_categoria_estrategica(row):
#             rotacion = row['rotacion_inventario']
#             valor = row['costo_stock']

#             if rotacion > 3 and valor > df_valid['costo_stock'].median():
#                 return 'Estrella'  # Alta rotación, alto valor
#             elif rotacion > 3 and valor <= df_valid['costo_stock'].median():
#                 return 'Oportunidad'  # Alta rotación, bajo valor
#             elif rotacion <= 1 and valor > df_valid['costo_stock'].median():
#                 return 'Problema'  # Baja rotación, alto valor
#             else:
#                 return 'Revisar'  # Baja rotación, bajo valor

#         df_valid['categoria_estrategica'] = df_valid.apply(
#             get_categoria_estrategica, axis=1)

#         # Colores para cada categoría
#         color_map = {
#             'Estrella': '#059669',    # Verde - mantener
#             'Oportunidad': '#3b82f6',  # Azul - incrementar
#             'Problema': '#dc2626',    # Rojo - reducir/liquidar
#             'Revisar': '#f59e0b'      # Amarillo - analizar
#         }

#         fig = go.Figure()

#         for categoria in df_valid['categoria_estrategica'].unique():
#             data_cat = df_valid[df_valid['categoria_estrategica'] == categoria]

#             # Calcular tamaño de puntos basado en stock
#             sizes = data_cat['stock'].apply(lambda x: min(max(x/10, 5), 50))

#             fig.add_trace(go.Scatter(
#                 x=data_cat['rotacion_inventario'],
#                 y=data_cat['costo_stock'],
#                 mode='markers',
#                 name=categoria,
#                 marker=dict(
#                     color=color_map[categoria],
#                     size=sizes,
#                     opacity=0.7,
#                     line=dict(width=1, color='white')
#                 ),
#                 hovertemplate=(
#                     "<b>%{customdata[0]}</b><br>"
#                     "Rotación: %{x:.2f}x<br>"
#                     "Valor Stock: %{customdata[1]}<br>"
#                     "Stock: %{customdata[2]} unidades<br>"
#                     "Categoría: " + categoria + "<br>"
#                     "<extra></extra>"
#                 ),
#                 customdata=[
#                     [desc[:50] + "..." if len(desc) > 50 else desc,
#                      format_currency_int(valor),
#                      f"{stock:,.0f}"]
#                     for desc, valor, stock in zip(
#                         data_cat['descripcion'],
#                         data_cat['costo_stock'],
#                         data_cat['stock']
#                     )
#                 ]
#             ))

#         # Añadir líneas de referencia
#         mediana_rotacion = df_valid['rotacion_inventario'].median()
#         mediana_valor = df_valid['costo_stock'].median()

#         fig.add_hline(y=mediana_valor, line_dash="dash",
#                       line_color="gray", opacity=0.5)
#         fig.add_vline(x=mediana_rotacion, line_dash="dash",
#                       line_color="gray", opacity=0.5)

#         # Añadir anotaciones de cuadrantes
#         max_x = df_valid['rotacion_inventario'].max()
#         max_y = df_valid['costo_stock'].max()

#         fig.add_annotation(
#             x=mediana_rotacion + (max_x - mediana_rotacion) * 0.5,
#             y=mediana_valor + (max_y - mediana_valor) * 0.5,
#             text="ESTRELLA<br>(Mantener)", showarrow=False,
#             font=dict(size=10, color='#059669'),
#             bgcolor="rgba(5,150,105,0.1)",
#             bordercolor="#059669"
#         )
#         fig.add_annotation(
#             x=mediana_rotacion * 0.5,
#             y=mediana_valor + (max_y - mediana_valor) * 0.5,
#             text="PROBLEMA<br>(Reducir)", showarrow=False,
#             font=dict(size=10, color='#dc2626'),
#             bgcolor="rgba(220,38,38,0.1)",
#             bordercolor="#dc2626"
#         )

#         fig.update_layout(
#             height=500,
#             plot_bgcolor=theme_styles['plot_bg'],
#             paper_bgcolor=theme_styles['plot_bg'],
#             font=dict(family="Inter", size=12,
#                       color=theme_styles['text_color']),
#             xaxis=dict(
#                 title="Rotación de Inventario (veces)",
#                 showgrid=True,
#                 gridcolor=theme_styles['grid_color'],
#                 linecolor=theme_styles['line_color']
#             ),
#             yaxis=dict(
#                 title="Valor del Inventario ($)",
#                 showgrid=True,
#                 gridcolor=theme_styles['grid_color'],
#                 linecolor=theme_styles['line_color'],
#                 type='log'  # Escala logarítmica para mejor visualización
#             ),
#             legend=dict(
#                 orientation="h",
#                 yanchor="bottom",
#                 y=1.02,
#                 xanchor="right",
#                 x=1
#             ),
#             margin=dict(t=80, b=60, l=80, r=20)
#         )

#         return fig

#     except Exception as e:
#         print(f"❌ Error en matriz de gestión: {e}")
#         return create_empty_figure("Error cargando datos", theme)


# @callback(
#     [Output('proveedores-compras-modelo-status', 'children'),
#      Output('proveedores-compras-data-store', 'data', allow_duplicate=True)],
#     [Input('proveedores-compras-btn-entrenar-modelo', 'n_clicks')],
#     [State('proveedores-compras-data-store', 'data')],
#     prevent_initial_call=True
# )
# def entrenar_modelo_ia(n_clicks, data_store):
#     """Entrenar modelo de IA"""
#     if n_clicks > 0:
#         if not analyzer:
#             return [html.Div("❌ Analyzer no disponible", style={'color': '#dc2626'})], dash.no_update

#         try:
#             # Mostrar loading
#             loading_msg = html.Div([
#                 html.Span("🔄 ", style={'marginRight': '8px'}),
#                 html.Span(
#                     "Entrenando modelo IA... Esto puede tomar unos segundos")
#             ], style={
#                 'color': '#667eea',
#                 'fontWeight': 'bold',
#                 'padding': '10px',
#                 'backgroundColor': 'rgba(102, 126, 234, 0.1)',
#                 'borderRadius': '8px',
#                 'border': '1px solid rgba(102, 126, 234, 0.3)'
#             })

#             metrics = analyzer.train_prediction_model()

#             if metrics:
#                 success_msg = html.Div([
#                     html.Span("✅ ", style={'marginRight': '8px'}),
#                     html.Span(f"Modelo entrenado exitosamente!"),
#                     html.Br(),
#                     html.Small(f"Productos analizados: {metrics['total_productos']}",
#                                style={'fontSize': '11px', 'opacity': '0.8'})
#                 ], style={
#                     'color': '#059669',
#                     'fontWeight': 'bold',
#                     'padding': '10px',
#                     'backgroundColor': '#ecfdf5',
#                     'borderRadius': '8px',
#                     'border': '1px solid #a7f3d0'
#                 })

#                 # Actualizar data store para trigger otros callbacks
#                 new_data_store = data_store.copy() if data_store else {}
#                 new_data_store['model_trained'] = n_clicks

#                 return success_msg, new_data_store
#             else:
#                 error_msg = html.Div([
#                     html.Span("❌ ", style={'marginRight': '8px'}),
#                     html.Span("Error entrenando modelo")
#                 ], style={'color': '#dc2626'})
#                 return error_msg, dash.no_update

#         except Exception as e:
#             error_msg = html.Div([
#                 html.Span("❌ ", style={'marginRight': '8px'}),
#                 html.Span(f"Error: {str(e)}")
#             ], style={'color': '#dc2626'})
#             return error_msg, dash.no_update

#     return dash.no_update, dash.no_update


# @callback(
#     Output('proveedores-compras-prediccion-metrics', 'children'),
#     [Input('proveedores-compras-dropdown-laboratorio', 'value'),
#      Input('proveedores-compras-data-store', 'data'),
#      Input('proveedores-compras-theme-store', 'data')]
# )
# def update_prediccion_metrics(laboratorio, data_store, theme):
#     """Actualizar métricas de predicciones"""
#     try:
#         if not analyzer or not analyzer.model_trained:
#             return html.Div("🤖 Entrena el modelo IA para ver predicciones", style={
#                 'textAlign': 'center', 'color': '#6b7280', 'fontStyle': 'italic', 'padding': '20px'
#             })

#         resumen = analyzer.get_resumen_predicciones(laboratorio or 'Todos')
#         is_dark = theme == 'dark'

#         metrics_data = [
#             {
#                 'title': 'Productos Analizados',
#                 'value': f"{resumen['total_productos']:,}",
#                 'icon': '🤖',
#                 'color': '#667eea'
#             },
#             {
#                 'title': 'Alta Urgencia',
#                 'value': f"{resumen['productos_alta_urgencia']:,}",
#                 'icon': '🚨',
#                 'color': '#dc2626'
#             },
#             {
#                 'title': 'Valor Compras Sugerido',
#                 'value': format_currency_int(resumen['valor_total_compras']),
#                 'icon': '💰',
#                 'color': '#059669'
#             },
#             {
#                 'title': 'Demanda Predicha 30d',
#                 'value': f"{resumen['demanda_total_predicha']:,.0f}",
#                 'icon': '📈',
#                 'color': '#f59e0b'
#             }
#         ]

#         return create_metrics_grid(
#             metrics=metrics_data,
#             is_dark=is_dark,
#             columns=4,
#             gap="15px"
#         )

#     except Exception as e:
#         return html.Div(f"Error: {e}", style={'color': '#dc2626', 'textAlign': 'center'})


# @callback(
#     Output('proveedores-compras-tabla-predicciones', 'children'),
#     [Input('proveedores-compras-dropdown-laboratorio', 'value'),
#      Input('proveedores-compras-data-store', 'data'),
#      Input('proveedores-compras-theme-store', 'data')]
# )
# def update_tabla_predicciones(laboratorio, data_store, theme):
#     """Actualizar tabla de predicciones"""
#     try:
#         if not analyzer or not analyzer.model_trained:
#             return html.Div("🤖 Entrena el modelo IA primero", style={
#                 'textAlign': 'center', 'color': '#6b7280', 'padding': '20px'
#             })

#         predicciones = analyzer.get_predicciones_compras(
#             laboratorio or 'Todos', top_n=20)

#         if predicciones.empty:
#             return html.Div("No hay predicciones disponibles", style={
#                 'textAlign': 'center', 'color': '#6b7280', 'fontStyle': 'italic'
#             })

#         # Filtrar solo productos con recomendación de compra
#         predicciones_compra = predicciones[predicciones['cantidad_recomendada'] > 0]

#         columns_config = [
#             {'column': 'codigo', 'title': 'Código', 'align': 'left'},
#             {'column': 'descripcion', 'title': 'Producto', 'align': 'left'},
#             {'column': 'urgencia', 'title': 'Urgencia', 'align': 'center'},
#             {'column': 'stock_actual', 'title': 'Stock',
#                 'align': 'right', 'format': 'number'},
#             {'column': 'demanda_predicha_30d', 'title': 'Demanda 30d',
#                 'align': 'right', 'format': 'number'},
#             {'column': 'cantidad_recomendada', 'title': 'Cant. Sugerida',
#                 'align': 'right', 'format': 'number'},
#             {'column': 'valor_compra_sugerido', 'title': 'Valor Compra',
#                 'align': 'right', 'format': 'currency'},
#             {'column': 'costo_unitario', 'title': 'Costo Unit.',
#                 'align': 'right', 'format': 'currency'}
#         ]

#         return create_data_table(predicciones_compra, columns_config, theme, max_rows=20)

#     except Exception as e:
#         return html.Div(f"Error: {e}", style={'color': '#dc2626', 'textAlign': 'center'})


# @callback(
#     Output('proveedores-compras-grafico-urgencia-pred', 'figure'),
#     [Input('proveedores-compras-dropdown-laboratorio', 'value'),
#      Input('proveedores-compras-data-store', 'data'),
#      Input('proveedores-compras-theme-store', 'data')]
# )
# def update_grafico_urgencia_predicciones(laboratorio, data_store, theme):
#     """Gráfico de análisis de urgencia de predicciones"""
#     try:
#         if not analyzer or not analyzer.model_trained:
#             return create_empty_figure("🤖 Entrena el modelo IA para ver predicciones", theme)

#         data = analyzer.get_analisis_urgencia_predicciones(
#             laboratorio or 'Todos')
#         theme_styles = get_theme_styles(theme)

#         if data.empty:
#             return create_empty_figure("No hay datos de predicciones", theme)

#         # Colores por urgencia
#         colors = {
#             'Alta': '#dc2626',     # Rojo
#             'Media': '#f59e0b',    # Amarillo
#             'Baja': '#059669'      # Verde
#         }

#         fig = go.Figure()

#         # Gráfico de barras apiladas
#         fig.add_trace(go.Bar(
#             x=data['urgencia'],
#             y=data['num_productos'],
#             name='Número de Productos',
#             marker=dict(
#                 color=[colors.get(urgencia, '#6b7280')
#                        for urgencia in data['urgencia']],
#                 opacity=0.8
#             ),
#             text=[f"{num} productos<br>{format_currency_int(valor)}"
#                   for num, valor in zip(data['num_productos'], data['valor_compras_sugerido'])],
#             textposition='inside',
#             hovertemplate=(
#                 "<b>Urgencia: %{x}</b><br>"
#                 "Productos: %{y}<br>"
#                 "Valor sugerido: %{customdata}<br>"
#                 "<extra></extra>"
#             ),
#             customdata=[format_currency_int(val)
#                         for val in data['valor_compras_sugerido']]
#         ))

#         fig.update_layout(
#             title="Distribución por Urgencia de Reabastecimiento",
#             height=400,
#             plot_bgcolor=theme_styles['plot_bg'],
#             paper_bgcolor=theme_styles['plot_bg'],
#             font=dict(family="Inter", size=12,
#                       color=theme_styles['text_color']),
#             xaxis=dict(
#                 title="Nivel de Urgencia",
#                 showgrid=False,
#                 linecolor=theme_styles['line_color']
#             ),
#             yaxis=dict(
#                 title="Número de Productos",
#                 showgrid=True,
#                 gridcolor=theme_styles['grid_color'],
#                 linecolor=theme_styles['line_color']
#             ),
#             showlegend=False,
#             margin=dict(t=60, b=60, l=60, r=20)
#         )

#         return fig

#     except Exception as e:
#         return create_empty_figure("Error cargando predicciones", theme)


# @callback(
#     Output('proveedores-compras-grafico-proveedores-pred', 'figure'),
#     [Input('proveedores-compras-dropdown-laboratorio', 'value'),
#      Input('proveedores-compras-data-store', 'data'),
#      Input('proveedores-compras-theme-store', 'data')]
# )
# def update_grafico_proveedores_predicciones(laboratorio, data_store, theme):
#     """Gráfico de compras sugeridas por proveedor"""
#     try:
#         if not analyzer or not analyzer.model_trained:
#             return create_empty_figure("🤖 Entrena el modelo IA para ver predicciones", theme)

#         data = analyzer.get_predicciones_por_proveedor(
#             laboratorio or 'Todos', top_n=10)
#         theme_styles = get_theme_styles(theme)

#         if data.empty:
#             return create_empty_figure("No hay datos de predicciones por proveedor", theme)

#         # Ordenar para gráfico horizontal
#         data_sorted = data.sort_values('valor_total_compras', ascending=True)

#         fig = go.Figure()

#         # Crear colores basados en productos urgentes
#         max_urgentes = data_sorted['productos_urgentes'].max()
#         colors = []
#         for urgentes in data_sorted['productos_urgentes']:
#             if max_urgentes > 0:
#                 intensity = urgentes / max_urgentes
#                 # Gradiente de azul a rojo según urgencia
#                 r = int(220 * intensity + 59 * (1 - intensity))
#                 g = int(38 * intensity + 130 * (1 - intensity))
#                 b = int(38 * intensity + 246 * (1 - intensity))
#                 colors.append(f'rgba({r}, {g}, {b}, 0.7)')
#             else:
#                 colors.append('rgba(59, 130, 246, 0.7)')

#         fig.add_trace(go.Bar(
#             x=data_sorted['valor_total_compras'],
#             y=[prov[:25] + "..." if len(prov) > 25 else prov
#                for prov in data_sorted['proveedor']],
#             orientation='h',
#             marker=dict(
#                 color=colors,
#                 line=dict(color='rgba(255, 255, 255, 0.8)', width=1)
#             ),
#             text=[
#                 f"{format_currency_int(val)}" for val in data_sorted['valor_total_compras']],
#             textposition='inside',
#             textfont=dict(color='white', size=9),
#             hovertemplate=(
#                 "<b>%{y}</b><br>"
#                 "Valor sugerido: %{text}<br>"
#                 "Productos: %{customdata[0]}<br>"
#                 "Productos urgentes: %{customdata[1]}<br>"
#                 "<extra></extra>"
#             ),
#             customdata=[[productos, urgentes] for productos, urgentes in
#                         zip(data_sorted['num_productos'], data_sorted['productos_urgentes'])]
#         ))

#         fig.update_layout(
#             height=400,
#             plot_bgcolor=theme_styles['plot_bg'],
#             paper_bgcolor=theme_styles['plot_bg'],
#             font=dict(family="Inter", size=12,
#                       color=theme_styles['text_color']),
#             xaxis=dict(
#                 tickformat='$,.0f',
#                 showgrid=True,
#                 gridcolor=theme_styles['grid_color'],
#                 title="Valor Sugerido Compras",
#                 linecolor=theme_styles['line_color']
#             ),
#             yaxis=dict(
#                 title="Proveedor",
#                 tickfont=dict(size=10),
#                 linecolor=theme_styles['line_color']
#             ),
#             margin=dict(t=20, b=40, l=120, r=80),
#             showlegend=False
#         )

#         return fig

#     except Exception as e:
#         return create_empty_figure("Error cargando datos de proveedores", theme)


# # ================================
# # CALLBACK ADICIONAL PARA FEATURE IMPORTANCE
# # ================================

# @callback(
#     Output('proveedores-compras-feature-importance', 'figure'),
#     [Input('proveedores-compras-data-store', 'data'),
#      Input('proveedores-compras-theme-store', 'data')]
# )
# def update_feature_importance(data_store, theme):
#     """Gráfico de importancia de features del modelo"""
#     try:
#         if not analyzer or not analyzer.model_trained:
#             return create_empty_figure("🤖 Entrena el modelo IA primero", theme)

#         importance_data = analyzer.get_feature_importance_data()
#         theme_styles = get_theme_styles(theme)

#         if not importance_data:
#             return create_empty_figure("No hay datos de importancia de features", theme)

#         # Convertir a DataFrame y ordenar
#         df_importance = pd.DataFrame(list(importance_data.items()),
#                                      columns=['feature', 'importance'])
#         df_importance = df_importance.sort_values(
#             'importance', ascending=True).tail(8)

#         # Mapear nombres más legibles
#         feature_names = {
#             'rotacion_inventario': 'Rotación Inventario',
#             'stock': 'Stock Actual',
#             'ventas_netas': 'Ventas Netas',
#             'dias_inventario': 'Días Inventario',
#             'ratio_venta_compra': 'Ratio Venta/Compra',
#             'margen_unitario': 'Margen Unitario',
#             'costo_ultimo': 'Costo Unitario',
#             'costo_stock': 'Valor Stock',
#             'compras_netas': 'Compras Netas',
#             'ratio_devolucion': 'Ratio Devolución'
#         }

#         df_importance['feature_display'] = df_importance['feature'].map(
#             lambda x: feature_names.get(x, x.replace('_', ' ').title())
#         )

#         fig = go.Figure()

#         fig.add_trace(go.Bar(
#             x=df_importance['importance'],
#             y=df_importance['feature_display'],
#             orientation='h',
#             marker=dict(
#                 color='rgba(102, 126, 234, 0.7)',
#                 line=dict(color='rgba(102, 126, 234, 1.0)', width=1)
#             ),
#             text=[f"{imp:.3f}" for imp in df_importance['importance']],
#             textposition='inside',
#             textfont=dict(color='white', size=10),
#             hovertemplate="<b>%{y}</b><br>Importancia: %{x:.3f}<extra></extra>"
#         ))

#         fig.update_layout(
#             title="Importancia de Variables en el Modelo IA",
#             height=350,
#             plot_bgcolor=theme_styles['plot_bg'],
#             paper_bgcolor=theme_styles['plot_bg'],
#             font=dict(family="Inter", size=12,
#                       color=theme_styles['text_color']),
#             xaxis=dict(
#                 title="Importancia Relativa",
#                 showgrid=True,
#                 gridcolor=theme_styles['grid_color'],
#                 linecolor=theme_styles['line_color']
#             ),
#             yaxis=dict(
#                 title="Variable",
#                 tickfont=dict(size=10),
#                 linecolor=theme_styles['line_color']
#             ),
#             margin=dict(t=60, b=40, l=150, r=40),
#             showlegend=False
#         )

#         return fig

#     except Exception as e:
#         return create_empty_figure("Error cargando importancia de features", theme)

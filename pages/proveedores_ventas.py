import time
from datetime import datetime
import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from utils import (
    format_currency_int,
    get_theme_styles,
    get_dropdown_style,
    get_user_vendor_filter,
    can_see_all_vendors
)

# Colores azules en formato rgba
BLUE_COLORS_BG = [
    "rgba(0, 119, 182, 0.2)", "rgba(0, 180, 216, 0.2)", "rgba(144, 224, 239, 0.2)",
    "rgba(202, 240, 248, 0.2)", "rgba(2, 62, 138, 0.2)", "rgba(3, 4, 94, 0.2)",
    "rgba(0, 150, 199, 0.2)", "rgba(72, 202, 228, 0.2)", "rgba(173, 232, 244, 0.2)",
    "rgba(97, 165, 194, 0.2)", "rgba(1, 79, 134, 0.2)", "rgba(0, 126, 167, 0.2)",
    "rgba(5, 102, 141, 0.2)", "rgba(95, 168, 211, 0.2)", "rgba(137, 194, 217, 0.2)"
]

BLUE_COLORS_BORDER = [
    "rgba(0, 119, 182, 1)", "rgba(0, 180, 216, 1)", "rgba(144, 224, 239, 1)",
    "rgba(202, 240, 248, 1)", "rgba(2, 62, 138, 1)", "rgba(3, 4, 94, 1)",
    "rgba(0, 150, 199, 1)", "rgba(72, 202, 228, 1)", "rgba(173, 232, 244, 1)",
    "rgba(97, 165, 194, 1)", "rgba(1, 79, 134, 1)", "rgba(0, 126, 167, 1)",
    "rgba(5, 102, 141, 1)", "rgba(95, 168, 211, 1)", "rgba(137, 194, 217, 1)"
]

# Inicializar analyzers
try:
    from server import get_db
    from analyzers import ImpactosAnalyzer, VentasProveedoresAnalyzer

    db = get_db()
    analyzer_impactos = ImpactosAnalyzer(db)
    analyzer_ventas = VentasProveedoresAnalyzer(db)
except Exception as e:
    analyzer_impactos = None
    analyzer_ventas = None


def get_selected_vendor(session_data, dropdown_value):
    """Obtener vendedor según permisos"""
    try:
        if not session_data:
            return 'Todos'
        if can_see_all_vendors(session_data):
            return dropdown_value if dropdown_value else 'Todos'
        else:
            return get_user_vendor_filter(session_data)
    except:
        return 'Todos'


def create_empty_figure(message, theme):
    """Crear figura vacía"""
    theme_styles = get_theme_styles(theme)
    fig = go.Figure()
    fig.add_annotation(
        text=message, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=14, color=theme_styles['text_color'], family='Inter')
    )
    fig.update_layout(
        height=350,
        paper_bgcolor=theme_styles['plot_bg'],
        plot_bgcolor=theme_styles['plot_bg'],
        margin=dict(t=10, b=10, l=10, r=10),
        font=dict(family='Inter')
    )
    return fig


def create_analytical_panel(resumen: dict, is_dark: bool = False):
    """Panel analítico moderno"""
    bg_primary = 'rgba(31, 41, 55, 0.95)' if is_dark else 'rgba(255, 255, 255, 0.95)'
    bg_secondary = 'rgba(55, 65, 81, 0.9)' if is_dark else 'rgba(249, 250, 251, 0.9)'
    text_primary = '#f9fafb' if is_dark else '#111827'
    text_secondary = '#d1d5db' if is_dark else '#6b7280'
    border_color = 'rgba(75, 85, 99, 0.5)' if is_dark else 'rgba(229, 231, 235, 0.8)'

    total_ventas = resumen.get('total_ventas', 0)
    total_unidades = resumen.get('total_unidades', 0)
    total_utilidad = resumen.get('total_utilidad', 0)
    margen_promedio = resumen.get('margen_promedio', 0)
    num_facturas = resumen.get('num_facturas', 0)
    num_clientes = resumen.get('num_clientes', 0)
    num_productos = resumen.get('num_productos', 0)
    num_laboratorios = resumen.get('num_laboratorios', 0)

    ticket_promedio = (total_ventas / num_facturas) if num_facturas > 0 else 0
    promedio_cliente = (total_ventas / num_clientes) if num_clientes > 0 else 0

    return html.Div([
        html.Div([
            html.Div([
                html.Span("📊", style={'fontSize': '32px',
                          'marginRight': '12px'}),
                html.Div([
                    html.H3("Panel Analítico", style={
                        'margin': '0', 'fontSize': '24px', 'fontWeight': '700',
                        'color': text_primary, 'fontFamily': 'Inter'
                    }),
                    html.P("Resumen ejecutivo de ventas", style={
                        'margin': '4px 0 0 0', 'fontSize': '14px',
                        'color': text_secondary, 'fontFamily': 'Inter'
                    })
                ])
            ], style={'display': 'flex', 'alignItems': 'center'})
        ], style={'marginBottom': '24px', 'paddingBottom': '16px', 'borderBottom': f'2px solid {border_color}'}),

        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.Span(
                            "💰", style={'fontSize': '28px', 'marginBottom': '8px'}),
                        html.P("Ventas Totales", style={'margin': '0', 'fontSize': '13px', 'color': text_secondary,
                               'fontWeight': '600', 'textTransform': 'uppercase', 'fontFamily': 'Inter'}),
                        html.H2(format_currency_int(total_ventas), style={
                                'margin': '8px 0 0 0', 'fontSize': '32px', 'fontWeight': '800', 'color': '#10b981', 'fontFamily': 'Inter'}),
                        html.Div([html.Span(f"Ticket Prom: {format_currency_int(ticket_promedio)}", style={
                                 'fontSize': '11px', 'color': text_secondary, 'fontFamily': 'Inter'})], style={'marginTop': '8px'})
                    ], style={'padding': '20px', 'textAlign': 'center'})
                ], style={'background': bg_secondary, 'borderRadius': '12px', 'border': f'1px solid {border_color}', 'height': '100%', 'boxShadow': '0 2px 8px rgba(0,0,0,0.05)'})
            ], style={'flex': '1'}),

            html.Div([
                html.Div([
                    html.Div([
                        html.Span(
                            "💵", style={'fontSize': '28px', 'marginBottom': '8px'}),
                        html.P("Utilidad", style={'margin': '0', 'fontSize': '13px', 'color': text_secondary,
                               'fontWeight': '600', 'textTransform': 'uppercase', 'fontFamily': 'Inter'}),
                        html.H2(format_currency_int(total_utilidad), style={
                                'margin': '8px 0 0 0', 'fontSize': '32px', 'fontWeight': '800', 'color': '#3b82f6', 'fontFamily': 'Inter'}),
                        html.Div([
                            html.Span("Margen: ", style={
                                      'fontSize': '11px', 'color': text_secondary, 'fontFamily': 'Inter'}),
                            html.Span(f"{margen_promedio:.1f}%", style={
                                      'fontSize': '14px', 'fontWeight': 'bold', 'color': '#8b5cf6', 'fontFamily': 'Inter'})
                        ], style={'marginTop': '8px'})
                    ], style={'padding': '20px', 'textAlign': 'center'})
                ], style={'background': bg_secondary, 'borderRadius': '12px', 'border': f'1px solid {border_color}', 'height': '100%', 'boxShadow': '0 2px 8px rgba(0,0,0,0.05)'})
            ], style={'flex': '1'}),

            html.Div([
                html.Div([
                    html.Div([
                        html.Span(
                            "📦", style={'fontSize': '28px', 'marginBottom': '8px'}),
                        html.P("Unidades", style={'margin': '0', 'fontSize': '13px', 'color': text_secondary,
                               'fontWeight': '600', 'textTransform': 'uppercase', 'fontFamily': 'Inter'}),
                        html.H2(f"{total_unidades:,}", style={'margin': '8px 0 0 0', 'fontSize': '32px',
                                'fontWeight': '800', 'color': '#f59e0b', 'fontFamily': 'Inter'}),
                        html.Div([html.Span(f"Facturas: {num_facturas:,}", style={
                                 'fontSize': '11px', 'color': text_secondary, 'fontFamily': 'Inter'})], style={'marginTop': '8px'})
                    ], style={'padding': '20px', 'textAlign': 'center'})
                ], style={'background': bg_secondary, 'borderRadius': '12px', 'border': f'1px solid {border_color}', 'height': '100%', 'boxShadow': '0 2px 8px rgba(0,0,0,0.05)'})
            ], style={'flex': '1'})
        ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '16px'}),

        html.Div([
            _create_mini_metric("👥", "Clientes", f"{num_clientes:,}", format_currency_int(
                promedio_cliente) + " prom", bg_secondary, text_primary, text_secondary, border_color),
            _create_mini_metric("🏭", "Laboratorios", f"{num_laboratorios:,}",
                                f"{num_productos:,} productos", bg_secondary, text_primary, text_secondary, border_color),
            _create_mini_metric("🧪", "Productos", f"{num_productos:,}", "códigos únicos",
                                bg_secondary, text_primary, text_secondary, border_color),
            _create_mini_metric("📋", "Facturas", f"{num_facturas:,}", f"{(total_unidades/num_facturas if num_facturas > 0 else 0):.1f} und/fact",
                                bg_secondary, text_primary, text_secondary, border_color)
        ], style={'display': 'flex', 'gap': '12px'})

    ], style={
        'background': bg_primary, 'borderRadius': '16px', 'padding': '28px',
        'boxShadow': '0 4px 20px rgba(0,0,0,0.08)', 'border': f'1px solid {border_color}',
        'marginBottom': '24px'
    })


def _create_mini_metric(icon, label, value, subtitle, bg, text_primary, text_secondary, border_color):
    """Métrica mini"""
    return html.Div([
        html.Div([
            html.Span(icon, style={'fontSize': '20px', 'marginBottom': '6px'}),
            html.P(label, style={'margin': '0', 'fontSize': '11px',
                   'color': text_secondary, 'fontWeight': '600', 'fontFamily': 'Inter'}),
            html.H3(value, style={'margin': '4px 0', 'fontSize': '18px',
                    'fontWeight': '700', 'color': text_primary, 'fontFamily': 'Inter'}),
            html.P(subtitle, style={
                   'margin': '0', 'fontSize': '9px', 'color': text_secondary, 'fontFamily': 'Inter'})
        ], style={'padding': '14px', 'textAlign': 'center'})
    ], style={'flex': '1', 'background': bg, 'borderRadius': '10px', 'border': f'1px solid {border_color}', 'boxShadow': '0 2px 6px rgba(0,0,0,0.04)'})


# ==================== LAYOUT ====================

layout = html.Div([
    dcc.Store(id='prov-theme-store', data='light'),
    dcc.Store(id='prov-data-store', data={'last_update': 0}),

    html.Div(id='prov-notification', children=[], style={
        'position': 'fixed', 'top': '20px', 'right': '20px',
        'zIndex': '1000', 'maxWidth': '300px'
    }),

    html.Div([
        # Header
        html.Div([
            html.Div([html.Img(src='/assets/logo.png', className="top-left-logo", style={
                     'maxWidth': '160px', 'height': 'auto'})], className="logo-left-container"),
            html.Div([
                html.H1("Proveedores Ventas - Dashboard",
                        className="main-title", style={'fontFamily': 'Inter'}),
                html.P(id='prov-subtitle', className="main-subtitle",
                       children="Análisis de ventas por laboratorio", style={'fontFamily': 'Inter'})
            ], className="center-title-section"),
            html.Div([html.Button("🌙", id="prov-theme-toggle", n_clicks=0, style={'background': 'transparent', 'border': '2px solid rgba(255,255,255,0.3)',
                     'borderRadius': '50%', 'width': '44px', 'height': '44px', 'fontSize': '18px', 'cursor': 'pointer', 'fontFamily': 'Inter'})], className="logout-right-container")
        ], className="top-header", id='prov-header'),

        # Controls
        html.Div([
            html.Div([
                html.Label("Laboratorio:", style={
                           'fontWeight': '600', 'fontSize': '14px', 'marginBottom': '8px', 'fontFamily': 'Inter'}),
                dcc.Dropdown(id='prov-dd-lab', options=[], value='Todos',
                             clearable=False, style={'height': '44px', 'borderRadius': '12px', 'fontFamily': 'Inter'})
            ], style={'flex': '1', 'minWidth': '250px'}),
            html.Div([
                html.Label("Mes:", style={
                           'fontWeight': '600', 'fontSize': '14px', 'marginBottom': '8px', 'fontFamily': 'Inter'}),
                dcc.Dropdown(id='prov-dd-mes', options=[], value='Todos',
                             clearable=False, style={'height': '44px', 'borderRadius': '12px', 'fontFamily': 'Inter'})
            ], style={'flex': '1', 'minWidth': '200px'}),
            html.Div([
                html.Label("Vendedor:", style={
                           'fontWeight': '600', 'fontSize': '14px', 'marginBottom': '8px', 'fontFamily': 'Inter'}),
                dcc.Dropdown(id='prov-dd-vendedor', options=[], value='Todos',
                             clearable=False, style={'height': '44px', 'borderRadius': '12px', 'fontFamily': 'Inter'})
            ], style={'flex': '1', 'minWidth': '250px'}, id='prov-dd-vendedor-container'),
            html.Div([html.Button("🔄 Actualizar", id="prov-btn-reload", n_clicks=0, style={'background': 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)', 'color': '#fff', 'border': 'none',
                     'padding': '12px 20px', 'borderRadius': '25px', 'fontWeight': '600', 'cursor': 'pointer', 'height': '44px', 'fontFamily': 'Inter'})], style={'display': 'flex', 'alignItems': 'flex-end'})
        ], id='prov-controls', style={'display': 'flex', 'gap': '24px', 'borderRadius': '16px', 'padding': '24px', 'marginBottom': '24px', 'boxShadow': '0 8px 32px rgba(0,0,0,0.1)', 'flexWrap': 'wrap'}),

        # Ventas Section
        html.Div([
            html.Div(id="prov-panel", children=[]),

            html.Div([
                html.Div([html.H3("Evolución Ventas", style={'textAlign': 'center', 'marginBottom': '15px', 'fontFamily': 'Inter', 'fontSize': '18px'}), dcc.Graph(
                    id='prov-g-evol')], style={'width': '100%'})
            ], id='prov-row-evol', style={'borderRadius': '16px', 'padding': '24px', 'marginBottom': '24px', 'boxShadow': '0 8px 32px rgba(0,0,0,0.1)'}),

            html.Div([
                html.Div([html.H3("🏆 Top 10 Laboratorios", style={'textAlign': 'center', 'marginBottom': '15px', 'fontFamily': 'Inter', 'fontSize': '18px'}), dcc.Graph(
                    id='prov-g-labs')], style={'width': '48%', 'display': 'inline-block', 'marginRight': '2%'}),
                html.Div([html.H3("🏆 Top 10 Clientes", style={'textAlign': 'center', 'marginBottom': '15px', 'fontFamily': 'Inter', 'fontSize': '18px'}), dcc.Graph(
                    id='prov-g-clientes')], style={'width': '48%', 'display': 'inline-block', 'marginLeft': '2%'})
            ], id='prov-row-1', style={'borderRadius': '16px', 'padding': '24px', 'marginBottom': '24px', 'boxShadow': '0 8px 32px rgba(0,0,0,0.1)'}),

            html.Div([
                html.Div([html.H3("Evolución Impactos", style={'textAlign': 'center', 'marginBottom': '15px', 'fontFamily': 'Inter', 'fontSize': '18px'}), dcc.Graph(
                    id='prov-g-impactos')], style={'width': '100%'})
            ], id='prov-row-2', style={'borderRadius': '16px', 'padding': '24px', 'marginBottom': '24px', 'boxShadow': '0 8px 32px rgba(0,0,0,0.1)'}),

            html.Div([
                html.H3("Análisis por Molécula", style={
                        'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Inter', 'fontSize': '18px'}),
                html.Div([
                    html.Div([
                        html.Label("Periodo:", style={
                                   'fontWeight': 'bold', 'marginRight': '10px', 'fontFamily': 'Inter'}),
                        dcc.Dropdown(id='prov-dd-periodo', options=[{'label': 'Mensual', 'value': 'mensual'}, {'label': 'Trimestral', 'value': 'trimestral'}, {
                                     'label': 'Anual', 'value': 'anual'}], value='mensual', clearable=False, style={'width': '200px', 'fontFamily': 'Inter'})
                    ], style={'marginRight': '20px'}),
                    html.Div([
                        html.Label("Ordenar por:", style={
                                   'fontWeight': 'bold', 'marginRight': '10px', 'fontFamily': 'Inter'}),
                        dcc.Dropdown(id='prov-dd-sort', options=[
                            {'label': 'Valor Ventas ↓', 'value': 'valor_desc'},
                            {'label': 'Valor Ventas ↑', 'value': 'valor_asc'},
                            {'label': 'Impactos ↓', 'value': 'impactos_desc'},
                            {'label': 'Impactos ↑', 'value': 'impactos_asc'}
                        ], value='valor_desc', clearable=False, style={'width': '180px', 'fontFamily': 'Inter'})
                    ], style={'marginRight': '20px'}),
                    html.Div([
                        html.Label("Mostrar:", style={
                                   'fontWeight': 'bold', 'marginRight': '10px', 'fontFamily': 'Inter'}),
                        dcc.Dropdown(id='prov-dd-limit', options=[
                            {'label': '10', 'value': 10},
                            {'label': '50', 'value': 50},
                            {'label': '100', 'value': 100},
                            {'label': '200', 'value': 200},
                            {'label': '500', 'value': 500},
                            {'label': '1000', 'value': 1000},
                            {'label': 'Todos', 'value': -1}
                        ], value=10, clearable=False, style={'width': '120px', 'fontFamily': 'Inter'})
                    ]),
                    html.Div([
                        html.Label("Buscar:", style={
                                   'fontWeight': 'bold', 'marginRight': '10px', 'fontFamily': 'Inter'}),
                        dcc.Input(id='prov-input-molecula', type='text', placeholder='Código o nombre...',
                                  debounce=True, style={
                                      'width': '250px', 'padding': '8px', 'borderRadius': '6px', 'border': '1px solid #d1d5db', 'fontFamily': 'Inter'})
                    ], style={'marginRight': '20px'}),
                ], style={'marginBottom': '20px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'flexWrap': 'wrap', 'gap': '10px'}),
                html.Div(id='prov-tabla-mol')
            ], id='prov-row-3', style={'borderRadius': '16px', 'padding': '24px', 'marginBottom': '48px', 'boxShadow': '0 8px 32px rgba(0,0,0,0.1)'}),
        ], style={'marginBottom': '60px'}),

        # TQ Section
        html.Div([
            html.Div([
                html.H2("🎯 Eventos - Tecnoquímicas", style={
                        'textAlign': 'center', 'marginBottom': '10px', 'fontFamily': 'Inter', 'fontSize': '28px', 'fontWeight': 'bold'}),
                html.P(id='prov-tq-quarter', style={
                       'textAlign': 'center', 'fontSize': '16px', 'color': '#6b7280', 'marginBottom': '30px', 'fontFamily': 'Inter'})
            ]),

            html.Div([
                html.Div([
                    html.Div([
                        html.Label("Vendedor:", style={
                                   'fontWeight': 'bold', 'marginRight': '10px', 'fontFamily': 'Inter', 'width': '100px'}),
                        dcc.Dropdown(id='prov-dd-tq-vendedor', options=[], value='Todos',
                                     clearable=False, style={'width': '750px', 'fontFamily': 'Inter'})
                    ], id='prov-tq-vendedor-container', style={'marginRight': '20px'}),
                    html.Div([
                        html.Label("Trimestre:", style={
                                   'fontWeight': 'bold', 'marginRight': '10px', 'fontFamily': 'Inter'}),
                        dcc.Dropdown(id='prov-dd-tq-quarter', options=[], value=None,
                                     clearable=False, style={'width': '200px', 'fontFamily': 'Inter'})
                    ])
                ], style={'marginBottom': '20px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center', 'flexWrap': 'wrap'}),
                dcc.Graph(id='prov-tq-prog')
            ], id='prov-tq-row1', style={'borderRadius': '16px', 'padding': '24px', 'marginBottom': '24px', 'boxShadow': '0 8px 32px rgba(0,0,0,0.1)'})
        ], style={'marginTop': '60px'})

    ], style={'margin': '0 auto', 'padding': '0 40px'}),

], id='prov-main', style={
    'width': '100%', 'minHeight': '100vh',
    'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
    'padding': '20px 0',
    'background': 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 25%, #f8fafc 50%, #f1f5f9 100%)',
    'backgroundSize': '400% 400%',
    'animation': 'gradientShift 15s ease infinite'
})

# ==================== CALLBACKS ====================


@callback(
    [Output('prov-dd-lab', 'options'),
     Output('prov-dd-mes', 'options'),
     Output('prov-dd-vendedor', 'options'),
     Output('prov-dd-tq-vendedor', 'options'),
     Output('prov-dd-tq-quarter', 'options'),
     Output('prov-dd-tq-quarter', 'value')],
    [Input('prov-data-store', 'data')]
)
def update_dropdown_options(data_store):
    """Actualizar opciones de dropdowns"""
    try:
        if not analyzer_ventas or not analyzer_impactos:
            return [{'label': 'Todos', 'value': 'Todos'}] * 4 + [[], None]

        labs = analyzer_ventas.laboratorios_list or ['Todos']
        meses = analyzer_ventas.meses_list or ['Todos']
        vendedores = analyzer_ventas.vendedores_list or ['Todos']
        vendedores_tq = analyzer_impactos.vendedores_list or ['Todos']
        quarters = analyzer_impactos.get_quarters_disponibles() or []

        labs_opts = [{'label': v, 'value': v} for v in labs]
        meses_opts = [{'label': m, 'value': m} for m in meses]
        vendedores_opts = [{'label': v, 'value': v} for v in vendedores]
        vendedores_tq_opts = [{'label': v, 'value': v} for v in vendedores_tq]
        quarters_opts = [{'label': q, 'value': q} for q in quarters]

        # Valor por defecto: quarter actual
        quarter_default = analyzer_impactos.quarter_actual if quarters else None

        return labs_opts, meses_opts, vendedores_opts, vendedores_tq_opts, quarters_opts, quarter_default
    except Exception as e:
        return [{'label': 'Todos', 'value': 'Todos'}] * 4 + [[], None]


@callback(
    Output('prov-tq-vendedor-container', 'style'),
    [Input('session-store', 'data')]
)
def show_tq_vendedor_dropdown(session_data):
    """Mostrar dropdown de vendedor TQ solo para admin"""
    try:
        if can_see_all_vendors(session_data):
            return {'marginRight': '20px'}
        else:
            return {'display': 'none'}
    except:
        return {'display': 'none'}


@callback(
    Output('prov-data-store', 'data'),
    [Input('prov-btn-reload', 'n_clicks')],
    prevent_initial_call=True
)
def reload_data(n_clicks):
    """Recargar datos desde Firebase"""
    if n_clicks > 0:
        try:
            start_time = time.time()
            if analyzer_ventas:
                analyzer_ventas.reload_data()
            if analyzer_impactos:
                analyzer_impactos.reload_data()

            return {
                'last_update': n_clicks,
                'timestamp': datetime.now().isoformat(),
                'success': True,
                'load_time': time.time() - start_time
            }
        except Exception as e:
            return {
                'last_update': n_clicks,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'success': False
            }
    return dash.no_update


@callback(
    Output('prov-notification', 'children'),
    [Input('prov-data-store', 'data')],
    prevent_initial_call=True
)
def show_notification(data_store):
    """Mostrar notificación"""
    if data_store and data_store.get('last_update', 0) > 0:
        if data_store.get('error'):
            return html.Div([
                html.Div([
                    html.Span("❌ Error al actualizar datos",
                              style={'fontFamily': 'Inter'})
                ], style={'backgroundColor': '#e74c3c', 'color': 'white', 'padding': '12px 16px', 'borderRadius': '6px', 'fontSize': '12px', 'fontFamily': 'Inter'})
            ])
        else:
            load_time = data_store.get('load_time', 0)
            return html.Div([
                html.Div([
                    html.Span(f"✅ Actualizado en {load_time:.1f}s", style={
                              'fontFamily': 'Inter'})
                ], style={'backgroundColor': '#27ae60', 'color': 'white', 'padding': '12px 16px', 'borderRadius': '6px', 'fontSize': '12px', 'fontFamily': 'Inter'})
            ])
    return []


@callback(
    Output('prov-subtitle', 'children'),
    [Input('session-store', 'data'),
     Input('prov-dd-lab', 'value'),
     Input('prov-dd-mes', 'value'),
     Input('prov-dd-vendedor', 'value')]
)
def update_subtitle(session_data, laboratorio, mes, dropdown_vendedor):
    """Actualizar subtítulo"""
    try:
        vendedor = get_selected_vendor(session_data, dropdown_vendedor)
        parts = []

        if laboratorio and laboratorio != 'Todos':
            parts.append(f"Lab: {laboratorio}")
        else:
            parts.append("Todos los Laboratorios")

        if mes and mes != 'Todos':
            parts.append(f"Mes: {mes}")

        if vendedor != 'Todos' and can_see_all_vendors(session_data):
            parts.append(f"Vendedor: {vendedor}")

        return " • ".join(parts) if parts else "Análisis de ventas por laboratorio"
    except:
        return "Análisis de ventas por laboratorio"


@callback(
    Output('prov-tq-quarter', 'children'),
    [Input('prov-data-store', 'data')]
)
def update_tq_quarter(data_store):
    """Actualizar quarter TQ"""
    try:
        if analyzer_impactos:
            return f"Trimestre Actual: {analyzer_impactos.quarter_actual}"
        return "Trimestre: N/A"
    except:
        return "Trimestre: N/A"


@callback(
    [Output('prov-dd-vendedor-container', 'style'),
     Output('prov-dd-vendedor', 'value')],
    [Input('session-store', 'data')]
)
def update_dropdown_visibility(session_data):
    """Mostrar/ocultar dropdown vendedor"""
    try:
        if not session_data or not can_see_all_vendors(session_data):
            vendor = get_user_vendor_filter(
                session_data) if session_data else 'Todos'
            return {'display': 'none'}, vendor
        else:
            return {'flex': '1', 'minWidth': '250px'}, 'Todos'
    except:
        return {'display': 'none'}, 'Todos'


@callback(
    Output('prov-panel', 'children'),
    [Input('session-store', 'data'),
     Input('prov-dd-lab', 'value'),
     Input('prov-dd-mes', 'value'),
     Input('prov-dd-vendedor', 'value'),
     Input('prov-data-store', 'data'),
     Input('prov-theme-store', 'data')]
)
def update_panel(session_data, laboratorio, mes, dropdown_vendedor, data_store, theme):
    """Actualizar panel analítico"""
    try:
        if not analyzer_ventas:
            return html.Div("Analyzer no disponible", style={'textAlign': 'center', 'padding': '20px', 'fontFamily': 'Inter'})

        vendedor = get_selected_vendor(session_data, dropdown_vendedor)
        resumen = analyzer_ventas.get_resumen_general(
            laboratorio or 'Todos', mes or 'Todos', vendedor)

        return create_analytical_panel(resumen, theme == 'dark')
    except Exception as e:
        return html.Div(f"Error: {str(e)}", style={'textAlign': 'center', 'padding': '20px', 'fontFamily': 'Inter'})


@callback(
    Output('prov-g-labs', 'figure'),
    [Input('session-store', 'data'),
     Input('prov-dd-mes', 'value'),
     Input('prov-dd-vendedor', 'value'),
     Input('prov-data-store', 'data'),
     Input('prov-theme-store', 'data')]
)
def update_grafico_labs(session_data, mes, dropdown_vendedor, data_store, theme):
    """Top 10 laboratorios"""
    try:
        if not analyzer_ventas:
            return create_empty_figure("Analyzer no disponible", theme)

        vendedor = get_selected_vendor(session_data, dropdown_vendedor)
        data = analyzer_ventas.get_ventas_por_laboratorio(
            mes or 'Todos', vendedor, top_n=10)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            return create_empty_figure("No hay datos", theme)

        data_sorted = data.sort_values('valor_ventas', ascending=True)
        colors = [BLUE_COLORS_BG[i % len(BLUE_COLORS_BG)]
                  for i in range(len(data_sorted))]
        borders = [BLUE_COLORS_BORDER[i %
                                      len(BLUE_COLORS_BORDER)] for i in range(len(data_sorted))]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=data_sorted['valor_ventas'],
            y=data_sorted['laboratorio'],
            orientation='h',
            marker=dict(color=colors, line=dict(color=borders, width=1.5)),
            text=[format_currency_int(val)
                  for val in data_sorted['valor_ventas']],
            textposition='inside',
            textfont=dict(color=theme_styles["text_color"], size=10,
                          family='Inter', weight='bold'),
            hovertemplate="<b>%{y}</b><br>Ventas: %{text}<br>Clientes: %{customdata}<extra></extra>",
            customdata=data_sorted['num_clientes']
        ))

        fig.update_layout(
            height=450,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=11,
                      color=theme_styles['text_color']),
            xaxis=dict(title="Ventas ($)", showgrid=True,
                       gridcolor=theme_styles['grid_color'], tickformat='$,.0f'),
            yaxis=dict(title="", tickfont=dict(size=10)),
            margin=dict(t=10, b=40, l=150, r=40),
            showlegend=False
        )
        return fig
    except Exception as e:
        return create_empty_figure("Error", theme)


@callback(
    Output('prov-g-evol', 'figure'),
    [Input('session-store', 'data'),
     Input('prov-dd-lab', 'value'),
     Input('prov-dd-vendedor', 'value'),
     Input('prov-data-store', 'data'),
     Input('prov-theme-store', 'data')]
)
def update_grafico_evolucion(session_data, laboratorio, dropdown_vendedor, data_store, theme):
    """Evolución de ventas"""
    try:
        if not analyzer_ventas:
            return create_empty_figure("Analyzer no disponible", theme)

        vendedor = get_selected_vendor(session_data, dropdown_vendedor)

        data = analyzer_ventas.get_evolucion_mensual(
            laboratorio or 'Todos', vendedor)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            return create_empty_figure("No hay datos", theme)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=data['mes'],
            y=data['valor_ventas'],
            mode='lines+markers',
            line=dict(color=BLUE_COLORS_BORDER[0], width=3, shape='spline'),
            marker=dict(size=10, color=BLUE_COLORS_BG[0],
                        line=dict(color=BLUE_COLORS_BORDER[0], width=2)),
            fill='tozeroy',
            fillcolor=BLUE_COLORS_BG[1],
            hovertemplate="<b>%{x}</b><br>Ventas: %{customdata}<br>Clientes: %{text}<extra></extra>",
            customdata=[format_currency_int(val)
                        for val in data['valor_ventas']],
            text=data['num_clientes']
        ))

        fig.update_layout(
            height=450,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=11,
                      color=theme_styles['text_color']),
            xaxis=dict(title="Mes", showgrid=True,
                       gridcolor=theme_styles['grid_color'], tickangle=-45),
            yaxis=dict(title="Ventas ($)", showgrid=True,
                       gridcolor=theme_styles['grid_color'], tickformat='$,.0f'),
            showlegend=False,
            margin=dict(t=10, b=60, l=60, r=20)
        )
        return fig
    except Exception as e:
        return create_empty_figure("Error", theme)


@callback(
    Output('prov-g-impactos', 'figure'),
    [Input('session-store', 'data'),
     Input('prov-dd-lab', 'value'),
     Input('prov-dd-vendedor', 'value'),
     Input('prov-data-store', 'data'),
     Input('prov-theme-store', 'data')]
)
def update_grafico_impactos(session_data, laboratorio, dropdown_vendedor, data_store, theme):
    """Evolución de impactos"""
    try:
        if not analyzer_ventas:
            return create_empty_figure("Analyzer no disponible", theme)

        vendedor = get_selected_vendor(session_data, dropdown_vendedor)
        data = analyzer_ventas.get_evolucion_impactos_mensual(
            laboratorio or 'Todos', vendedor)
        theme_styles = get_theme_styles(theme)

        if data.empty:
            return create_empty_figure("No hay datos", theme)

        colors = [BLUE_COLORS_BG[i % len(BLUE_COLORS_BG)]
                  for i in range(len(data))]
        borders = [BLUE_COLORS_BORDER[i %
                                      len(BLUE_COLORS_BORDER)] for i in range(len(data))]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=data['mes'],
            y=data['impactos'],
            marker=dict(color=colors, line=dict(color=borders, width=1.5)),
            text=[f"{int(val)}" for val in data['impactos']],
            textposition='outside',
            textfont=dict(
                size=11, color=theme_styles['text_color'], family='Inter', weight='bold'),
            hovertemplate="<b>%{x}</b><br>Impactos: %{y}<extra></extra>"
        ))

        fig.update_layout(
            height=400,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=10,
                      color=theme_styles['text_color']),
            xaxis=dict(title="Mes", showgrid=False, tickangle=-45),
            yaxis=dict(title="Impactos (Clientes Únicos)",
                       showgrid=True, gridcolor=theme_styles['grid_color']),
            showlegend=False,
            margin=dict(t=10, b=60, l=60, r=20)
        )
        return fig
    except Exception as e:
        return create_empty_figure("Error", theme)


@callback(
    Output('prov-g-clientes', 'figure'),
    [Input('session-store', 'data'),
     Input('prov-dd-lab', 'value'),
     Input('prov-dd-mes', 'value'),
     Input('prov-dd-vendedor', 'value'),
     Input('prov-data-store', 'data'),
     Input('prov-theme-store', 'data')]
)
def update_grafico_clientes(session_data, laboratorio, mes, dropdown_vendedor, data_store, theme):
    """Top 10 clientes"""
    try:
        if not analyzer_ventas:
            return create_empty_figure("Analyzer no disponible", theme)

        vendedor = get_selected_vendor(session_data, dropdown_vendedor)

        data = \
            analyzer_ventas.get_top_clientes(
                laboratorio or 'Todos',
                mes or 'Todos',
                vendedor,
                top_n=10
            )
        theme_styles = get_theme_styles(theme)

        if data.empty:
            return create_empty_figure("No hay datos", theme)

        data_sorted = data.sort_values('valor_ventas', ascending=True)
        colors = \
            [
                BLUE_COLORS_BG[i % len(BLUE_COLORS_BG)]
                for i in range(len(data_sorted))
            ]
        borders = \
            [
                BLUE_COLORS_BORDER[i % len(BLUE_COLORS_BORDER)]
                for i in range(len(data_sorted))
            ]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=data_sorted['valor_ventas'],
            y=[cliente[:40] + "..." if len(cliente) >
               40 else cliente for cliente in data_sorted['cliente']],
            orientation='h',
            marker=dict(color=colors, line=dict(color=borders, width=1.5)),
            text=[format_currency_int(val)
                  for val in data_sorted['valor_ventas']],
            textposition='inside',
            textfont=dict(color=theme_styles["text_color"], size=10,
                          family='Inter', weight='bold'),
            hovertemplate="<b>%{customdata[0]}</b><br>Ventas: %{text}<br>Zona: %{customdata[1]}<extra></extra>",
            customdata=[[cliente, zona] for cliente, zona in zip(
                data_sorted['cliente'], data_sorted['zona'])]
        ))

        fig.update_layout(
            height=450,
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=11,
                      color=theme_styles['text_color']),
            xaxis=dict(title="Ventas ($)", showgrid=True,
                       gridcolor=theme_styles['grid_color'], tickformat='$,.0f'),
            yaxis=dict(title="", tickfont=dict(size=10)),
            margin=dict(t=10, b=40, l=180, r=40),
            showlegend=False
        )
        return fig
    except Exception as e:
        print("Error en update_grafico_clientes:", str(e))
        return create_empty_figure("Error", theme)


@callback(
    Output('prov-tabla-mol', 'children'),
    [Input('session-store', 'data'),
     Input('prov-dd-lab', 'value'),
     Input('prov-dd-mes', 'value'),
     Input('prov-dd-vendedor', 'value'),
     Input('prov-dd-periodo', 'value'),
     Input('prov-input-molecula', 'value'),
     Input('prov-dd-sort', 'value'),
     Input('prov-dd-limit', 'value'),
     Input('prov-data-store', 'data'),
     Input('prov-theme-store', 'data')]
)
def update_tabla_moleculas(session_data, laboratorio, mes, dropdown_vendedor, periodo, buscar_mol, sort_by, limit, data_store, theme):
    """Tabla de moléculas con filtros mejorados"""
    try:
        if not analyzer_ventas or not analyzer_ventas.db:
            return html.Div("Analyzer no disponible", style={'textAlign': 'center', 'padding': '20px', 'fontFamily': 'Inter'})

        # Cargar nombres de moléculas
        codigos_productos = analyzer_ventas.db.get_by_path(
            "maestros/codigos_productos")

        vendedor = get_selected_vendor(session_data, dropdown_vendedor)
        data = analyzer_ventas.get_ventas_por_molecula(
            laboratorio or 'Todos', mes or 'Todos', vendedor, periodo or 'mensual')
        theme_styles = get_theme_styles(theme)

        if data.empty:
            return html.Div("No hay datos", style={'textAlign': 'center', 'padding': '20px', 'color': theme_styles['text_color'], 'fontFamily': 'Inter'})

        # Agregar nombres de moléculas
        if codigos_productos:
            data['nombre_molecula'] = data['molecula'].apply(
                lambda x: codigos_productos.get(str(x), {}).get(
                    'ds', 'Sin descripción') if codigos_productos.get(str(x)) else 'Sin descripción'
            )
        else:
            data['nombre_molecula'] = 'Sin descripción'

        # Aplicar filtro de búsqueda
        if buscar_mol and buscar_mol.strip():
            search_term = buscar_mol.strip().lower()
            data = data[
                data['molecula'].str.lower().str.contains(search_term, na=False) |
                data['nombre_molecula'].str.lower(
                ).str.contains(search_term, na=False)
            ]

        # Aplicar sorting
        if sort_by == 'valor_desc':
            data = data.sort_values('valor_ventas', ascending=False)
        elif sort_by == 'valor_asc':
            data = data.sort_values('valor_ventas', ascending=True)
        elif sort_by == 'impactos_desc':
            data = data.sort_values('impactos', ascending=False)
        elif sort_by == 'impactos_asc':
            data = data.sort_values('impactos', ascending=True)

        # Aplicar límite
        if limit and limit > 0:
            data = data.head(limit)

        # Tabla moderna con scroll
        bg_header = 'rgba(55, 65, 81, 1)' if theme == 'dark' else 'rgba(59, 130, 246, 1)'

        table_header = [
            html.Thead(html.Tr([
                html.Th("Código", style={'padding': '14px', 'textAlign': 'left',
                        'fontWeight': 'bold', 'color': 'white', 'position': 'sticky', 'top': '0', 'backgroundColor': bg_header, 'zIndex': '10', 'fontSize': '12px', 'fontFamily': 'Inter'}),
                html.Th("Nombre Molécula", style={'padding': '14px', 'textAlign': 'left',
                        'fontWeight': 'bold', 'color': 'white', 'position': 'sticky', 'top': '0', 'backgroundColor': bg_header, 'zIndex': '10', 'fontSize': '12px', 'fontFamily': 'Inter'}),
                html.Th("Laboratorio", style={
                        'padding': '14px', 'textAlign': 'left', 'fontWeight': 'bold', 'color': 'white', 'position': 'sticky', 'top': '0', 'backgroundColor': bg_header, 'zIndex': '10', 'fontSize': '12px', 'fontFamily': 'Inter'}),
                html.Th("Periodo", style={'padding': '12px', 'textAlign': 'center',
                        'fontWeight': 'bold', 'borderBottom': '2px solid #e5e7eb'}),
                html.Th("Valor Ventas", style={
                        'padding': '14px', 'textAlign': 'right', 'fontWeight': 'bold', 'color': 'white', 'position': 'sticky', 'top': '0', 'backgroundColor': bg_header, 'zIndex': '10', 'fontSize': '12px', 'fontFamily': 'Inter'}),
                html.Th("Unidades", style={'padding': '14px', 'textAlign': 'right',
                        'fontWeight': 'bold', 'color': 'white', 'position': 'sticky', 'top': '0', 'backgroundColor': bg_header, 'zIndex': '10', 'fontSize': '12px', 'fontFamily': 'Inter'}),
                html.Th("Impactos", style={'padding': '14px', 'textAlign': 'right',
                        'fontWeight': 'bold', 'color': 'white', 'position': 'sticky', 'top': '0', 'backgroundColor': bg_header, 'zIndex': '10', 'fontSize': '12px', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': bg_header}))
        ]

        rows = []
        for idx, row in data.iterrows():
            bg_color = theme_styles['paper_color'] if idx % 2 == 0 else (
                'rgba(249, 250, 251, 0.5)' if theme == 'light' else 'rgba(55, 65, 81, 0.3)')
            rows.append(html.Tr([
                html.Td(row['molecula'], style={
                        'padding': '12px', 'fontWeight': '600', 'fontFamily': 'Inter', 'fontSize': '11px'}),
                html.Td(row['nombre_molecula'][:60] + "..." if len(row['nombre_molecula']) > 60 else row['nombre_molecula'],
                        style={'padding': '12px', 'fontSize': '11px', 'fontFamily': 'Inter'}),
                html.Td(row['laboratorio'], style={
                        'padding': '12px', 'fontSize': '11px', 'fontFamily': 'Inter'}),
                html.Td(row['periodo'], style={
                        'padding': '10px', 'textAlign': 'center'}),
                html.Td(format_currency_int(row['valor_ventas']), style={
                        'padding': '12px', 'textAlign': 'right', 'fontWeight': '600', 'fontSize': '11px', 'fontFamily': 'Inter'}),
                html.Td(f"{int(row['unidades']):,}", style={
                        'padding': '12px', 'textAlign': 'right', 'fontSize': '11px', 'fontFamily': 'Inter'}),
                html.Td(f"{int(row['impactos']):,}", style={
                        'padding': '12px', 'textAlign': 'right', 'fontWeight': 'bold', 'color': '#3b82f6', 'fontSize': '11px', 'fontFamily': 'Inter'})
            ], style={'backgroundColor': bg_color, 'borderBottom': '1px solid rgba(229, 231, 235, 0.5)'}))

        return html.Div([
            html.Table(
                table_header + [html.Tbody(rows)],
                style={'width': '100%', 'borderCollapse': 'collapse',
                       'fontSize': '12px', 'fontFamily': 'Inter'}
            )
        ], style={
            'maxHeight': '500px',
            'overflowY': 'auto',
            'overflowX': 'auto',
            'backgroundColor': theme_styles['paper_color'],
            'borderRadius': '12px',
            'boxShadow': '0 4px 12px rgba(0,0,0,0.1)',
            'border': '1px solid rgba(229, 231, 235, 0.3)'
        })
    except Exception as e:
        return html.Div(f"Error: {str(e)}", style={'textAlign': 'center', 'padding': '20px', 'fontFamily': 'Inter'})


@callback(
    Output('prov-tq-prog', 'figure'),
    [Input('session-store', 'data'),
     Input('prov-dd-tq-vendedor', 'value'),
     Input('prov-dd-tq-quarter', 'value'),
     Input('prov-data-store', 'data'),
     Input('prov-theme-store', 'data')]
)
def update_tq_progreso(session_data, dropdown_tq_vendedor, selected_quarter, data_store, theme):
    """Progreso por molécula TQ unificado con histórico"""
    try:
        if not analyzer_impactos or not analyzer_impactos.db:
            return create_empty_figure("Analyzer no disponible", theme)

        # Cargar nombres de moléculas
        codigos_productos = analyzer_impactos.db.get_by_path(
            "maestros/codigos_productos")

        # Determinar vendedor a mostrar
        if can_see_all_vendors(session_data):
            vendedor = dropdown_tq_vendedor if dropdown_tq_vendedor else 'Todos'
        else:
            vendedor = get_user_vendor_filter(session_data)

        # Usar quarter seleccionado o el actual por defecto
        quarter = selected_quarter if selected_quarter else analyzer_impactos.quarter_actual

        # Obtener proyectadas del vendedor
        proyectadas = analyzer_impactos.get_proyectadas_vendedor(vendedor)
        proyectadas_grouped = proyectadas.groupby(
            'molecula')['cantidad_proyectada'].sum()

        # Obtener reales del quarter seleccionado
        reales = analyzer_impactos.get_reales_vendedor(vendedor, quarter)
        reales_grouped = reales.groupby('molecula').size()

        # Combinar datos
        data = pd.DataFrame({
            'proyectado': proyectadas_grouped,
            'alcanzado': reales_grouped
        }).fillna(0)

        data['faltante'] = data['proyectado'] - data['alcanzado']
        data['porcentaje'] = (data['alcanzado'] /
                              data['proyectado'] * 100).fillna(0)
        data = data.reset_index()
        data.columns = ['molecula', 'proyectado',
                        'alcanzado', 'faltante', 'porcentaje']
        data = data.sort_values('porcentaje', ascending=True)

        theme_styles = get_theme_styles(theme)

        if data.empty:
            return create_empty_figure("No hay datos para este vendedor y quarter", theme)

        # Agregar nombres de moléculas para hover
        if codigos_productos:
            data['nombre_molecula'] = data['molecula'].apply(
                lambda x: codigos_productos.get(str(x), {}).get(
                    'ds', 'Sin descripción') if codigos_productos.get(str(x)) else 'Sin descripción'
            )
        else:
            data['nombre_molecula'] = 'Sin descripción'

        fig = go.Figure()

        # Barra de fondo (Meta completa)
        fig.add_trace(go.Bar(
            name='Meta',
            x=data['proyectado'],
            y=data['molecula'],
            orientation='h',
            marker=dict(
                color='rgba(226, 232, 240, 0.4)',
                line=dict(color='rgba(148, 163, 184, 0.6)', width=1)
            ),
            text=[f"Meta: {int(val)}" for val in data['proyectado']],
            textposition='inside',
            textangle=0,
            textfont=dict(color='rgba(100, 116, 139, 0.8)',
                          size=10, family='Inter'),
            hovertemplate="<b>%{customdata}</b><br>Código: %{y}<br>Meta Total: %{x}<extra></extra>",
            customdata=data['nombre_molecula']
        ))

        # Barra de progreso (Alcanzado)
        fig.add_trace(go.Bar(
            name='Alcanzado',
            x=data['alcanzado'],
            y=data['molecula'],
            orientation='h',
            marker=dict(
                color='rgba(34, 197, 94, 0.85)',
                line=dict(color='rgba(22, 163, 74, 1)', width=2)
            ),
            text=[f"{int(val)} ({pct:.0f}%)" for val, pct in zip(
                data['alcanzado'], data['porcentaje'])],
            textposition='inside',
            textangle=0,
            textfont=dict(color='white', size=11,
                          family='Inter', weight='bold'),
            hovertemplate="<b>%{customdata}</b><br>Código: %{y}<br>Alcanzado: %{x}<br>Progreso: %{text}<extra></extra>",
            customdata=data['nombre_molecula']
        ))

        fig.update_layout(
            barmode='overlay',
            height=max(500, len(data) * 60),
            plot_bgcolor=theme_styles['plot_bg'],
            paper_bgcolor=theme_styles['plot_bg'],
            font=dict(family="Inter", size=11,
                      color=theme_styles['text_color']),
            xaxis=dict(
                title=dict(text="Impactos", font=dict(
                    size=13, weight='bold', family='Inter')),
                showgrid=True,
                gridcolor=theme_styles['grid_color'],
                gridwidth=0.5,
                zeroline=True,
                zerolinecolor=theme_styles['grid_color']
            ),
            yaxis=dict(
                title="",
                tickfont=dict(size=11, weight=600, family='Inter'),
                showgrid=False
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(size=13, weight='bold', family='Inter'),
                bgcolor='rgba(255, 255, 255, 0.8)' if theme == 'light' else 'rgba(31, 41, 55, 0.8)',
                bordercolor=theme_styles['grid_color'],
                borderwidth=1
            ),
            margin=dict(t=70, b=50, l=110, r=50),
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Inter"
            )
        )

        return fig
    except Exception as e:
        return create_empty_figure(f"Error: {str(e)}", theme)


@callback(
    [Output('prov-theme-store', 'data'),
     Output('prov-theme-toggle', 'children'),
     Output('prov-main', 'style')],
    [Input('prov-theme-toggle', 'n_clicks')],
    [State('prov-theme-store', 'data')]
)
def toggle_theme(n_clicks, current_theme):
    """Toggle tema"""
    if not n_clicks:
        return ("light", "🌙", {
            'width': '100%', 'minHeight': '100vh',
            'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
            'padding': '20px 0',
            'background': 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 25%, #f8fafc 50%, #f1f5f9 100%)',
            'backgroundSize': '400% 400%',
            'animation': 'gradientShift 15s ease infinite',
            'color': '#111827'
        })

    is_dark = current_theme != 'dark'
    icon = "☀️" if is_dark else "🌙"
    new_theme = 'dark' if is_dark else 'light'

    if is_dark:
        return (new_theme, icon, {
            'width': '100%', 'minHeight': '100vh',
            'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
            'padding': '20px 0',
            'background': 'linear-gradient(135deg, #0f172a 0%, #1e293b 25%, #334155 50%, #475569 100%)',
            'backgroundSize': '400% 400%',
            'animation': 'gradientShift 15s ease infinite',
            'color': '#f8fafc'
        })
    else:
        return (new_theme, icon, {
            'width': '100%', 'minHeight': '100vh',
            'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
            'padding': '20px 0',
            'background': 'linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 25%, #f8fafc 50%, #f1f5f9 100%)',
            'backgroundSize': '400% 400%',
            'animation': 'gradientShift 15s ease infinite',
            'color': '#111827'
        })


@callback(
    [Output('prov-dd-lab', 'style'),
     Output('prov-dd-mes', 'style'),
     Output('prov-dd-vendedor', 'style'),
     Output('prov-dd-periodo', 'style'),
     Output('prov-dd-tq-vendedor', 'style'),
     Output('prov-dd-tq-quarter', 'style'),
     Output('prov-dd-sort', 'style'),
     Output('prov-dd-limit', 'style'),
     Output('prov-dd-lab', 'className'),
     Output('prov-dd-mes', 'className'),
     Output('prov-dd-vendedor', 'className'),
     Output('prov-dd-periodo', 'className'),
     Output('prov-dd-tq-vendedor', 'className'),
     Output('prov-dd-tq-quarter', 'className'),
     Output('prov-dd-sort', 'className'),
     Output('prov-dd-limit', 'className')],
    [Input('prov-theme-store', 'data')]
)
def update_dropdown_styles(theme):
    """Estilos dropdowns"""
    dropdown_style = get_dropdown_style(theme)
    dropdown_style['fontFamily'] = 'Inter'

    # Estilo especial para dropdown de vendedor TQ (más ancho)
    dropdown_style_tq_vendedor = dropdown_style.copy()
    dropdown_style_tq_vendedor['width'] = '550px'
    dropdown_style_tq_vendedor['minWidth'] = '550px'

    css_class = 'dash-dropdown dark-theme' if theme == 'dark' else 'dash-dropdown'

    return [
        dropdown_style,  # prov-dd-lab
        dropdown_style,  # prov-dd-mes
        dropdown_style,  # prov-dd-vendedor
        dropdown_style,  # prov-dd-periodo
        dropdown_style_tq_vendedor,  # prov-dd-tq-vendedor (MÁS ANCHO)
        dropdown_style,  # prov-dd-tq-quarter
        dropdown_style,  # prov-dd-sort
        dropdown_style,  # prov-dd-limit
        css_class, css_class, css_class, css_class,
        css_class, css_class, css_class, css_class
    ]


@callback(
    [Output('prov-controls', 'style'),
     Output('prov-header', 'style'),
     Output('prov-row-evol', 'style'),
     Output('prov-row-1', 'style'),
     Output('prov-row-2', 'style'),
     Output('prov-row-3', 'style'),
     Output('prov-tq-row1', 'style')],
    [Input('prov-theme-store', 'data')]
)
def update_container_styles(theme):
    """Estilos contenedores"""
    theme_styles = get_theme_styles(theme)

    base_style = {
        'backgroundColor': theme_styles['paper_color'],
        'padding': '24px',
        'borderRadius': '16px',
        'boxShadow': theme_styles['card_shadow'],
        'marginBottom': '24px',
        'color': theme_styles['text_color']
    }

    controls_style = {
        'display': 'flex', 'gap': '24px', 'alignItems': 'stretch',
        'backgroundColor': theme_styles['paper_color'],
        'borderRadius': '16px', 'padding': '24px', 'marginBottom': '24px',
        'boxShadow': theme_styles['card_shadow'], 'flexWrap': 'wrap',
        'color': theme_styles['text_color']
    }

    header_style = {
        'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between',
        'backgroundColor': theme_styles['paper_color'] if theme == 'dark' else 'linear-gradient(135deg, rgba(209, 213, 219, 0.75) 0%, rgba(156, 163, 175, 0.8) 25%, rgba(107, 114, 128, 0.85) 50%, rgba(75, 85, 99, 0.9) 75%, rgba(55, 65, 81, 0.95) 100%)',
        'borderRadius': '20px', 'padding': '32px 40px', 'marginBottom': '24px',
        'boxShadow': theme_styles['card_shadow'], 'minHeight': '80px', 'color': '#ffffff'
    }

    return [controls_style, header_style] + [base_style] * 5

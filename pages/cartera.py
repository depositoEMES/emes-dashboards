import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.express as px
import plotly.graph_objects as go

from analyzers import CarteraAnalyzer
from utils import format_currency_int, get_theme_styles


# Initialize analyzer
analyzer = CarteraAnalyzer()
df = analyzer.load_data_from_firebase()


layout = html.Div([
    # Store for theme
    dcc.Store(id='cartera-theme-store', data='light'),

    # Header
    html.Div([
        html.Div([
            html.H1(id='cartera-titulo-dashboard')
        ], style={'width': '60%', 'display': 'inline-block'}),

        html.Div([
            html.Button('🌙', id='cartera-theme-toggle', n_clicks=0)
        ], style={'width': '10%', 'display': 'inline-block', 'verticalAlign': 'top', 'textAlign': 'right'})
    ], style={'marginBottom': '30px', 'padding': '20px'}, id='cartera-header-container'),

    # Cards de resumen - 8 cards en 2 filas de 4 columnas
    html.Div([
        # Primera fila de cards
        html.Div([
            html.Div([
                html.H3("Cartera Total", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Arial'}),
                html.H2(
                    id='cartera-total-cartera', style={'color': '#e74c3c', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Arial'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='cartera-card-1'),

            html.Div([
                html.H3("Vencida", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Arial'}),
                html.H2(
                    id='cartera-total-vencida', style={'color': '#e74c3c', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Arial'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='cartera-card-2'),

            html.Div([
                html.H3("Sin Vencer", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Arial'}),
                html.H2(id='cartera-total-sin-vencer',
                        style={'color': '#27ae60', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Arial'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='cartera-card-3'),

            html.Div([
                html.H3("Calidad Cartera", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Arial'}),
                html.H2(id='cartera-calidad-cartera',
                        style={'color': '#9b59b6', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Arial'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='cartera-card-4')
        ], style={'marginBottom': '15px'}),

        # Segunda fila de cards
        html.Div([
            html.Div([
                html.H3("Clientes", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Arial'}),
                html.H2(id='cartera-total-clientes',
                        style={'color': '#3498db', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Arial'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='cartera-card-5'),

            html.Div([
                html.H3("Clientes con cartera vencida", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Arial'}),
                html.H2(id='cartera-clientes-vencida',
                        style={'color': '#e67e22', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Arial'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='cartera-card-6'),

            html.Div([
                html.H3("Facturas", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Arial'}),
                html.H2(
                    id='cartera-num-facturas', style={'color': '#16a085', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Arial'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='cartera-card-7'),

            html.Div([
                html.H3("% Vencida", style={
                        'color': '#34495e', 'fontSize': '14px', 'margin': '0 0 10px 0', 'fontFamily': 'Arial'}),
                html.H2(id='cartera-porcentaje-vencida',
                        style={'color': '#f39c12', 'fontSize': '20px', 'margin': '0', 'fontFamily': 'Arial'})
            ], style={'backgroundColor': 'white', 'padding': '15px', 'borderRadius': '8px',
                      'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center',
                      'width': '20%', 'display': 'inline-block', 'margin': '1.5%'}, id='cartera-card-8')
        ])
    ], style={'marginBottom': '30px'}),

    # Fila 1: Distribución por Días Vencidos y Forma de Pago
    html.Div([
        html.Div([
            html.H3("Distribución por Días Vencidos", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Arial'}),
            dcc.Graph(id='cartera-grafico-rangos')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'}),

        html.Div([
            html.H3("Distribución por Forma de Pago", style={
                    'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Arial'}),
            dcc.Graph(id='cartera-grafico-forma-pago')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'})
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'},
        id='cartera-row1-container'),

    # Fila 2: Treemap Cartera Total
    html.Div([
        html.H3("Mapa de Cartera Total por Cliente", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Arial'}),
        dcc.Graph(id='cartera-treemap-cartera')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'},
        id='cartera-row2-container'),

    # Fila 2.5: Treemap Cartera Vencida
    html.Div([
        html.H3("Mapa de Cartera Vencida por Cliente", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Arial'}),
        dcc.Graph(id='cartera-treemap-cartera-vencida')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'},
        id='cartera-row2-5-container'),

    # Fila 3: Top 10
    html.Div([
        html.Div([
            html.H3("Top 10 - Cartera Vencida",
                    style={'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Arial'}),
            dcc.Graph(id='cartera-top-vencida')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'}),

        html.Div([
            html.H3("Top 10 - Cartera Sin Vencer",
                    style={'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Arial'}),
            dcc.Graph(id='cartera-top-sin-vencer')
        ], style={'width': '48%', 'display': 'inline-block', 'margin': '1%'})
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'},
        id='cartera-row3-container'),

    # Fila 4: Análisis de Vencimientos - Configuración
    html.Div([
        html.H3("Análisis de Vencimientos Próximos", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Arial'}),
        html.Div([
            html.Label("Días para análisis:", style={
                       'marginBottom': '10px', 'fontWeight': 'bold', 'fontFamily': 'Arial'}),
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
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Arial'}),
        dcc.Graph(id='cartera-grafico-proximos-vencer')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'},
        id='cartera-row5-container'),

    # Fila 6: Tabla Detallada de Vencimientos
    html.Div([
        html.H3("Detalle de Documentos por Vencer", style={
                'textAlign': 'center', 'marginBottom': '20px', 'fontFamily': 'Arial'}),
        html.Div(id='cartera-tabla-proximos-vencer')
    ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px',
              'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'margin': '10px 0'},
        id='cartera-row6-container'),

    # Botón actualizar
    html.Div([
        html.Button('Actualizar Datos', id='cartera-btn-actualizar', n_clicks=0,
                    style={'backgroundColor': '#3498db', 'color': 'white', 'border': 'none',
                           'padding': '10px 20px', 'borderRadius': '5px', 'cursor': 'pointer',
                           'fontFamily': 'Arial'})
    ], style={'textAlign': 'center', 'margin': '20px 0'})

], style={'fontFamily': 'Arial', 'backgroundColor': '#f5f5f5', 'padding': '20px'}, id='cartera-main-container')


# Callback para obtener sesión y determinar vendedor
@callback(
    Output('cartera-user-session', 'data'),
    [Input('session-store', 'data')],  # Escucha la sesión global
    prevent_initial_call=True
)
def update_user_session(session_data):
    return session_data


@callback(
    [Output('cartera-theme-store', 'data'),
     Output('cartera-theme-toggle', 'children'),
     Output('cartera-main-container', 'style'),
     Output('cartera-header-container', 'style')],
    [Input('cartera-theme-toggle', 'n_clicks')],
    [State('cartera-theme-store', 'data')]
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


@callback(
    Output('cartera-dropdown-vendedor', 'style'),
    [Input('cartera-theme-store', 'data')]
)
def update_dropdown_style(theme):
    """
    Update dropdown style based on theme.
    """
    theme_styles = get_theme_styles(theme)

    if theme == 'dark':
        return {
            'fontFamily': 'Arial',
            'backgroundColor': theme_styles['paper_color'],
            'color': theme_styles['text_color']
        }
    else:
        return {'fontFamily': 'Arial'}

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
    [Output('cartera-row1-container', 'style'),
     Output('cartera-row2-container', 'style'),
     Output('cartera-row2-5-container', 'style'),
     Output('cartera-row3-container', 'style'),
     Output('cartera-row5-container', 'style'),
     Output('cartera-row6-container', 'style'),
     Output('cartera-config-container', 'style')],
    [Input('cartera-theme-store', 'data')]
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

    config_style = {
        'backgroundColor': theme_styles['paper_color'],
        'padding': '20px',
        'borderRadius': '8px',
        'margin': '10px 0',
        'color': theme_styles['text_color']
    }

    return chart_style, chart_style, chart_style, chart_style, chart_style, chart_style, config_style


# Callback para título (SIN input de dropdown-vendedor)
@callback(
    Output('cartera-titulo-dashboard', 'children'),
    [Input('session-store', 'data')]
)
def update_title(session_data):
    from utils import get_user_vendor_filter, can_see_all_vendors

    if not session_data:
        return "Dashboard de Cartera"

    if can_see_all_vendors(session_data):
        return "Dashboard de Cartera - Todos los Vendedores"
    else:
        vendor = get_user_vendor_filter(session_data)
        return f"Dashboard de Cartera - {vendor}"


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
     Input('cartera-btn-actualizar', 'n_clicks')]
)
def update_cards(session_data, n_clicks):
    from utils import get_user_vendor_filter

    try:
        vendor_filter = get_user_vendor_filter(session_data)
        resumen = analyzer.get_resumen(vendor_filter)

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
        print(f"Error en update_cards: {e}")
        return "$0", "$0", "$0", "0%", "0", "0", "0", "0%"


@callback(
    Output('cartera-grafico-rangos', 'figure'),
    [Input('session-store', 'data'),
     Input('cartera-btn-actualizar', 'n_clicks'),
     Input('cartera-theme-store', 'data')]
)
def update_rangos(session_data, n_clicks, theme):
    """
    Update overdue ranges chart.
    """
    from utils import get_user_vendor_filter

    vendor_filter = get_user_vendor_filter(session_data)
    data = analyzer.get_rangos_vencimiento(vendor_filter)
    theme_styles = get_theme_styles(theme)

    if data.empty:
        fig = px.bar(title="No hay datos disponibles")
        return fig

    # Create modern chart
    fig = go.Figure()

    colors = ['#2ECC71', '#F39C12', '#E74C3C',
              '#9B59B6', '#34495E', '#E67E22', '#95A5A6']

    for i, row in data.iterrows():
        fig.add_trace(go.Bar(
            x=[row['rango']],
            y=[row['saldo']],
            name=row['rango'],
            marker_color=colors[i % len(colors)],
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
        height=450,  # Increased height
        showlegend=False,
        plot_bgcolor=theme_styles['plot_bg'],
        paper_bgcolor=theme_styles['plot_bg'],
        font=dict(family="Arial", size=12, color=theme_styles['text_color']),
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
        margin=dict(t=60, b=120, l=100, r=60),  # Increased margins
        autosize=True
    )

    return fig


@callback(
    Output('cartera-grafico-forma-pago', 'figure'),
    [Input('session-store', 'data'),
     Input('cartera-btn-actualizar', 'n_clicks'),
     Input('cartera-theme-store', 'data')]
)
def update_forma_pago(session_data, n_clicks, theme):
    """
    Update payment method distribution chart.
    """
    from utils import get_user_vendor_filter

    vendor_filter = get_user_vendor_filter(session_data)
    data = analyzer.get_forma_pago(vendor_filter)
    theme_styles = get_theme_styles(theme)

    if data.empty:
        fig = px.pie(title="No hay datos disponibles")
        return fig

    # Modern donut chart with side legend
    fig = go.Figure(data=[go.Pie(
        labels=data['forma_pago'],
        values=data['saldo'],
        hole=.4,
        textinfo='percent',
        textposition='inside',
        marker=dict(
            colors=['#3498DB', '#E74C3C', '#2ECC71',
                    '#F39C12', '#9B59B6', '#1ABC9C', '#E67E22'],
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
        font=dict(family="Arial", size=12, color=theme_styles['text_color']),
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


@callback(
    Output('cartera-treemap-cartera', 'figure'),
    [Input('session-store', 'data'),
     Input('cartera-btn-actualizar', 'n_clicks'),
     Input('cartera-theme-store', 'data')]
)
def update_treemap(session_data, n_clicks, theme):
    """
    Update portfolio treemap with combined client-company names.
    """
    from utils import get_user_vendor_filter

    vendor_filter = get_user_vendor_filter(session_data)
    data = analyzer.get_treemap_data(vendor_filter)
    theme_styles = get_theme_styles(theme)

    if data.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False, font=dict(size=16, color=theme_styles['text_color'])
        )
        fig.update_layout(height=500, paper_bgcolor=theme_styles['plot_bg'])
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
        fig.update_layout(height=500, paper_bgcolor=theme_styles['plot_bg'])
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
            colorbar=dict(title="Valor de Cartera"),
            line=dict(width=2, color='white')
        ),
        textfont=dict(size=12, color='white')
    ))

    fig.update_layout(
        title="",
        height=500,
        font=dict(family="Arial", size=12, color=theme_styles['text_color']),
        plot_bgcolor=theme_styles['plot_bg'],
        paper_bgcolor=theme_styles['plot_bg'],
        margin=dict(t=0, b=0, l=0, r=0)
    )

    return fig


@callback(
    Output('cartera-treemap-cartera-vencida', 'figure'),
    [Input('session-store', 'data'),
     Input('cartera-btn-actualizar', 'n_clicks'),
     Input('cartera-theme-store', 'data')]
)
def update_treemap_vencida(session_data, n_clicks, theme):
    """
    Update overdue portfolio treemap with combined client-company names.
    """
    from utils import get_user_vendor_filter

    vendor_filter = get_user_vendor_filter(session_data)

    data = analyzer.get_treemap_data_vencida(vendor_filter)
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
            font=dict(family="Arial", size=12,
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
            font=dict(family="Arial", size=12,
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
            colorbar=dict(title="Cartera Vencida"),
            line=dict(width=2, color='white')
        ),
        textfont=dict(size=12, color='white')
    ))

    fig.update_layout(
        title="",
        height=500,
        font=dict(family="Arial", size=12, color=theme_styles['text_color']),
        plot_bgcolor=theme_styles['plot_bg'],
        paper_bgcolor=theme_styles['plot_bg'],
        margin=dict(t=0, b=0, l=0, r=0)
    )

    return fig


@callback(
    Output('cartera-top-vencida', 'figure'),
    [Input('session-store', 'data'),
     Input('cartera-btn-actualizar', 'n_clicks'),
     Input('cartera-theme-store', 'data')]
)
def update_top_vencida(session_data, n_clicks, theme):
    """
    Update top overdue customers chart with combined names.
    """
    from utils import get_user_vendor_filter

    vendor_filter = get_user_vendor_filter(session_data)

    data = analyzer.get_top_clientes('vencida', vendor_filter)
    theme_styles = get_theme_styles(theme)

    if data.empty:
        fig = px.bar(title="No hay cartera vencida")
        fig.update_layout(height=400, paper_bgcolor=theme_styles['plot_bg'])
        return fig

    # Create shorter labels for y-axis (just numbers)
    data_sorted = data.sort_values('vencida', ascending=True)
    data_sorted['rank'] = range(1, len(data_sorted) + 1)
    data_sorted['short_label'] = [f"#{i}" for i in data_sorted['rank']]

    fig = px.bar(data_sorted, x='vencida', y='short_label', orientation='h',
                 labels={
                     'vencida': 'Cartera Vencida ($)', 'short_label': 'Top'},
                 color='vencida', color_continuous_scale='Reds')

    # Update format with client names inside bars
    fig.update_traces(
        text=[
            name[:25] + "..." if len(name) > 25 else name for name in data_sorted['cliente_completo']],
        textposition='inside',
        textfont=dict(color='white', size=10),
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
        font=dict(family="Arial", size=12, color=theme_styles['text_color']),
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


@callback(
    Output('cartera-top-sin-vencer', 'figure'),
    [Input('session-store', 'data'),
     Input('cartera-btn-actualizar', 'n_clicks'),
     Input('cartera-theme-store', 'data')]
)
def update_top_sin_vencer(session_data, n_clicks, theme):
    """
    Update top current customers chart with combined names.
    """
    from utils import get_user_vendor_filter

    vendor_filter = get_user_vendor_filter(session_data)

    data = analyzer.get_top_clientes('sin_vencer', vendor_filter)
    theme_styles = get_theme_styles(theme)

    if data.empty:
        fig = px.bar(title="No hay cartera sin vencer")
        fig.update_layout(height=400, paper_bgcolor=theme_styles['plot_bg'])
        return fig

    # Create shorter labels for y-axis (just numbers)
    data_sorted = data.sort_values('sin_vencer', ascending=True)
    data_sorted['rank'] = range(1, len(data_sorted) + 1)
    data_sorted['short_label'] = [f"#{i}" for i in data_sorted['rank']]

    fig = px.bar(data_sorted, x='sin_vencer', y='short_label', orientation='h',
                 labels={
                     'sin_vencer': 'Cartera Sin Vencer ($)', 'short_label': 'Top'},
                 color='sin_vencer', color_continuous_scale='Greens')

    # Update format with client names inside bars
    fig.update_traces(
        text=[
            name[:25] + "..." if len(name) > 25 else name for name in data_sorted['cliente_completo']],
        textposition='inside',
        textfont=dict(color='white', size=10),
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
        font=dict(family="Arial", size=12, color=theme_styles['text_color']),
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


@callback(
    [Output('cartera-grafico-proximos-vencer', 'figure'),
     Output('cartera-tabla-proximos-vencer', 'children')],
    [Input('cartera-slider-dias', 'value'),
     Input('session-store', 'data'),
     Input('cartera-theme-store', 'data')]
)
def update_proximos_vencer(dias, session_data, theme):
    """
    Update upcoming expiration chart with urgency-based colors and proper sorting.
    """
    from utils import get_user_vendor_filter

    vendor_filter = get_user_vendor_filter(session_data)

    data_agrupados = \
        analyzer.get_documentos_agrupados_por_dias(dias, vendor_filter)
    data_documentos_table = \
        analyzer.get_documentos_proximos_vencer(
            dias,
            vendor_filter
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
            font=dict(family="Arial", size=12,
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
        all_days = sorted(data_agrupados['dias_hasta_vencimiento'].unique())

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
                    line=dict(color='white', width=1)
                ),
                hovertemplate="<b>%{fullData.name}</b><br>" +
                "Días hasta vencimiento: %{x}<br>" +
                "%{customdata}<br>" +
                "<extra></extra>",
                customdata=hover_data,
                text=text_data,
                textposition='inside',
                textfont=dict(size=9, color='white', family='Arial'),
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
            font=dict(family="Arial", size=12,
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
                size=11, color=theme_styles['text_color'], family='Arial'),
            bgcolor=theme_styles['paper_color'],
            bordercolor=theme_styles['line_color'],
            borderwidth=1
        )

    # Detailed table grouped by customer
    if data_documentos_table.empty:
        tabla = html.Div([
            html.P("No hay documentos próximos a vencer en este período.",
                   style={'textAlign': 'center', 'color': 'gray', 'fontSize': '16px', 'fontFamily': 'Arial'})
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
                                       'fontFamily': 'Arial'})
                    ])
                )

            # Add document with urgency indicator - FIXED: Red only for 1 day or less
            urgency_emoji = "🔴" if row['dias_hasta_vencimiento'] <= 1 else "🟡" if row['dias_hasta_vencimiento'] <= 7 else "🟢"
            clientes_grupos.append(
                html.Div([
                    html.Div([
                        html.Span(f"{urgency_emoji} Documento: {row['documento_id']}",
                                  style={'fontWeight': 'bold', 'marginRight': '20px', 'fontFamily': 'Arial'}),
                        html.Span(f"Valor: {format_currency_int(row['sin_vencer'])}",
                                  style={'color': '#27AE60', 'marginRight': '20px', 'fontFamily': 'Arial'}),
                        html.Span(f"Vence en: {int(row['dias_hasta_vencimiento'])} días",
                                  style={'color': '#E74C3C', 'fontFamily': 'Arial'}),
                        html.Span(f"Fecha: {row['vencimiento'].strftime('%Y-%m-%d')}",
                                  style={'color': '#7F8C8D', 'marginLeft': '20px', 'fontFamily': 'Arial'})
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

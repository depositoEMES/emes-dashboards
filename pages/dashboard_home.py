from dash import dcc, html

layout = html.Div([
    html.Div([
        # Header con logo izquierda + logout derecha
        html.Div([
            # Logo en la esquina superior izquierda
            html.Div([
                html.Img(
                    src='/assets/logo.png',
                    className="top-left-logo",
                    alt="Logo de la empresa"
                )
            ], className="logo-left-container"),

            # Título centrado (sin logo arriba)
            html.Div([
                html.H1("Panel de Control",
                        className="main-title"),
                html.P("Dashboards de Depósito de Medicamentos Emes S.A.S",
                       className="main-subtitle")
            ], className="center-title-section"),

            # Logout button en la esquina superior derecha
            html.Div([
                html.Button("🚪 Cerrar Sesión", id="logout-button",
                            className="logout-button")
            ], className="logout-right-container")
        ], className="top-header"),

        # Dashboard Cards
        html.Div([
            # Cartera Card
            html.Div([
                html.Span("📊", className="card-icon",
                          style={'color': '#1e3a8a'}),
                html.H3("Dashboard de Cartera", className="card-title"),
                html.P("Análisis completo de cartera, clientes vencidos, rangos de vencimiento y seguimiento de cuentas por cobrar.",
                       className="card-description"),
                dcc.Link("Acceder al Dashboard", href="/cartera",
                         className="card-button")
            ], className="dashboard-card cartera-card"),

            # Ventas Card
            html.Div([
                html.Span("💰", className="card-icon",
                          style={'color': '#3b82f6'}),
                html.H3("Dashboard de Ventas", className="card-title"),
                html.P("Seguimiento de ventas por vendedor, análisis de tendencias, cumplimiento de metas y evolución temporal.",
                       className="card-description"),
                dcc.Link("Acceder al Dashboard", href="/ventas",
                         className="card-button")
            ], className="dashboard-card ventas-card")
        ], className="dashboards-grid"),

        # Stats Section
        html.Div([
            html.H3("📊 Información del Sistema", style={
                    'color': 'white', 'textAlign': 'center', 'marginBottom': '20px'}),
            html.Div([
                html.Div([
                    html.Div("2", className="stat-number"),
                    html.Div("Dashboards", className="stat-label")
                ], className="stat-item"),
                html.Div([
                    html.Div("50+", className="stat-number"),
                    html.Div("Gráficos", className="stat-label")
                ], className="stat-item"),
                html.Div([
                    html.Div("Real-time", className="stat-number"),
                    html.Div("Actualización", className="stat-label")
                ], className="stat-item"),
                html.Div([
                    html.Div("Firebase", className="stat-number"),
                    html.Div("Base de Datos", className="stat-label")
                ], className="stat-item")
            ], className="stats-grid")
        ], className="stats-section")

    ], className="dashboard-container")
])

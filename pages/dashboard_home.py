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
                html.Div([
                    html.H3("Cartera", className="card-title"),
                    html.P("Análisis completo de cuentas por cobrar y seguimiento de clientes.",
                           className="card-description")
                ], className="card-content"),
                html.Div([
                    dcc.Link("Análisis General", href="/cartera",
                             className="card-button primary"),
                ], className="card-actions")
            ], className="dashboard-card cartera-card"),

            # Ventas Card
            html.Div([
                html.Div([
                    html.H3("Ventas", className="card-title"),
                    html.P("Seguimiento de ventas, análisis de tendencias y cumplimiento de metas.",
                           className="card-description")
                ], className="card-content"),
                html.Div([
                    dcc.Link("Vendedores", href="/ventas",
                             className="card-button primary"),
                    dcc.Link("Transferencias", href="/transferencias",
                             className="card-button secondary")
                ], className="card-actions")
            ], className="dashboard-card ventas-card"),

            # Proveedores Card
            html.Div([
                html.Div([
                    html.H3("Proveedores", className="card-title"),
                    html.P("Análisis de relaciones comerciales y gestión de proveedores.",
                           className="card-description")
                ], className="card-content"),
                html.Div([
                    dcc.Link("Ventas", href="/proveedores-ventas",
                             className="card-button primary"),
                    dcc.Link("Compras", href="/proveedores-compras",
                             className="card-button secondary")
                ], className="card-actions")
            ], className="dashboard-card proveedores-card"),
        ], className="dashboards-grid"),

        # Stats Section
        html.Div([
            html.H3("📊 Información del Sistema", style={
                    'color': 'white', 'textAlign': 'center', 'marginBottom': '20px'}),
            html.Div([
                html.Div([
                    html.Div("4", className="stat-number"),
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

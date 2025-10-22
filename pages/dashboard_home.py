from dash import dcc, html, Input, Output, callback
import dash

# Layout base que se renderizará dinámicamente
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
        ], className="top-header-home"),

        # Dashboard Cards - Se renderizará dinámicamente
        html.Div(id="dashboards-grid", className="dashboards-grid"),

        # Stats Section
        html.Div([
            html.H3("📊 Información del Sistema", style={
                    'color': 'white', 'textAlign': 'center', 'marginBottom': '20px'}),
            html.Div(id="stats-grid", className="stats-grid")
        ], className="stats-section")

    ], className="dashboard-container")
])


def create_cartera_card():
    """
    Crear card de Cartera.
    """
    return html.Div([
        html.Div([
            html.H3("Cartera", className="card-title"),
            html.P("Análisis completo de cuentas por cobrar y seguimiento de clientes.",
                   className="card-description")
        ], className="card-content"),
        html.Div([
            dcc.Link("Análisis General", href="/cartera",
                     className="card-button primary"),
        ], className="card-actions")
    ], className="dashboard-card cartera-card")


def create_ventas_card():
    """
    Crear card de Ventas.
    """
    return html.Div([
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
    ], className="dashboard-card ventas-card")


def create_facturas_card():
    """
    Crear card de Facturas.
    """
    return html.Div([
        html.Div([
            html.H3("Facturas", className="card-title"),
            html.P("Gestión y análisis de facturas de proveedores y clientes con seguimiento de órdenes.",
                   className="card-description")
        ], className="card-content"),
        html.Div([
            dcc.Link("Proveedores", href="/facturas/proveedores",
                     className="card-button primary"),
            dcc.Link("Clientes", href="/facturas/clientes",
                     className="card-button secondary")
        ], className="card-actions")
    ], className="dashboard-card facturas-card")


def create_cotizaciones_card():
    """
    Crear card de Cotizaciones IA.
    """
    return html.Div([
        html.Div([
            html.H3("Cotizador IA", className="card-title"),
            html.P("Agente inteligente para cotizaciones rápidas con chat conversacional y generación automática de Excel.",
                   className="card-description")
        ], className="card-content"),
        html.Div([
            dcc.Link("💬 Chat IA", href="/cotizaciones",
                     className="card-button primary"),
            dcc.Link("📊 Reportes", href="/cotizaciones/reportes",
                     className="card-button secondary")
        ], className="card-actions")
    ], className="dashboard-card cotizaciones-ia-card")


def create_proveedores_card():
    """
    Crear card de Proveedores.
    """
    return html.Div([
        html.Div([
            html.H3("Proveedores", className="card-title"),
            html.P("Análisis de relaciones comerciales y gestión de proveedores.",
                   className="card-description")
        ], className="card-content"),
        html.Div([
            dcc.Link("Ventas", href="/proveedores-ventas",
                     className="card-button primary"),
            # dcc.Link("Compras", href="/proveedores-compras",
            #          className="card-button secondary")
        ], className="card-actions")
    ], className="dashboard-card proveedores-card")


def create_administrativo_card():
    """
    Crear card de Administrativo.
    """
    return html.Div([
        html.Div([
            html.H3("Administrativo", className="card-title"),
            html.P("Gestión administrativa, convenios, pedidos, recibos y seguimiento.",
                   className="card-description")
        ], className="card-content"),
        html.Div([
            dcc.Link("Consultas", href="/administrativo/consultas",
                     className="card-button primary"),
            dcc.Link("Convenios", href="/administrativo/convenios",
                     className="card-button secondary")
        ], className="card-actions")
    ], className="dashboard-card administrativo-card")


@callback(
    Output('dashboards-grid', 'children'),
    [Input('session-store', 'data')]
)
def filter_accessible_dashboards(session_data):
    """
    Filtrar y mostrar solo los dashboards a los que el usuario tiene acceso
    """
    try:
        if not session_data:
            return [
                html.Div([
                    html.H3("⚠️ Error de Sesión", style={
                            'color': '#e74c3c', 'textAlign': 'center'}),
                    html.P("No se pudieron cargar los datos de sesión.",
                           style={'textAlign': 'center'})
                ])
            ]

        # Importar aquí para evitar importaciones circulares
        from server import get_db, PermissionManager

        db = get_db()

        if not db:
            return [
                html.Div([
                    html.H3("⚠️ Error de Conexión", style={
                            'color': '#e74c3c', 'textAlign': 'center'}),
                    html.P("No se pudo conectar a la base de datos.",
                           style={'textAlign': 'center'})
                ])
            ]

        permission_manager = PermissionManager(db)
        accessible_dashboards = \
            permission_manager.get_accessible_dashboards(session_data)

        dashboard_cards = []

        # Mapeo de dashboards a funciones de creación de cards
        dashboard_map = {
            'cartera': create_cartera_card,
            'ventas': create_ventas_card,
            'facturas': create_facturas_card,
            'cotizador': create_cotizaciones_card,
            'proveedores': create_proveedores_card,
            'administrativo': create_administrativo_card
        }

        # Crear cards solo para dashboards accesibles
        for dashboard_name in accessible_dashboards:
            if dashboard_name in dashboard_map:
                dashboard_cards.append(dashboard_map[dashboard_name]())

        # Si no tiene acceso a ningún dashboard
        if not dashboard_cards:
            dashboard_cards = [
                html.Div([
                    html.Div([
                        html.H3("🚫 Sin Acceso", className="card-title",
                                style={'color': '#e74c3c'}),
                        html.P("No tienes permisos para acceder a ningún dashboard. Contacta al administrador.",
                               className="card-description", style={'color': '#7f8c8d'})
                    ], className="card-content"),
                ], className="dashboard-card", style={
                    'backgroundColor': '#f8f9fa',
                    'border': '2px dashed #e9ecef',
                    'textAlign': 'center'
                })
            ]

        return dashboard_cards

    except Exception as e:
        print(f"❌ Error en filter_accessible_dashboards: {e}")
        return [
            html.Div([
                html.H3("⚠️ Error", style={
                        'color': '#e74c3c', 'textAlign': 'center'}),
                html.P(f"Error cargando dashboards: {str(e)}", style={
                       'textAlign': 'center'})
            ])
        ]


@callback(
    Output('stats-grid', 'children'),
    [Input('session-store', 'data')]
)
def update_stats_section(session_data):
    """
    Actualizar la sección de estadísticas basada en los permisos del usuario
    """
    try:
        if not session_data:
            return []

        from server import get_db, PermissionManager

        db = get_db()
        if not db:
            return []

        permission_manager = PermissionManager(db)
        accessible_dashboards = permission_manager.get_accessible_dashboards(
            session_data)

        # Contar dashboards accesibles
        total_dashboards = len(accessible_dashboards)

        # Estadísticas dinámicas basadas en permisos
        stats = [
            html.Div([
                html.Div(str(total_dashboards), className="stat-number"),
                html.Div("Dashboards", className="stat-label")
            ], className="stat-item"),
            html.Div([
                html.Div("Real-time", className="stat-number"),
                html.Div("Actualización", className="stat-label")
            ], className="stat-item"),
            html.Div([
                html.Div("Firebase", className="stat-number"),
                html.Div("Base de Datos", className="stat-label")
            ], className="stat-item")
        ]

        # Agregar estadística adicional si tiene acceso a múltiples dashboards
        if total_dashboards > 2:
            stats.append(
                html.Div([
                    html.Div("Multi-role", className="stat-number"),
                    html.Div("Usuario", className="stat-label")
                ], className="stat-item")
            )
        else:
            stats.append(
                html.Div([
                    html.Div("Seguro", className="stat-number"),
                    html.Div("Sistema", className="stat-label")
                ], className="stat-item")
            )

        return stats

    except Exception as e:
        print(f"❌ Error en update_stats_section: {e}")
        return [
            html.Div([
                html.Div("Error", className="stat-number"),
                html.Div("Cargando Stats", className="stat-label")
            ], className="stat-item")
        ]


# Callback adicional para manejar información del usuario en tiempo real
@callback(
    Output('center-title-section', 'children'),
    [Input('session-store', 'data')]
)
def update_user_welcome(session_data):
    """
    Actualizar el título con información personalizada del usuario
    """
    try:
        if session_data and session_data.get('full_name'):
            user_name = session_data.get('full_name', 'Usuario')
            return [
                html.H1("Panel de Control", className="main-title"),
                html.P(f"Bienvenido, {user_name}",
                       className="main-subtitle",
                       style={'fontSize': '16px', 'fontWeight': 'bold', 'color': '#2c3e50'}),
                html.P("Dashboards de Depósito de Medicamentos Emes S.A.S",
                       className="main-subtitle")
            ]
        else:
            return [
                html.H1("Panel de Control", className="main-title"),
                html.P("Dashboards de Depósito de Medicamentos Emes S.A.S",
                       className="main-subtitle")
            ]
    except Exception as e:
        print(f"❌ Error en update_user_welcome: {e}")
        return [
            html.H1("Panel de Control", className="main-title"),
            html.P("Dashboards de Depósito de Medicamentos Emes S.A.S",
                   className="main-subtitle")
        ]

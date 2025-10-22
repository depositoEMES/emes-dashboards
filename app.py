import os
import dash
from dash import html, dcc, Input, Output, State, callback
import traceback

external_stylesheets = [
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap',
    'https://cdnjs.cloudflare.com/ajax/libs/react-datepicker/4.8.0/react-datepicker.min.css'
]

app = dash.Dash(__name__, suppress_callback_exceptions=True,
                external_stylesheets=external_stylesheets)
app.title = "Depósito de Medicamentos Emes S.A.S"

server = app.server

server.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=28800,  # 8 horas
)

# Importar paginas
try:
    from pages import (
        login,
        dashboard_home,
        cartera,
        ventas,
        transferencias,
        # cotizaciones,
        proveedores_ventas,
        # proveedores_compras,
        # facturas,
        # facturas_proveedores
    )
except Exception as e:
    print(f"❌ Error importando páginas: {e}")
    traceback.print_exc()

# Importar componentes de permisos
try:
    from components.permission_modal import create_permission_denied_modal
    from server import PermissionManager
except Exception as e:
    print(f"❌ Error importando componentes de permisos: {e}")
    traceback.print_exc()

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='session-store', storage_type='session'),
    dcc.Store(id='permission-store', storage_type='memory'),
    html.Div(id='page-content')
])


def get_permission_manager():
    """
    Helper para obtener el gestor de permisos con manejo de errores
    """
    try:
        from server import get_db

        db = get_db()

        if db:
            return PermissionManager(db)
        else:
            print("❌ No se pudo obtener conexión a la base de datos")
            return None

    except Exception as e:
        print(f"❌ Error obteniendo PermissionManager: {e}")
        return None


@callback(
    [Output('page-content', 'children'),
     Output('permission-store', 'data')],
    [Input('url', 'pathname')],
    [State('session-store', 'data')]
)
def display_page(pathname, session_data):
    """
    Callback principal para mostrar páginas con verificación de permisos
    """
    try:
        # Verificar autenticación
        authenticated = session_data is not None

        # Rutas públicas - no requieren autenticación
        if pathname in ['/', '/login']:
            if authenticated and pathname == '/':
                return dashboard_home.layout, {'has_permission': True}
            else:
                return login.layout, {'has_permission': True}

        # Todas las demás rutas requieren autenticación
        if not authenticated:
            print("❌ Usuario no autenticado, redirigiendo a login")
            return login.layout, {'has_permission': False}

        # Obtener gestor de permisos
        permission_manager = get_permission_manager()
        if not permission_manager:
            error_page = create_error_page("Error de conexión",
                                           "No se pudo conectar al sistema de permisos.")
            return error_page, {'has_permission': False}

        # Mapeo de rutas a permisos requeridos
        route_permissions = {
            '/dashboard': None,  # Dashboard principal - siempre accesible si está autenticado
            '/cartera': 'cartera',
            '/ventas': 'ventas',
            '/transferencias': 'ventas',  # Transferencias usa permisos de ventas
            '/cotizaciones': 'cotizador',
            '/cotizaciones/reportes': 'cotizador',
            '/proveedores': 'proveedores',
            '/proveedores-ventas': 'proveedores',
            '/proveedores-compras': 'proveedores',
            '/facturas': 'facturas',
            '/facturas/proveedores': 'facturas',
            '/facturas/clientes': 'facturas'
        }

        # Verificar si la ruta existe
        if pathname not in route_permissions:
            print(f"❌ Ruta no encontrada: {pathname}")
            not_found_page = create_not_found_page()
            return not_found_page, {'has_permission': False}

        # Dashboard principal - siempre accesible
        if pathname == '/dashboard':
            return dashboard_home.layout, {'has_permission': True}

        # Verificar permisos para rutas específicas
        required_permission = route_permissions[pathname]

        if required_permission:
            has_permission = permission_manager.check_dashboard_permission(
                session_data, required_permission
            )

            if not has_permission:
                print(f"❌ Sin permisos para {pathname}")
                permission_denied_page = create_permission_denied_modal()
                return permission_denied_page, {'has_permission': False}

        # Cargar la página correspondiente
        page_content = load_page_content(pathname)

        if page_content:
            return page_content, {'has_permission': True}
        else:
            print(f"❌ Error cargando página: {pathname}")
            error_page = create_error_page(
                "Error", f"No se pudo cargar la página {pathname}")
            return error_page, {'has_permission': False}

    except Exception as e:
        print(f"❌ Error en display_page: {e}")
        traceback.print_exc()
        error_page = create_error_page("Error del Sistema",
                                       f"Error interno: {str(e)}")
        return error_page, {'has_permission': False}


def load_page_content(pathname):
    """
    Cargar el contenido de la página según la ruta
    """
    try:
        page_map = {
            '/cartera': cartera.layout,
            '/ventas': ventas.layout,
            '/transferencias': transferencias.layout,  # transferencias.layout,
            # cotizaciones.layout,
            '/cotizaciones': create_coming_soon_page("Cotizaciones"),
            '/cotizaciones/reportes': create_coming_soon_page("Reportes de Cotizaciones"),
            '/proveedores': create_coming_soon_page("Proveedores"),
            # proveedores_ventas.layout,
            '/proveedores-ventas': proveedores_ventas.layout,
            # proveedores_compras.layout,
            '/proveedores-compras': create_coming_soon_page("Proveedores Compras"),
            # facturas.layout,
            '/facturas': create_coming_soon_page("Facturas"),
            # facturas_proveedores.layout,
            '/facturas/proveedores': create_coming_soon_page("Facturas Proveedores"),
            '/facturas/clientes': create_coming_soon_page("Facturas de Clientes"),
        }

        return page_map.get(pathname)

    except Exception as e:
        print(f"❌ Error cargando contenido de página {pathname}: {e}")
        return None


def create_permission_denied_page():
    """
    Crear página de permisos denegados con opción de volver
    """
    return html.Div([
        html.Div([
            html.Div([
                html.Span("🚫", style={
                    'fontSize': '80px',
                    'marginBottom': '30px',
                    'display': 'block'
                }),
                html.H1("Acceso Denegado", style={
                    'color': '#e74c3c',
                    'marginBottom': '20px',
                    'fontFamily': 'Inter',
                    'fontSize': '2.5rem'
                }),
                html.P("No tienes permisos para acceder a esta página.", style={
                    'color': '#7f8c8d',
                    'marginBottom': '30px',
                    'fontFamily': 'Inter',
                    'fontSize': '1.2rem'
                }),
                html.P("Contacta al administrador si crees que esto es un error.", style={
                    'color': '#95a5a6',
                    'marginBottom': '40px',
                    'fontFamily': 'Inter',
                    'fontSize': '1rem'
                }),
                html.Div([
                    dcc.Link("← Volver al Dashboard",
                             href="/dashboard",
                             style={
                                 'backgroundColor': '#3498db',
                                 'color': 'white',
                                 'padding': '15px 30px',
                                 'borderRadius': '8px',
                                 'textDecoration': 'none',
                                 'fontFamily': 'Inter',
                                 'fontWeight': 'bold',
                                 'fontSize': '1.1rem',
                                 'display': 'inline-block',
                                 'transition': 'all 0.3s ease'
                             }),
                    html.Button("🔄 Actualizar Página",
                                id="refresh-page-btn",
                                style={
                                   'backgroundColor': '#95a5a6',
                                   'color': 'white',
                                   'border': 'none',
                                   'padding': '15px 30px',
                                   'borderRadius': '8px',
                                   'cursor': 'pointer',
                                   'fontFamily': 'Inter',
                                   'fontWeight': 'bold',
                                   'fontSize': '1.1rem',
                                   'marginLeft': '20px',
                                   'transition': 'all 0.3s ease'
                                })
                ], style={'textAlign': 'center'})
            ], style={
                'textAlign': 'center',
                'padding': '60px 40px',
                'backgroundColor': 'white',
                'borderRadius': '16px',
                'boxShadow': '0 20px 60px rgba(0,0,0,0.1)',
                'maxWidth': '600px',
                'margin': '0 auto'
            })
        ], style={
            'minHeight': '100vh',
            'backgroundColor': '#f8f9fa',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'padding': '20px'
        })
    ])


def create_error_page(title, message):
    """
    Crear página de error genérica
    """
    return html.Div([
        html.Div([
            html.Div([
                html.Span("⚠️", style={
                    'fontSize': '80px',
                    'marginBottom': '30px',
                    'display': 'block'
                }),
                html.H1(title, style={
                    'color': '#e74c3c',
                    'marginBottom': '20px',
                    'fontFamily': 'Inter',
                    'fontSize': '2.5rem'
                }),
                html.P(message, style={
                    'color': '#7f8c8d',
                    'marginBottom': '40px',
                    'fontFamily': 'Inter',
                    'fontSize': '1.2rem'
                }),
                dcc.Link("← Volver al Dashboard",
                         href="/dashboard",
                         style={
                             'backgroundColor': '#3498db',
                             'color': 'white',
                             'padding': '15px 30px',
                             'borderRadius': '8px',
                             'textDecoration': 'none',
                             'fontFamily': 'Inter',
                             'fontWeight': 'bold',
                             'fontSize': '1.1rem'
                         })
            ], style={
                'textAlign': 'center',
                'padding': '60px 40px',
                'backgroundColor': 'white',
                'borderRadius': '16px',
                'boxShadow': '0 20px 60px rgba(0,0,0,0.1)',
                'maxWidth': '600px',
                'margin': '0 auto'
            })
        ], style={
            'minHeight': '100vh',
            'backgroundColor': '#f8f9fa',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'padding': '20px'
        })
    ])


def create_not_found_page():
    """
    Crear página 404
    """
    return html.Div([
        html.Div([
            html.Div([
                html.H1("404", style={
                    'fontSize': '120px',
                    'color': '#3498db',
                    'margin': '0',
                    'fontFamily': 'Inter',
                    'fontWeight': 'bold'
                }),
                html.H2("Página no encontrada", style={
                    'color': '#2c3e50',
                    'marginBottom': '20px',
                    'fontFamily': 'Inter'
                }),
                html.P("La página que buscas no existe o ha sido movida.", style={
                    'color': '#7f8c8d',
                    'marginBottom': '40px',
                    'fontFamily': 'Inter',
                    'fontSize': '1.2rem'
                }),
                dcc.Link("← Volver al Dashboard",
                         href="/dashboard",
                         style={
                             'backgroundColor': '#3498db',
                             'color': 'white',
                             'padding': '15px 30px',
                             'borderRadius': '8px',
                             'textDecoration': 'none',
                             'fontFamily': 'Inter',
                             'fontWeight': 'bold',
                             'fontSize': '1.1rem'
                         })
            ], style={
                'textAlign': 'center',
                'padding': '60px 40px',
                'backgroundColor': 'white',
                'borderRadius': '16px',
                'boxShadow': '0 20px 60px rgba(0,0,0,0.1)',
                'maxWidth': '600px',
                'margin': '0 auto'
            })
        ], style={
            'minHeight': '100vh',
            'backgroundColor': '#f8f9fa',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'padding': '20px'
        })
    ])


def create_coming_soon_page(feature_name):
    """
    Crear página "Próximamente" para funcionalidades en desarrollo
    """
    return html.Div([
        html.Div([
            html.Div([
                html.Span("🚧", style={
                    'fontSize': '80px',
                    'marginBottom': '30px',
                    'display': 'block'
                }),
                html.H1(f"{feature_name}", style={
                    'color': '#f39c12',
                    'marginBottom': '20px',
                    'fontFamily': 'Inter',
                    'fontSize': '2.5rem'
                }),
                html.P("Esta funcionalidad está en desarrollo.", style={
                    'color': '#7f8c8d',
                    'marginBottom': '20px',
                    'fontFamily': 'Inter',
                    'fontSize': '1.2rem'
                }),
                html.P("Estará disponible próximamente.", style={
                    'color': '#95a5a6',
                    'marginBottom': '40px',
                    'fontFamily': 'Inter',
                    'fontSize': '1rem'
                }),
                dcc.Link("← Volver al Dashboard",
                         href="/dashboard",
                         style={
                             'backgroundColor': '#f39c12',
                             'color': 'white',
                             'padding': '15px 30px',
                             'borderRadius': '8px',
                             'textDecoration': 'none',
                             'fontFamily': 'Inter',
                             'fontWeight': 'bold',
                             'fontSize': '1.1rem'
                         })
            ], style={
                'textAlign': 'center',
                'padding': '60px 40px',
                'backgroundColor': 'white',
                'borderRadius': '16px',
                'boxShadow': '0 20px 60px rgba(0,0,0,0.1)',
                'maxWidth': '600px',
                'margin': '0 auto'
            })
        ], style={
            'minHeight': '100vh',
            'backgroundColor': '#f8f9fa',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'padding': '20px'
        })
    ])


@callback(
    [Output('session-store', 'data', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],
    [Input('logout-button', 'n_clicks')],
    prevent_initial_call=True
)
def logout_user(n_clicks):
    """
    Manejar logout del usuario
    """
    if n_clicks:
        return None, '/login'
    return dash.no_update, dash.no_update


@callback(
    Output('url', 'pathname', allow_duplicate=True),
    [Input('refresh-page-btn', 'n_clicks')],
    [State('url', 'pathname')],
    prevent_initial_call=True
)
def refresh_current_page(n_clicks, current_pathname):
    """
    Refrescar página actual (para botón de actualizar en página de permisos denegados)
    """
    if n_clicks:
        return current_pathname

    return dash.no_update


# Callback para manejar errores globales de la aplicación
@app.server.errorhandler(404)
def not_found(error):
    """
    Manejar errores 404 a nivel de servidor
    """
    return create_not_found_page(), 404


@app.server.errorhandler(500)
def internal_error(error):
    """
    Manejar errores 500 a nivel de servidor
    """
    return create_error_page("Error del Servidor",
                             "Ha ocurrido un error interno del servidor."), 500


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', debug=False)

    except Exception as e:
        print(f"❌ Error iniciando aplicación: {e}")
        traceback.print_exc()

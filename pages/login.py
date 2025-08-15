# login_page.py
import dash
from dash import dcc, html, Input, Output, State, callback
from server import AuthManager

auth_manager = AuthManager()

layout = html.Div([
    html.Div([
        html.Div([
            html.Div(className="shape"),
            html.Div(className="shape"),
            html.Div(className="shape"),
        ], className="floating-shapes"),

        html.Div([
            # Logo y header
            html.Div([
                # LOGO - Se carga automáticamente desde assets/
                html.Img(
                    src='/assets/logo.png',  # Dash sirve automáticamente desde assets/
                    className="company-logo",
                    alt="Logo de la empresa"
                ),
                html.H1("Bienvenido", className="login-title"),
                html.P("Sistema de Dashboards Corporativo",
                       className="login-subtitle")
            ], className="login-header"),

            # Formulario
            html.Div([
                html.Div([
                    html.Span("👤", className="input-icon"),
                    dcc.Input(
                        id='login-username',
                        placeholder='Usuario',
                        type='text',
                        className='login-input'
                    )
                ], className="input-group"),

                html.Div([
                    html.Span("🔒", className="input-icon"),
                    dcc.Input(
                        id='login-password',
                        placeholder='Contraseña',
                        type='password',
                        className='login-input'
                    )
                ], className="input-group"),

                html.Button(
                    'Acceder al Sistema',
                    id='login-button',
                    n_clicks=0,
                    className='login-button'
                ),

                html.Div(id='login-message', className='login-message'),
                dcc.Store(id='login-validation-store')
            ])
        ], className="login-card")
    ], className="login-container")
])


@callback(
    [Output('login-message', 'children'),
     Output('login-message', 'className'),
     Output('url', 'pathname', allow_duplicate=True),
     Output('session-store', 'data', allow_duplicate=True)],
    [Input('login-button', 'n_clicks')],
    [State('login-username', 'value'),
     State('login-password', 'value')],
    prevent_initial_call=True
)
def authenticate_user(n_clicks, username, password):
    if n_clicks > 0:
        if not username or not password:
            return (
                "⚠️ Por favor ingresa usuario y contraseña",
                "login-message message-error",
                dash.no_update,
                dash.no_update                    # No cambiar sesión
            )

        is_valid, user_info = auth_manager.validate_user(username, password)

        if is_valid:
            print(f"✅ Login exitoso - Guardando sesión: {user_info}")
            return (
                f"✅ Bienvenido {user_info['full_name']}",
                "login-message message-success",
                "/dashboard",                     # Cambiar URL
                user_info                         # Guardar sesión
            )
        else:
            return (
                "❌ Credenciales incorrectas",
                "login-message message-error",
                dash.no_update,
                dash.no_update                    # No cambiar sesión
            )

    return "", "login-message", dash.no_update, dash.no_update

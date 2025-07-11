import os
import dash
from dash import html, dcc, Input, Output, State, callback

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Depósito de Medicamentos Emes S.A.S"

server = app.server

# Importar paginas
try:
    from pages import login, dashboard_home, cartera, ventas, transferencias, proveedores
except Exception as e:
    print(f"❌ Error importando login_page: {e}")


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='session-store', storage_type='session'),
    html.Div(id='page-content')
])


@callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')],
    [State('session-store', 'data')]
)
def display_page(pathname, session_data):
    # Verificar autenticación
    authenticated = session_data is not None

    # Rutas públicas
    if pathname == '/login' or pathname == '/':
        if authenticated and pathname == '/':
            return dashboard_home.layout
        else:
            print("❌ Usuario no autenticado, mostrando login")
            return login.layout

    # Rutas protegidas
    if not authenticated:
        print("❌ Ruta protegida sin autenticación, redirigiendo a login")
        return login.layout

    if pathname == '/dashboard':
        return dashboard_home.layout
    elif pathname == '/cartera':
        return cartera.layout
    elif pathname == '/ventas':
        return ventas.layout
    elif pathname == '/transferencias':
        return transferencias.layout
    elif pathname == '/proveedores':
        return proveedores.layout
    else:
        return html.Div([
            html.H1("Página no encontrada"),
            dcc.Link("Volver al inicio", href="/dashboard")
        ])


@callback(
    [Output('session-store', 'data'),
     Output('url', 'pathname')],
    [Input('logout-button', 'n_clicks')],
    prevent_initial_call=True
)
def logout_user(n_clicks):
    if n_clicks:
        return None, '/login'
    return dash.no_update, dash.no_update


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    app.run(host='0.0.0.0', port=port, debug=False)

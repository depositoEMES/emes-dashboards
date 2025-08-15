from dash import html, dcc


def create_permission_denied_modal():
    return html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.Span(
                        "🚫", style={'fontSize': '48px', 'marginBottom': '20px'}),
                    html.H2("Acceso Denegado", style={
                        'color': '#e74c3c',
                        'marginBottom': '15px',
                        'fontFamily': 'Inter'
                    }),
                    html.P("No tienes permisos para acceder a esta página.", style={
                        'color': '#7f8c8d',
                        'marginBottom': '25px',
                        'fontFamily': 'Inter'
                    }),
                    html.Button("Volver al Dashboard",
                                id="modal-back-button",
                                style={
                                   'backgroundColor': '#3498db',
                                   'color': 'white',
                                   'border': 'none',
                                   'padding': '12px 24px',
                                   'borderRadius': '8px',
                                   'cursor': 'pointer',
                                   'fontFamily': 'Inter'
                                })
                ], style={
                    'textAlign': 'center',
                    'padding': '40px'
                })
            ], style={
                'backgroundColor': 'white',
                'borderRadius': '12px',
                'maxWidth': '400px',
                'margin': '0 auto',
                'boxShadow': '0 10px 30px rgba(0,0,0,0.3)'
            })
        ], style={
            'position': 'fixed',
            'top': '0',
            'left': '0',
            'width': '100%',
            'height': '100%',
            'backgroundColor': 'rgba(0,0,0,0.5)',
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'zIndex': '9999'
        })
    ], id='permission-denied-modal')

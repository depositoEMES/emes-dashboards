import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
from datetime import datetime, timedelta

from utils import format_currency_int

# Importar el procesador
try:
    from analyzers import FacturasProveedoresAnalyzer
    print("✅ FacturasProveedoresAnalyzer importado correctamente")
except ImportError as e:
    print(f"❌ Error importando FacturasProveedoresAnalyzer: {e}")
    FacturasProveedoresAnalyzer = None

def get_theme_styles(is_dark=False):
    """Obtener estilos según el tema seleccionado"""
    if is_dark:
        return {
            'background': 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)',
            'text_primary': '#f8fafc',
            'text_secondary': '#e2e8f0',
            'text_muted': '#94a3b8',
            'card_bg': 'rgba(30, 41, 59, 0.8)',
            'card_border': 'rgba(148, 163, 184, 0.2)',
            'table_bg': 'rgba(30, 41, 59, 0.8)',
            'table_bg_alt': 'rgba(51, 65, 85, 0.8)',
            'input_bg': 'rgba(30, 41, 59, 0.8)',
            'input_border': '#475569'
        }
    else:
        return {
            'background': 'linear-gradient(135deg, #f9fafb 0%, #eff6ff 100%)',
            'text_primary': '#111827',
            'text_secondary': '#374151',
            'text_muted': '#6b7280',
            'card_bg': '#ffffff',
            'card_border': '#e5e7eb',
            'table_bg': '#ffffff',
            'table_bg_alt': '#f8fafc',
            'input_bg': '#ffffff',
            'input_border': '#d1d5db'
        }

layout = html.Div([
    # Store para el tema
    dcc.Store(id='theme-store', data={'is_dark': False}),
    
    # Div interno para el contenido con margen
    html.Div([
        # Header de la página con toggle de tema
        html.Div([
            html.Div([
                html.H1("📦 Facturas de Proveedores",
                        style={
                            'fontSize': '32px',
                            'fontWeight': '700',
                            'margin': '0',
                            'textAlign': 'center'
                        }),
                
                # Toggle de tema
                html.Div([
                    html.Button(
                        "🌙",
                        id="theme-toggle",
                        title="Cambiar tema",
                        style={
                            'background': 'transparent',
                            'border': '2px solid rgba(255, 255, 255, 0.3)',
                            'borderRadius': '50%',
                            'width': '40px',
                            'height': '40px',
                            'fontSize': '18px',
                            'cursor': 'pointer',
                            'transition': 'all 0.3s ease',
                            'display': 'flex',
                            'alignItems': 'center',
                            'justifyContent': 'center'
                        }
                    )
                ], style={
                    'position': 'absolute',
                    'top': '20px',
                    'right': '20px'
                })
            ], style={'position': 'relative'})
        ], id='header-container', style={
            'borderRadius': '16px',
            'padding': '32px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'position': 'relative'
        }),

        # Controles superiores
        html.Div([
            # Filtro de proveedor
            html.Div([
                html.Label("Filtrar por Proveedor:",
                           style={
                               'fontWeight': '600',
                               'fontSize': '14px',
                               'marginBottom': '8px',
                               'display': 'block'
                           }),
                dcc.Dropdown(
                    id='proveedor-filter',
                    placeholder="Seleccionar proveedor...",
                    clearable=True,
                    style={
                        'height': '44px',
                        'borderRadius': '12px',
                        'fontSize': '14px'
                    }
                )
            ], style={
                'display': 'flex',
                'flexDirection': 'column',
                'flex': '1',
                'minWidth': '250px'
            }),

            # Selector de fechas
            html.Div([
                html.Label("Rango de Fechas:",
                           style={
                               'fontWeight': '600',
                               'fontSize': '14px',
                               'marginBottom': '8px',
                               'display': 'block'
                           }),
                html.Div([
                    dcc.DatePickerRange(
                        id='date-range-picker',
                        start_date=datetime.now().replace(day=1).date(),
                        end_date=datetime.now().date(),
                        display_format='DD/MM/YYYY',
                        clearable=True,
                        with_portal=True,
                        style={
                            'width': '100%',
                            'height': '44px'
                        }
                    )
                ], style={
                    'width': '100%',
                    'height': '44px'
                })
            ], style={
                'display': 'flex',
                'flexDirection': 'column',
                'flex': '1',
                'minWidth': '250px'
            })
        ], id='controls-container', style={
            'display': 'flex',
            'gap': '24px',
            'alignItems': 'stretch',
            'borderRadius': '16px',
            'padding': '24px',
            'marginBottom': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'flexWrap': 'wrap'
        }),

        # Métricas resumidas
        html.Div(id="metrics-cards", children=[], style={'marginBottom': '24px'}),

        # Tabla principal
        html.Div([
            html.Div([
                html.Div([
                    html.H3("📋 Detalle de Facturas",
                            style={
                                'fontSize': '20px',
                                'fontWeight': '700',
                                'margin': '0'
                            }),
                    html.Div(id="table-info",
                             style={
                                'fontSize': '14px',
                                'fontWeight': '500'
                             })
                ], style={
                    'display': 'flex',
                    'justifyContent': 'space-between',
                    'alignItems': 'center',
                    'marginBottom': '16px',
                    'flexWrap': 'wrap',
                    'gap': '12px'
                }),
                
                # Botón de generar nota
                html.Div([
                    html.Button([
                        "📝 Generar Nota"
                    ],
                    id="change-state-button",
                    title="Generar Nota para Facturas Seleccionadas",
                    style={
                        'background': 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                        'color': '#ffffff',
                        'border': 'none',
                        'padding': '12px 24px',
                        'borderRadius': '25px',
                        'fontWeight': '600',
                        'fontSize': '14px',
                        'cursor': 'pointer',
                        'boxShadow': '0 4px 14px rgba(16, 185, 129, 0.3)',
                        'transition': 'all 0.3s ease',
                        'display': 'flex',
                        'alignItems': 'center',
                        'minHeight': '44px',
                        'position': 'relative'
                    }),
                    
                    html.Span(
                        id="selected-count-badge",
                        children="0",
                        style={
                            'background': '#ef4444',
                            'color': 'white',
                            'borderRadius': '50%',
                            'width': '20px',
                            'height': '20px',
                            'fontSize': '11px',
                            'fontWeight': '700',
                            'display': 'flex',
                            'alignItems': 'center',
                            'justifyContent': 'center',
                            'position': 'absolute',
                            'top': '-8px',
                            'right': '-8px',
                            'boxShadow': '0 2px 8px rgba(239, 68, 68, 0.4)',
                            'border': '2px solid transparent',
                            'minWidth': '20px'
                        }
                    )
                ], style={
                    'position': 'relative',
                    'display': 'inline-flex',
                    'alignItems': 'center',
                    'marginBottom': '16px',
                    'alignSelf': 'flex-start'
                })
            ]),

            html.Div(id="facturas-table-container", children=[])
        ], id='table-container', style={
            'borderRadius': '16px',
            'padding': '24px',
            'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'width': '100%'
        }),

        # Botón de actualizar
        html.Div([
            html.Button(
                "🔄 Actualizar Datos",
                id="update-button",
                n_clicks=0,
                style={
                    'background': 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
                    'color': '#ffffff',
                    'border': 'none',
                    'padding': '14px 28px',
                    'borderRadius': '25px',
                    'fontWeight': '600',
                    'fontSize': '16px',
                    'cursor': 'pointer',
                    'boxShadow': '0 4px 12px rgba(59, 130, 246, 0.3)',
                    'transition': 'all 0.3s ease'
                }
            )
        ], style={
            'display': 'flex',
            'justifyContent': 'center',
            'marginTop': '32px',
            'marginBottom': '32px'
        }),

        # Modal para detalles de productos
        html.Div(id="product-modal", style={"display": "none"}),
        
        # Modal para cambio de estado
        html.Div(id="state-change-modal", style={"display": "none"}),

        # Store para datos
        dcc.Store(id='processed-data-store'),
        dcc.Store(id='selected-invoices-store', data=[]),
        dcc.Store(id='loading-state', data=False)
        
    ], style={
        # 'maxWidth': '1400px',        # Ancho máximo del contenido
        'margin': '0 auto',          # Centrar horizontalmente
        'padding': '0 40px',         # Margen interno horizontal
    }),
    
], id='main-container', style={
    'width': '100%',                 # Ocupar todo el ancho
    'minHeight': '100vh',
    'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
    'transition': 'all 0.3s ease',
    'padding': '20px 0'             # Padding vertical para el contenedor principal
})


# Callback para cambiar tema
@callback(
    [Output('theme-store', 'data'),
     Output('theme-toggle', 'children'),
     Output('main-container', 'style'),
     Output('header-container', 'style'),
     Output('controls-container', 'style'),
     Output('table-container', 'style')],
    [Input('theme-toggle', 'n_clicks')],
    [State('theme-store', 'data')]
)
def toggle_theme(n_clicks, theme_data):
    if not n_clicks:
        # Tema claro por defecto
        theme = get_theme_styles(False)
        return (
            {'is_dark': False},
            "🌙",
            {'maxWidth': '100%', 'margin': '0 auto', 'padding': '20px', 'minHeight': '100vh',
             'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
             'background': theme['background'], 'color': theme['text_primary'], 'transition': 'all 0.3s ease'},
            {'borderRadius': '16px', 'padding': '32px', 'marginBottom': '24px',
             'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)', 'position': 'relative',
             'background': theme['card_bg'], 'border': f"1px solid {theme['card_border']}",
             'color': theme['text_primary']},
            {'display': 'flex', 'gap': '24px', 'alignItems': 'stretch', 'borderRadius': '16px',
             'padding': '24px', 'marginBottom': '24px', 'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
             'flexWrap': 'wrap', 'background': theme['card_bg'], 'border': f"1px solid {theme['card_border']}",
             'color': theme['text_primary']},
            {'borderRadius': '16px', 'padding': '24px', 'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
             'width': '100%', 'background': theme['card_bg'], 'border': f"1px solid {theme['card_border']}",
             'color': theme['text_primary']}
        )
    
    is_dark = not theme_data.get('is_dark', False)
    theme = get_theme_styles(is_dark)
    icon = "☀️" if is_dark else "🌙"
    
    return (
        {'is_dark': is_dark},
        icon,
        {'maxWidth': '100%', 'margin': '0 auto', 'padding': '20px', 'minHeight': '100vh',
         'fontFamily': 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
         'background': theme['background'], 'color': theme['text_primary'], 'transition': 'all 0.3s ease'},
        {'borderRadius': '16px', 'padding': '32px', 'marginBottom': '24px',
         'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.3)' if is_dark else '0 8px 32px rgba(0, 0, 0, 0.1)',
         'position': 'relative', 'background': theme['card_bg'], 'border': f"1px solid {theme['card_border']}",
         'color': theme['text_primary'], 'backdropFilter': 'blur(10px)' if is_dark else 'none'},
        {'display': 'flex', 'gap': '24px', 'alignItems': 'stretch', 'borderRadius': '16px',
         'padding': '24px', 'marginBottom': '24px', 
         'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.3)' if is_dark else '0 8px 32px rgba(0, 0, 0, 0.1)',
         'flexWrap': 'wrap', 'background': theme['card_bg'], 'border': f"1px solid {theme['card_border']}",
         'color': theme['text_primary'], 'backdropFilter': 'blur(10px)' if is_dark else 'none'},
        {'borderRadius': '16px', 'padding': '24px', 
         'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.3)' if is_dark else '0 8px 32px rgba(0, 0, 0, 0.1)',
         'width': '100%', 'background': theme['card_bg'], 'border': f"1px solid {theme['card_border']}",
         'color': theme['text_primary'], 'backdropFilter': 'blur(10px)' if is_dark else 'none'}
    )


@callback(
    [Output('processed-data-store', 'data'),
     Output('proveedor-filter', 'options')],
    [Input('update-button', 'n_clicks')],
    prevent_initial_call=False
)
def load_and_process_data(update_clicks):
    """Cargar y procesar datos desde Firebase"""
    try:
        processor = FacturasProveedoresAnalyzer()
        supplier_list = processor.get_suppliers_list()
        suppliers = ['Todos'] + supplier_list
        proveedor_options = [{'label': s, 'value': s} for s in suppliers]

        start_date = datetime.now().replace(day=1).date()
        end_date = datetime.now().date()
        date_range = (start_date, end_date)

        processed_data = processor.process_invoices(date_range=date_range)
        return processed_data, proveedor_options

    except Exception as e:
        print(f"Error en load_and_process_data: {e}")
        return {}, []


@callback(
    [Output('metrics-cards', 'children'),
     Output('facturas-table-container', 'children'),
     Output('table-info', 'children')],
    [Input('processed-data-store', 'data'),
     Input('proveedor-filter', 'value'),
     Input('date-range-picker', 'start_date'),
     Input('date-range-picker', 'end_date'),
     Input('theme-store', 'data')]
)
def update_dashboard(processed_data, selected_proveedor, start_date, end_date, theme_data):
    """Actualizar dashboard con filtros automáticos"""
    try:
        processor = FacturasProveedoresAnalyzer()
        is_dark = theme_data.get('is_dark', False)
        
        date_range = None
        if start_date and end_date:
            start_date_obj = datetime.fromisoformat(start_date).date()
            end_date_obj = datetime.fromisoformat(end_date).date()
            date_range = (start_date_obj, end_date_obj)
        else:
            start_date_obj = datetime.now().replace(day=1).date()
            end_date_obj = datetime.now().date()
            date_range = (start_date_obj, end_date_obj)
        
        filtered_data = processor.process_invoices(
            proveedor_filter=selected_proveedor,
            date_range=date_range
        )

        if not filtered_data:
            return (
                create_empty_metrics(is_dark),
                create_no_data_message("No hay datos disponibles para el rango seleccionado", is_dark),
                "Sin datos"
            )

        metrics = create_metrics_cards(filtered_data, is_dark)
        table_data = prepare_table_data(filtered_data)
        table = create_facturas_table(table_data, is_dark)

        table_info = f"Mostrando {len(table_data)} facturas"
        if selected_proveedor:
            table_info += f" de {selected_proveedor}"
        if date_range:
            start_str = date_range[0].strftime("%d/%m/%Y")
            end_str = date_range[1].strftime("%d/%m/%Y")
            table_info += f" (desde {start_str} hasta {end_str})"

        return metrics, table, table_info

    except Exception as e:
        print(f"Error actualizando dashboard: {e}")
        return (
            create_empty_metrics(False),
            create_no_data_message(f"Error: {e}", False),
            f"Error: {e}"
        )


def create_no_data_message(message, is_dark=False):
    """Crear mensaje de no datos"""
    theme = get_theme_styles(is_dark)
    return html.Div(
        message,
        style={
            'textAlign': 'center',
            'padding': '48px',
            'color': theme['text_muted'],
            'fontSize': '16px',
            'background': theme['card_bg'],
            'borderRadius': '12px',
            'border': f"2px dashed {theme['card_border']}"
        }
    )


def create_empty_metrics(is_dark=False):
    """Crear métricas vacías"""
    return html.Div([
        create_metric_card("0", "Total Facturas", "📄", "#3b82f6", is_dark),
        create_metric_card("$0", "Valor Total", "💰", "#10b981", is_dark),
        create_metric_card("$0", "Valor Notas", "📋", "#f59e0b", is_dark),
        create_metric_card("0", "Proveedores", "🏢", "#8b5cf6", is_dark)
    ], style={
        'display': 'grid',
        'gridTemplateColumns': 'repeat(auto-fit, minmax(280px, 1fr))',
        'gap': '20px'
    })


def create_metrics_cards(processed_data, is_dark=False):
    """Crear cards de métricas"""
    if not processed_data:
        return create_empty_metrics(is_dark)

    total_facturas = len(processed_data)
    total_valor_facturas = sum(item.get('valor_factura', 0) for item in processed_data.values())
    total_valor_notas = sum(item.get('valor_nota', 0) for item in processed_data.values())
    proveedores_unicos = len(set(item.get('proveedor', '') for item in processed_data.values()))
    facturas_vencidas = sum(1 for item in processed_data.values() if item.get('dias_vencidos', 0) > 0)

    return html.Div([
        create_metric_card(f"{total_facturas:,}", "Total Facturas", "", "#3b82f6", is_dark),
        create_metric_card(f"{format_currency_int(total_valor_facturas)}", "Valor Total Facturas", "", "#10b981", is_dark),
        create_metric_card(f"{format_currency_int(total_valor_notas)}", "Valor Total Notas", "", "#f59e0b", is_dark),
        create_metric_card(f"{facturas_vencidas:,}", "Facturas Vencidas", "", "#ef4444", is_dark),
        create_metric_card(f"{proveedores_unicos:,}", "Proveedores Únicos", "", "#8b5cf6", is_dark)
    ], style={
        'display': 'grid',
        'gridTemplateColumns': 'repeat(auto-fit, minmax(250px, 1fr))',
        'gap': '20px'
    })


def create_metric_card(number, label, icon, color, is_dark=False):
    """Crear una card de métrica individual"""
    theme = get_theme_styles(is_dark)
    
    return html.Div([
        html.Div(style={
            'position': 'absolute', 'top': '0', 'left': '0', 'right': '0', 'height': '4px',
            'background': color, 'borderRadius': '16px 16px 0 0'
        }),
        html.H3(number, style={
            'fontSize': '28px', 'fontWeight': '800', 'color': theme['text_primary'],
            'margin': '0 0 8px 0', 'textShadow': '0 2px 4px rgba(0, 0, 0, 0.3)' if is_dark else 'none'
        }),
        html.P(label, style={
            'fontSize': '14px', 'color': theme['text_muted'], 'fontWeight': '500', 'margin': '0'
        }),
        html.Div(icon, style={
            'position': 'absolute', 'top': '20px', 'right': '20px', 'fontSize': '24px', 'opacity': '0.7'
        })
    ], style={
        'background': theme['card_bg'],
        'backdropFilter': 'blur(15px)' if is_dark else 'none',
        'WebkitBackdropFilter': 'blur(15px)' if is_dark else 'none',
        'border': f"1px solid {theme['card_border']}",
        'borderRadius': '16px', 'padding': '24px',
        'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.2)' if is_dark else '0 8px 32px rgba(0, 0, 0, 0.1)',
        'position': 'relative', 'overflow': 'hidden', 'transition': 'all 0.3s ease', 'cursor': 'pointer'
    }, className='glass-card')


def get_state_badge_html(state, is_dark=False):
    """Crear badge HTML para estados - ESTA ES LA FUNCIÓN CORRECTA"""
    state_config = {
        1: {"text": "Pendiente", "color": "#fbbf24" if is_dark else "#f59e0b", 
            "bg": "rgba(251, 191, 36, 0.2)" if is_dark else "#fef3c7", 
            "border": "#fbbf24" if is_dark else "#f59e0b"},
        2: {"text": "En Advance", "color": "#60a5fa" if is_dark else "#2563eb", 
            "bg": "rgba(96, 165, 250, 0.2)" if is_dark else "#dbeafe", 
            "border": "#60a5fa" if is_dark else "#2563eb"},
        3: {"text": "Nota Generada", "color": "#34d399" if is_dark else "#059669", 
            "bg": "rgba(52, 211, 153, 0.2)" if is_dark else "#d1fae5", 
            "border": "#34d399" if is_dark else "#059669"},
        4: {"text": "Nota Descargada", "color": "#9ca3af", 
            "bg": "rgba(156, 163, 175, 0.2)" if is_dark else "#f3f4f6", 
            "border": "#9ca3af"}
    }
    
    config = state_config.get(state, state_config[1])
    
    return html.Span(
        config["text"],
        style={
            'backgroundColor': config["bg"],
            'color': config["color"],
            'border': f'1px solid {config["border"]}',
            'borderRadius': '20px',
            'padding': '6px 12px',
            'fontSize': '12px',
            'fontWeight': '600',
            'display': 'inline-block',
            'textAlign': 'center',
            'minWidth': '90px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.3)' if is_dark else '0 1px 2px rgba(0,0,0,0.1)'
        }
    )


def prepare_table_data(processed_data):
    """Preparar datos para la tabla - USANDO BADGES HTML"""
    table_data = []

    for invoice_id, data in processed_data.items():
        dias_vencidos = data.get('dias_vencidos', 0)
        if dias_vencidos > 0:
            estado_vencimiento = f"🔴 Vencida ({dias_vencidos} días)"
        elif dias_vencidos > -7:
            estado_vencimiento = f"🟡 Por vencer ({abs(dias_vencidos)} días)"
        else:
            estado_vencimiento = f"🟢 Al día ({abs(dias_vencidos)} días)"

        table_data.append({
            'Ver': '📄',
            'Factura': data.get('factura', ''),
            'Órdenes de Compra': data.get('orden', ''),
            'Estado': data.get('estado', 1),  # Mantener número para usar en style_data_conditional
            'Proveedor': data.get('proveedor', ''),
            'Valor Factura': f"{format_currency_int(data.get('valor_factura', 0))}",
            'Valor Nota': f"{format_currency_int(data.get('valor_nota', 0))}",
            'Forma pago': data.get('forma_pago', ''),
            'Fecha cargue': data.get('fecha_cargue', 'N/A'),
            'Días desde cargue': str(data.get('dias_cargue', 0)),
            'Fecha vencimiento': data.get('fecha_vcto', 'N/A'),
            'Estado vencimiento': estado_vencimiento
        })

    return table_data

def create_facturas_table(table_data, is_dark=False):
    """Crear tabla moderna con scroll horizontal responsivo y bordes delgados"""
    if not table_data:
        return create_no_data_message("No hay datos para mostrar", is_dark)

    theme = get_theme_styles(is_dark)

    return html.Div([
        # Contenedor con scroll horizontal
        html.Div([
            dash_table.DataTable(
                id='facturas-table',
                data=table_data,
                columns=[
                    {'name': '', 'id': 'Ver', 'type': 'text'},
                    {'name': 'Factura', 'id': 'Factura', 'type': 'text'},
                    {'name': 'Órdenes de Compra', 'id': 'Órdenes de Compra', 'type': 'text'},
                    {'name': 'Estado', 'id': 'Estado', 'type': 'numeric'},
                    {'name': 'Proveedor', 'id': 'Proveedor', 'type': 'text'},
                    {'name': 'Valor Factura', 'id': 'Valor Factura', 'type': 'text'},
                    {'name': 'Valor Nota', 'id': 'Valor Nota', 'type': 'text'},
                    {'name': 'Forma pago', 'id': 'Forma pago', 'type': 'text'},
                    {'name': 'Fecha cargue', 'id': 'Fecha cargue', 'type': 'text'},
                    {'name': 'Días desde cargue', 'id': 'Días desde cargue', 'type': 'numeric'},
                    {'name': 'Fecha vencimiento', 'id': 'Fecha vencimiento', 'type': 'text'},
                    {'name': 'Estado vencimiento', 'id': 'Estado vencimiento', 'type': 'text'}
                ],
                style_table={
                    'overflowX': 'auto',
                    'borderRadius': '12px',
                    'overflow': 'hidden',
                    'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.3)' if is_dark else '0 8px 32px rgba(0, 0, 0, 0.1)',
                    'border': f"1px solid {theme['card_border']}",
                    'width': '100%',
                    'minWidth': '1200px'  # Ancho mínimo para forzar scroll horizontal en móvil
                },
                style_header={
                    'backgroundColor': '#1e40af',  # Azul moderno sin !important
                    'color': '#ffffff',
                    'fontWeight': '600',
                    'textAlign': 'center',
                    'border': 'none',
                    'fontSize': '13px',
                    'padding': '14px 8px',
                    'fontFamily': 'Inter, sans-serif',
                    'borderBottom': 'none'
                },
                style_cell={
                    'textAlign': 'center',
                    'padding': '12px 6px',
                    'border': '0.5px solid rgba(0, 0, 0, 0.1)',  # Borde muy delgado
                    'fontSize': '12px',
                    'fontFamily': 'Inter, sans-serif',
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'minWidth': '80px',
                    'maxWidth': '200px',
                    'textOverflow': 'ellipsis',
                    'backgroundColor': theme['table_bg'],
                    'color': theme['text_secondary']
                },
                style_cell_conditional=[
                    {
                        'if': {'column_id': 'Ver'},
                        'width': '50px',
                        'minWidth': '50px',
                        'maxWidth': '50px',
                        'cursor': 'pointer',
                        'fontSize': '16px'
                    },
                    {
                        'if': {'column_id': 'Estado'},
                        'width': '120px',
                        'minWidth': '120px'
                    },
                    {
                        'if': {'column_id': 'Factura'},
                        'minWidth': '100px',
                        'fontWeight': '600'
                    },
                    {
                        'if': {'column_id': 'Proveedor'},
                        'minWidth': '150px',
                        'textAlign': 'left'
                    },
                    {
                        'if': {'column_id': 'Valor Factura'},
                        'minWidth': '110px',
                        'fontWeight': '600',
                        'color': '#059669'
                    },
                    {
                        'if': {'column_id': 'Valor Nota'},
                        'minWidth': '110px',
                        'fontWeight': '600',
                        'color': '#dc2626'
                    }
                ],
                style_data={
                    'backgroundColor': theme['table_bg'],
                    'color': theme['text_secondary'],
                    'border': '0.5px solid rgba(0, 0, 0, 0.05)'  # Borde aún más sutil
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': theme['table_bg_alt'],
                        'border': '0.5px solid rgba(0, 0, 0, 0.03)'
                    },
                    # Hover effect más moderno y transparente
                    {
                        'if': {'state': 'active'},
                        'backgroundColor': f"rgba(59, 130, 246, 0.1)",
                        'border': f"1px solid rgba(59, 130, 246, 0.3)"
                    },
                    # Estilos para badges de estado con bordes delgados
                    {
                        'if': {'filter_query': '{Estado} = 1', 'column_id': 'Estado'},
                        'backgroundColor': 'rgba(251, 191, 36, 0.2)' if is_dark else '#fef3c7',
                        'color': '#fbbf24' if is_dark else '#f59e0b',
                        'fontWeight': '600',
                        'borderRadius': '20px',
                        'textAlign': 'center',
                        'border': f"1px solid {'#fbbf24' if is_dark else '#f59e0b'}",
                        'padding': '6px 12px'
                    },
                    {
                        'if': {'filter_query': '{Estado} = 2', 'column_id': 'Estado'},
                        'backgroundColor': 'rgba(96, 165, 250, 0.2)' if is_dark else '#dbeafe',
                        'color': '#60a5fa' if is_dark else '#2563eb',
                        'fontWeight': '600',
                        'borderRadius': '20px',
                        'textAlign': 'center',
                        'border': f"1px solid {'#60a5fa' if is_dark else '#2563eb'}",
                        'padding': '6px 12px'
                    },
                    {
                        'if': {'filter_query': '{Estado} = 3', 'column_id': 'Estado'},
                        'backgroundColor': 'rgba(52, 211, 153, 0.2)' if is_dark else '#d1fae5',
                        'color': '#34d399' if is_dark else '#059669',
                        'fontWeight': '600',
                        'borderRadius': '20px',
                        'textAlign': 'center',
                        'border': f"1px solid {'#34d399' if is_dark else '#059669'}",
                        'padding': '6px 12px'
                    },
                    {
                        'if': {'filter_query': '{Estado} = 4', 'column_id': 'Estado'},
                        'backgroundColor': 'rgba(156, 163, 175, 0.2)' if is_dark else '#f3f4f6',
                        'color': '#9ca3af',
                        'fontWeight': '600',
                        'borderRadius': '20px',
                        'textAlign': 'center',
                        'border': '1px solid #9ca3af',
                        'padding': '6px 12px'
                    },
                    # Estados de vencimiento con bordes sutiles
                    {
                        'if': {'filter_query': '{Estado vencimiento} contains "🔴"'},
                        'backgroundColor': 'rgba(220, 38, 38, 0.2)' if is_dark else 'rgba(220, 38, 38, 0.1)',
                        'color': '#fca5a5' if is_dark else '#dc2626',
                        'border': '0.5px solid rgba(220, 38, 38, 0.3)'
                    },
                    {
                        'if': {'filter_query': '{Estado vencimiento} contains "🟡"'},
                        'backgroundColor': 'rgba(245, 158, 11, 0.2)' if is_dark else 'rgba(245, 158, 11, 0.1)',
                        'color': '#fcd34d' if is_dark else '#f59e0b',
                        'border': '0.5px solid rgba(245, 158, 11, 0.3)'
                    },
                    {
                        'if': {'filter_query': '{Estado vencimiento} contains "🟢"'},
                        'backgroundColor': 'rgba(34, 197, 94, 0.2)' if is_dark else 'rgba(34, 197, 94, 0.1)',
                        'color': '#86efac' if is_dark else '#16a34a',
                        'border': '0.5px solid rgba(34, 197, 94, 0.3)'
                    }
                ],
                row_selectable='multi',
                page_action='native',
                page_current=0,
                page_size=15,
                sort_action='native',
                filter_action='native',
                export_format=None,
                export_headers=None,
                css=[
                    {
                        'selector': '.dash-table-container',
                        'rule': 'overflow-x: auto; max-width: 100%;'
                    },
                    {
                        'selector': '.export, .dash-spreadsheet-menu',
                        'rule': 'display: none !important;'
                    },
                    # Hover effect moderno con bordes sutiles
                    {
                        'selector': '.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner table tbody tr:hover',
                        'rule': f'background-color: rgba(59, 130, 246, 0.08) !important; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0, 0, 0, {"0.2" if is_dark else "0.1"}) !important; transition: all 0.2s ease !important; border: 1px solid rgba(59, 130, 246, 0.3) !important;'
                    },
                    # Forzar header azul y sobreescribir cualquier verde
                    {
                        'selector': '#facturas-table .dash-header, #facturas-table .column-header, #facturas-table thead tr th',
                        'rule': 'background-color: #1e40af !important; color: white !important; border: none !important;'
                    },
                    # Bordes más delgados en toda la tabla
                    {
                        'selector': '.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner table td',
                        'rule': 'border: 0.5px solid rgba(0, 0, 0, 0.1) !important;'
                    }
                ]
            )
        ], className="table-scroll-container", style={
            'width': '100%',
            'overflowX': 'auto',
            'overflowY': 'visible',
            'WebkitOverflowScrolling': 'touch',  # Scroll suave en iOS
            'position': 'relative'
        }),
        
        # Indicador de scroll horizontal en móvil
        html.Div([
            html.Span("← Desliza horizontalmente para ver más columnas →", style={
                'fontSize': '11px',
                'color': '#6b7280',
                'fontWeight': '500',
                'textAlign': 'center',
                'display': 'block',
                'padding': '8px',
                'background': 'linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.1), transparent)',
                'borderRadius': '0 0 12px 12px',
                'fontStyle': 'italic'
            })
        ], className="mobile-scroll-indicator", style={
            'display': 'none'  # Se mostrará solo en móvil via CSS
        })
    ], style={
        'width': '100%',
        'position': 'relative'
    })
# def create_facturas_table(table_data, is_dark=False):
#     """Crear tabla moderna sin color en header"""
#     if not table_data:
#         return create_no_data_message("No hay datos para mostrar", is_dark)

#     theme = get_theme_styles(is_dark)

#     return dash_table.DataTable(
#         id='facturas-table',
#         data=table_data,
#         columns=[
#             {'name': '', 'id': 'Ver', 'type': 'text'},
#             {'name': 'Factura', 'id': 'Factura', 'type': 'text'},
#             {'name': 'Órdenes de Compra', 'id': 'Órdenes de Compra', 'type': 'text'},
#             {'name': 'Estado', 'id': 'Estado', 'type': 'numeric'},
#             {'name': 'Proveedor', 'id': 'Proveedor', 'type': 'text'},
#             {'name': 'Valor Factura', 'id': 'Valor Factura', 'type': 'text'},
#             {'name': 'Valor Nota', 'id': 'Valor Nota', 'type': 'text'},
#             {'name': 'Forma pago', 'id': 'Forma pago', 'type': 'text'},
#             {'name': 'Fecha cargue', 'id': 'Fecha cargue', 'type': 'text'},
#             {'name': 'Días desde cargue', 'id': 'Días desde cargue', 'type': 'numeric'},
#             {'name': 'Fecha vencimiento', 'id': 'Fecha vencimiento', 'type': 'text'},
#             {'name': 'Estado vencimiento', 'id': 'Estado vencimiento', 'type': 'text'}
#         ],
#         style_table={
#             'overflowX': 'auto',
#             'borderRadius': '12px',
#             'overflow': 'hidden',
#             'boxShadow': '0 8px 32px rgba(0, 0, 0, 0.3)' if is_dark else '0 8px 32px rgba(0, 0, 0, 0.1)',
#             'border': f"1px solid {theme['card_border']}",
#             'width': '100%',
#             'minWidth': '1200px'
#         },
#         style_header={
#             'backgroundColor': '#1e40af',  # Azul moderno consistente
#             'color': theme['text_primary'],
#             'fontWeight': '600',
#             'textAlign': 'center',
#             'border': 'none',
#             'fontSize': '13px',
#             'padding': '14px 8px',
#             'fontFamily': 'Inter, sans-serif',
#             'borderBottom': f"2px solid {theme['card_border']}"
#         },
#         style_cell={
#             'textAlign': 'center',
#             'padding': '12px 6px',
#             'border': '0.5px solid rgba(0, 0, 0, 0.1)',  # Borde muy delgado
#             'fontSize': '12px',
#             'fontFamily': 'Inter, sans-serif',
#             'whiteSpace': 'normal',
#             'height': 'auto',
#             'minWidth': '80px',
#             'maxWidth': '200px',
#             'textOverflow': 'ellipsis',
#             'backgroundColor': theme['table_bg'],
#             'color': theme['text_secondary']
#         },
#         style_cell_conditional=[
#             {
#                 'if': {'column_id': 'Ver'},
#                 'width': '50px',
#                 'minWidth': '50px',
#                 'maxWidth': '50px',
#                 'cursor': 'pointer',
#                 'fontSize': '16px'
#             },
#             {
#                 'if': {'column_id': 'Estado'},
#                 'width': '120px',
#                 'minWidth': '120px'
#             }
#         ],
#         style_data={
#             'backgroundColor': theme['table_bg'],
#             'color': theme['text_secondary'],
#             'border': 'none'
#         },
#         style_data_conditional=[
#             {
#                 'if': {'row_index': 'odd'},
#                 'backgroundColor': theme['table_bg_alt']
#             },
#             # Hover effect más moderno y transparente
#             {
#                 'if': {'state': 'active'},
#                 'backgroundColor': f"rgba(59, 130, 246, 0.1)",
#                 'border': f"1px solid rgba(59, 130, 246, 0.3)"
#             },
#             # Estilos para badges de estado
#             {
#                 'if': {'filter_query': '{Estado} = 1', 'column_id': 'Estado'},
#                 'backgroundColor': 'rgba(251, 191, 36, 0.2)' if is_dark else '#fef3c7',
#                 'color': '#fbbf24' if is_dark else '#f59e0b',
#                 'fontWeight': '600',
#                 'borderRadius': '20px',
#                 'textAlign': 'center',
#                 'border': f"1px solid {'#fbbf24' if is_dark else '#f59e0b'}",
#                 'padding': '6px 12px'
#             },
#             {
#                 'if': {'filter_query': '{Estado} = 2', 'column_id': 'Estado'},
#                 'backgroundColor': 'rgba(96, 165, 250, 0.2)' if is_dark else '#dbeafe',
#                 'color': '#60a5fa' if is_dark else '#2563eb',
#                 'fontWeight': '600',
#                 'borderRadius': '20px',
#                 'textAlign': 'center',
#                 'border': f"1px solid {'#60a5fa' if is_dark else '#2563eb'}",
#                 'padding': '6px 12px'
#             },
#             {
#                 'if': {'filter_query': '{Estado} = 3', 'column_id': 'Estado'},
#                 'backgroundColor': 'rgba(52, 211, 153, 0.2)' if is_dark else '#d1fae5',
#                 'color': '#34d399' if is_dark else '#059669',
#                 'fontWeight': '600',
#                 'borderRadius': '20px',
#                 'textAlign': 'center',
#                 'border': f"1px solid {'#34d399' if is_dark else '#059669'}",
#                 'padding': '6px 12px'
#             },
#             {
#                 'if': {'filter_query': '{Estado} = 4', 'column_id': 'Estado'},
#                 'backgroundColor': 'rgba(156, 163, 175, 0.2)' if is_dark else '#f3f4f6',
#                 'color': '#9ca3af',
#                 'fontWeight': '600',
#                 'borderRadius': '20px',
#                 'textAlign': 'center',
#                 'border': '1px solid #9ca3af',
#                 'padding': '6px 12px'
#             },
#             # Estados de vencimiento
#             {
#                 'if': {'filter_query': '{Estado vencimiento} contains "🔴"'},
#                 'backgroundColor': 'rgba(220, 38, 38, 0.2)' if is_dark else 'rgba(220, 38, 38, 0.1)',
#                 'color': '#fca5a5' if is_dark else '#dc2626'
#             },
#             {
#                 'if': {'filter_query': '{Estado vencimiento} contains "🟡"'},
#                 'backgroundColor': 'rgba(245, 158, 11, 0.2)' if is_dark else 'rgba(245, 158, 11, 0.1)',
#                 'color': '#fcd34d' if is_dark else '#f59e0b'
#             },
#             {
#                 'if': {'filter_query': '{Estado vencimiento} contains "🟢"'},
#                 'backgroundColor': 'rgba(34, 197, 94, 0.2)' if is_dark else 'rgba(34, 197, 94, 0.1)',
#                 'color': '#86efac' if is_dark else '#16a34a'
#             }
#         ],
#         row_selectable='multi',
#         page_action='native',
#         page_current=0,
#         page_size=15,
#         sort_action='native',
#         filter_action='native',
#         export_format=None,
#         export_headers=None,
#         css=[
#             {
#                 'selector': '.dash-table-container',
#                 'rule': 'overflow-x: auto; max-width: 100%;'
#             },
#             {
#                 'selector': '.export, .dash-spreadsheet-menu',
#                 'rule': 'display: none !important;'
#             },
#             # Hover effect moderno
#             {
#                 'selector': '.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner table tbody tr:hover',
#                 'rule': f'background-color: rgba(59, 130, 246, 0.08) !important; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0, 0, 0, {"0.2" if is_dark else "0.1"}) !important; transition: all 0.2s ease !important;'
#             }
#         ]
#     )


# Callback para actualizar contador de seleccionados
@callback(
    Output('selected-count-badge', 'children'),
    [Input('facturas-table', 'selected_rows')]
)
def update_selected_count(selected_rows):
    count = len(selected_rows) if selected_rows else 0
    return str(count)


# Callback para abrir modal de productos - CORREGIDO
# @callback(
#     [Output('product-modal', 'children'),
#      Output('product-modal', 'style')],
#     [Input('facturas-table', 'active_cell')],
#     [State('facturas-table', 'data'),
#      State('processed-data-store', 'data'),
#      State('theme-store', 'data')]
# )
# def show_product_details(active_cell, table_data, processed_data, theme_data):
#     """Modal de productos con scroll corregido"""
#     if not active_cell or not table_data or not processed_data:
#         return [], {"display": "none"}

#     if active_cell['column_id'] != 'Ver':
#         return [], {"display": "none"}

#     try:
#         is_dark = theme_data.get('is_dark', False)
#         theme = get_theme_styles(is_dark)
        
#         row_data = table_data[active_cell['row']]
#         factura_num = row_data['Factura']
#         invoice_data = processed_data.get(factura_num, {})
#         products_data = invoice_data.get('productos', {})

#         if not products_data:
#             return [], {"display": "none"}

#         # Crear lista de productos
#         products_list = []
#         for product_code, product_info in products_data.items():
#             if isinstance(product_info, dict):
#                 cantidad_total = 0
#                 distribution = product_info.get('distribution', {})
#                 for dist_data in distribution.values():
#                     if isinstance(dist_data, dict):
#                         cantidad_total += dist_data.get('cantidad', 0)

#                 products_list.append({
#                     'Código': product_code,
#                     'Descripción': product_info.get('description', ''),
#                     'Costo': f"{format_currency_int(product_info.get('cost', 0))}",
#                     'Cantidad': cantidad_total,
#                     'Subtotal': f"{format_currency_int(product_info.get('subtotal', 0))}",
#                     'IVA': f"{product_info.get('iva', 0)}%",
#                     'Retención': f"{product_info.get('retefuente', 0)}%"
#                 })

#         # Modal con tabla corregida
#         modal_content = html.Div([
#             html.Div([
#                 # Header fijo
#                 html.Div([
#                     html.H3(f"Productos - Factura {factura_num}",
#                             style={'margin': '0', 'color': theme['text_primary'], 'fontSize': '18px'}),
#                     html.Button("✕", id="close-modal",
#                                 style={
#                                     'background': 'none', 'border': 'none', 'fontSize': '20px',
#                                     'cursor': 'pointer', 'padding': '8px', 'borderRadius': '8px',
#                                     'color': theme['text_muted']
#                                 })
#                 ], style={
#                     'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
#                     'padding': '20px', 'borderBottom': f"1px solid {theme['card_border']}",
#                     'background': theme['card_bg'], 'position': 'sticky', 'top': '0', 'zIndex': '10'
#                 }),

#                 # Información de la factura
#                 html.Div([
#                     html.P(f"📦 Total de productos: {len(products_data)}", 
#                            style={'fontWeight': 'bold', 'margin': '0 0 8px 0', 'color': theme['text_primary']}),
#                     html.P(f"🏢 Proveedor: {invoice_data.get('proveedor', 'N/A')}", 
#                            style={'margin': '0 0 8px 0', 'color': theme['text_secondary']}),
#                     html.P(f"💰 Valor total: {format_currency_int(invoice_data.get('valor_factura', 0))}", 
#                            style={'margin': '0 0 8px 0', 'color': theme['text_secondary']}),
#                     html.P(f"📋 Valor nota: {format_currency_int(invoice_data.get('valor_nota', 0))}", 
#                            style={'margin': '0 0 20px 0', 'color': theme['text_secondary']})
#                 ], style={'padding': '20px', 'background': theme['card_bg']}),

#                 # Tabla con scroll CORREGIDO
#                 html.Div([
#                     # Header de tabla fijo
#                     html.Div([
#                         html.Div("Código", style={'flex': '1', 'padding': '12px', 'fontWeight': '600', 'fontSize': '12px', 'color': 'white'}),
#                         html.Div("Descripción", style={'flex': '2', 'padding': '12px', 'fontWeight': '600', 'fontSize': '12px', 'color': 'white'}),
#                         html.Div("Costo", style={'flex': '1', 'padding': '12px', 'fontWeight': '600', 'fontSize': '12px', 'color': 'white'}),
#                         html.Div("Cantidad", style={'flex': '1', 'padding': '12px', 'fontWeight': '600', 'fontSize': '12px', 'color': 'white'}),
#                         html.Div("Subtotal", style={'flex': '1', 'padding': '12px', 'fontWeight': '600', 'fontSize': '12px', 'color': 'white'}),
#                         html.Div("IVA", style={'flex': '1', 'padding': '12px', 'fontWeight': '600', 'fontSize': '12px', 'color': 'white'}),
#                         html.Div("Retención", style={'flex': '1', 'padding': '12px', 'fontWeight': '600', 'fontSize': '12px', 'color': 'white'})
#                     ], style={
#                         'display': 'flex', 'backgroundColor': '#1e40af', 'textAlign': 'center',
#                         'position': 'sticky', 'top': '0', 'zIndex': '5'
#                     }),
                    
#                     # Cuerpo de tabla con altura fija y scroll
#                     html.Div([
#                         html.Div([
#                             html.Div(product['Código'], style={'flex': '1', 'padding': '12px', 'fontSize': '11px', 'color': theme['text_secondary']}),
#                             html.Div(product['Descripción'], style={'flex': '2', 'padding': '12px', 'fontSize': '11px', 'textAlign': 'left', 'color': theme['text_secondary']}),
#                             html.Div(product['Costo'], style={'flex': '1', 'padding': '12px', 'fontSize': '11px', 'color': theme['text_secondary']}),
#                             html.Div(product['Cantidad'], style={'flex': '1', 'padding': '12px', 'fontSize': '11px', 'color': theme['text_secondary']}),
#                             html.Div(product['Subtotal'], style={'flex': '1', 'padding': '12px', 'fontSize': '11px', 'color': theme['text_secondary']}),
#                             html.Div(product['IVA'], style={'flex': '1', 'padding': '12px', 'fontSize': '11px', 'color': theme['text_secondary']}),
#                             html.Div(product['Retención'], style={'flex': '1', 'padding': '12px', 'fontSize': '11px', 'color': theme['text_secondary']})
#                         ], style={
#                             'display': 'flex', 'textAlign': 'center',
#                             'borderBottom': f"1px solid {theme['card_border']}",
#                             'backgroundColor': theme['table_bg'] if i % 2 == 0 else theme['table_bg_alt']
#                         }) for i, product in enumerate(products_list)
#                     ], style={
#                         'height': '350px',  # Altura fija
#                         'overflowY': 'auto',  # Scroll vertical
#                         'overflowX': 'hidden',  # Sin scroll horizontal
#                         'border': f"1px solid {theme['card_border']}",
#                         'marginBottom': '20px'  # MARGEN INFERIOR AGREGADO
#                     })
#                 ], style={'padding': '0 20px 20px 20px'})  # Padding inferior agregado
#             ], style={
#                 'background': theme['card_bg'],
#                 'backdropFilter': 'blur(15px)' if is_dark else 'none',
#                 'borderRadius': '20px', 'maxWidth': '900px', 'width': '100%',
#                 'maxHeight': '80vh', 'overflow': 'hidden',
#                 'boxShadow': '0 25px 50px rgba(0, 0, 0, 0.5)' if is_dark else '0 25px 50px rgba(0, 0, 0, 0.15)',
#                 'border': f"1px solid {theme['card_border']}"
#             })
#         ], style={
#             'position': 'fixed', 'top': '0', 'left': '0', 'width': '100%', 'height': '100%',
#             'background': 'rgba(0, 0, 0, 0.8)' if is_dark else 'rgba(0, 0, 0, 0.5)',
#             'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
#             'zIndex': '1000', 'padding': '20px'
#         })

#         return modal_content, {"display": "flex"}

#     except Exception as e:
#         print(f"Error mostrando detalles: {e}")
#         return [], {"display": "none"}

# Callback para abrir modal de productos - MEJORADO
@callback(
    [Output('product-modal', 'children'),
     Output('product-modal', 'style')],
    [Input('facturas-table', 'active_cell')],
    [State('facturas-table', 'data'),
     State('processed-data-store', 'data'),
     State('theme-store', 'data')]
)
def show_product_details(active_cell, table_data, processed_data, theme_data):
    """Modal de productos con tabla mejorada y bordes redondeados"""
    if not active_cell or not table_data or not processed_data:
        return [], {"display": "none"}

    if active_cell['column_id'] != 'Ver':
        return [], {"display": "none"}

    try:
        is_dark = theme_data.get('is_dark', False)
        theme = get_theme_styles(is_dark)
        
        row_data = table_data[active_cell['row']]
        factura_num = row_data['Factura']
        invoice_data = processed_data.get(factura_num, {})
        products_data = invoice_data.get('productos', {})

        if not products_data:
            return [], {"display": "none"}

        # Crear lista de productos
        products_list = []
        for product_code, product_info in products_data.items():
            if isinstance(product_info, dict):
                cantidad_total = 0
                distribution = product_info.get('distribution', {})
                for dist_data in distribution.values():
                    if isinstance(dist_data, dict):
                        cantidad_total += dist_data.get('cantidad', 0)

                products_list.append({
                    'Código': product_code,
                    'Descripción': product_info.get('description', ''),
                    'Costo': f"{format_currency_int(product_info.get('cost', 0))}",
                    'Cantidad': cantidad_total,
                    'Subtotal': f"{format_currency_int(product_info.get('subtotal', 0))}",
                    'IVA': f"{product_info.get('iva', 0)}%",
                    'Retención': f"{product_info.get('retefuente', 0)}%"
                })

        # Modal con tabla mejorada y bordes redondeados
        modal_content = html.Div([
            html.Div([
                # Header fijo
                html.Div([
                    html.H3(f"Productos - Factura {factura_num}",
                            style={'margin': '0', 'color': theme['text_primary'], 'fontSize': '18px'}),
                    html.Button("✕", id="close-modal",
                                style={
                                    'background': 'none', 'border': 'none', 'fontSize': '20px',
                                    'cursor': 'pointer', 'padding': '8px', 'borderRadius': '8px',
                                    'color': theme['text_muted']
                                })
                ], style={
                    'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
                    'padding': '20px', 'borderBottom': f"1px solid {theme['card_border']}",
                    'background': theme['card_bg'], 'borderRadius': '20px 20px 0 0'
                }),

                # Información de la factura
                html.Div([
                    html.P(f"📦 Total de productos: {len(products_data)}", 
                           style={'fontWeight': 'bold', 'margin': '0 0 8px 0', 'color': theme['text_primary']}),
                    html.P(f"🏢 Proveedor: {invoice_data.get('proveedor', 'N/A')}", 
                           style={'margin': '0 0 8px 0', 'color': theme['text_secondary']}),
                    html.P(f"💰 Valor total: {format_currency_int(invoice_data.get('valor_factura', 0))}", 
                           style={'margin': '0 0 8px 0', 'color': theme['text_secondary']}),
                    html.P(f"📋 Valor nota: {format_currency_int(invoice_data.get('valor_nota', 0))}", 
                           style={'margin': '0 0 15px 0', 'color': theme['text_secondary']})
                ], style={'padding': '20px', 'background': theme['card_bg']}),

                # Contenedor de tabla con altura ajustable y bordes redondeados
                html.Div([
                    # Header de tabla fijo con bordes redondeados superiores
                    html.Div([
                        html.Div("Código", style={'flex': '1', 'padding': '12px', 'fontWeight': '600', 'fontSize': '12px', 'color': 'white'}),
                        html.Div("Descripción", style={'flex': '2', 'padding': '12px', 'fontWeight': '600', 'fontSize': '12px', 'color': 'white'}),
                        html.Div("Costo", style={'flex': '1', 'padding': '12px', 'fontWeight': '600', 'fontSize': '12px', 'color': 'white'}),
                        html.Div("Cantidad", style={'flex': '1', 'padding': '12px', 'fontWeight': '600', 'fontSize': '12px', 'color': 'white'}),
                        html.Div("Subtotal", style={'flex': '1', 'padding': '12px', 'fontWeight': '600', 'fontSize': '12px', 'color': 'white'}),
                        html.Div("IVA", style={'flex': '1', 'padding': '12px', 'fontWeight': '600', 'fontSize': '12px', 'color': 'white'}),
                        html.Div("Retención", style={'flex': '1', 'padding': '12px', 'fontWeight': '600', 'fontSize': '12px', 'color': 'white'})
                    ], style={
                        'display': 'flex', 'backgroundColor': '#1e40af', 'textAlign': 'center',
                        'borderRadius': '12px 12px 0 0', 'overflow': 'hidden'
                    }),
                    
                    # Cuerpo de tabla con altura ajustable y scroll
                    html.Div([
                        html.Div([
                            html.Div(product['Código'], style={'flex': '1', 'padding': '12px', 'fontSize': '11px', 'color': theme['text_secondary']}),
                            html.Div(product['Descripción'], style={'flex': '2', 'padding': '12px', 'fontSize': '11px', 'textAlign': 'left', 'color': theme['text_secondary']}),
                            html.Div(product['Costo'], style={'flex': '1', 'padding': '12px', 'fontSize': '11px', 'color': theme['text_secondary']}),
                            html.Div(product['Cantidad'], style={'flex': '1', 'padding': '12px', 'fontSize': '11px', 'color': theme['text_secondary']}),
                            html.Div(product['Subtotal'], style={'flex': '1', 'padding': '12px', 'fontSize': '11px', 'color': theme['text_secondary']}),
                            html.Div(product['IVA'], style={'flex': '1', 'padding': '12px', 'fontSize': '11px', 'color': theme['text_secondary']}),
                            html.Div(product['Retención'], style={'flex': '1', 'padding': '12px', 'fontSize': '11px', 'color': theme['text_secondary']})
                        ], style={
                            'display': 'flex', 'textAlign': 'center',
                            'borderBottom': f"1px solid {theme['card_border']}" if i < len(products_list) - 1 else 'none',
                            'backgroundColor': theme['table_bg'] if i % 2 == 0 else theme['table_bg_alt']
                        }) for i, product in enumerate(products_list)
                    ], style={
                        'maxHeight': 'calc(70vh - 200px)',  # Altura ajustable basada en viewport
                        'minHeight': '60px',               # Altura mínima
                        'overflowY': 'auto',               # Scroll vertical
                        'overflowX': 'hidden',             # Sin scroll horizontal
                        'borderRadius': '0 0 12px 12px',   # Bordes redondeados inferiores
                        'border': f"1px solid {theme['card_border']}",
                        'borderTop': 'none'                # Sin borde superior (conecta con header)
                    })
                ], style={
                    'margin': '0 20px 20px 20px',         # Margen uniforme
                    'borderRadius': '12px',               # Bordes redondeados del contenedor
                    'overflow': 'hidden',                 # Ocultar desbordamiento
                    'boxShadow': '0 4px 12px rgba(0, 0, 0, 0.1)'  # Sombra sutil
                })
            ], style={
                'background': theme['card_bg'],
                'backdropFilter': 'blur(15px)' if is_dark else 'none',
                'borderRadius': '20px', 
                'maxWidth': '90vw',                    # Responsive width
                'width': '900px',                      # Ancho fijo en desktop
                'maxHeight': '85vh',                   # Altura máxima del modal
                'display': 'flex',
                'flexDirection': 'column',
                'overflow': 'hidden',
                'boxShadow': '0 25px 50px rgba(0, 0, 0, 0.5)' if is_dark else '0 25px 50px rgba(0, 0, 0, 0.15)',
                'border': f"1px solid {theme['card_border']}",
                'transition': 'all 0.3s ease'
            }, className="modal-products-container")
        ], style={
            'position': 'fixed', 'top': '0', 'left': '0', 'width': '100%', 'height': '100%',
            'background': 'rgba(0, 0, 0, 0.8)' if is_dark else 'rgba(0, 0, 0, 0.5)',
            'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
            'zIndex': '1000', 'padding': '20px'
        })

        return modal_content, {"display": "flex"}

    except Exception as e:
        print(f"Error mostrando detalles: {e}")
        return [], {"display": "none"}

# Callback para manejar selecciones múltiples
@callback(
    Output('selected-invoices-store', 'data'),
    [Input('facturas-table', 'selected_rows')],
    [State('facturas-table', 'data')]
)
def update_selected_invoices(selected_rows, table_data):
    if not selected_rows or not table_data:
        return []
    
    selected_invoices = []
    for row_idx in selected_rows:
        if row_idx < len(table_data):
            selected_invoices.append({
                'factura': table_data[row_idx]['Factura'],
                'estado_actual': table_data[row_idx]['Estado']  # Usar valor numérico
            })
    
    return selected_invoices


# Callback para modal de cambio de estado
@callback(
    [Output('state-change-modal', 'children'),
     Output('state-change-modal', 'style')],
    [Input('change-state-button', 'n_clicks')],
    [State('selected-invoices-store', 'data'),
     State('theme-store', 'data')]
)
def show_state_change_modal(n_clicks, selected_invoices, theme_data):
    if not n_clicks or n_clicks == 0 or not selected_invoices:
        return [], {"display": "none"}

    is_dark = theme_data.get('is_dark', False)
    theme = get_theme_styles(is_dark)

    modal_content = html.Div([
        html.Div([
            html.Div([
                html.H3(f"Generar Nota - {len(selected_invoices)} Facturas",
                        style={'margin': '0', 'color': theme['text_primary'], 'fontSize': '18px'}),
                html.Button("✕", id="close-state-modal",
                            style={'background': 'none', 'border': 'none', 'fontSize': '20px',
                                   'cursor': 'pointer', 'padding': '8px', 'borderRadius': '8px',
                                   'color': theme['text_muted']})
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
                      'padding': '20px', 'borderBottom': f"1px solid {theme['card_border']}",
                      'background': theme['card_bg']}),

            html.Div([
                html.P(f"Facturas seleccionadas: {', '.join([inv['factura'] for inv in selected_invoices])}", 
                       style={'marginBottom': '20px', 'fontSize': '14px', 'color': theme['text_muted']}),
                
                html.Label("Nuevo Estado:", style={'fontWeight': '600', 'marginBottom': '10px', 
                                                   'display': 'block', 'color': theme['text_secondary']}),
                
                dcc.Dropdown(
                    id='new-state-dropdown',
                    options=[
                        {'label': '1 - Pendiente', 'value': 1},
                        {'label': '2 - En Advance', 'value': 2},
                        {'label': '3 - Nota Generada', 'value': 3},
                        {'label': '4 - Nota Descargada', 'value': 4}
                    ],
                    placeholder="Seleccionar nuevo estado...",
                    style={'marginBottom': '20px'}
                ),
                
                html.Div([
                    html.Button("Cancelar", id="cancel-state-change",
                                style={'background': '#6b7280', 'color': 'white', 'border': 'none',
                                       'padding': '10px 20px', 'borderRadius': '8px', 'marginRight': '10px',
                                       'cursor': 'pointer'}),
                    html.Button("Confirmar Cambio", id="confirm-state-change",
                                style={'background': '#10b981', 'color': 'white', 'border': 'none',
                                       'padding': '10px 20px', 'borderRadius': '8px', 'cursor': 'pointer'})
                ], style={'textAlign': 'right'})
                
            ], style={'padding': '20px', 'background': theme['card_bg']})
        ], style={'background': theme['card_bg'], 'backdropFilter': 'blur(15px)' if is_dark else 'none',
                  'borderRadius': '16px', 'maxWidth': '500px', 'width': '100%',
                  'boxShadow': '0 25px 50px rgba(0, 0, 0, 0.5)' if is_dark else '0 25px 50px rgba(0, 0, 0, 0.15)',
                  'border': f"1px solid {theme['card_border']}"})
    ], style={'position': 'fixed', 'top': '0', 'left': '0', 'width': '100%', 'height': '100%',
              'background': 'rgba(0, 0, 0, 0.8)' if is_dark else 'rgba(0, 0, 0, 0.5)',
              'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
              'zIndex': '1000', 'padding': '20px'})

    return modal_content, {"display": "flex"}


# Callback para procesar cambio de estado - CORREGIDO
@callback(
    [Output('processed-data-store', 'data', allow_duplicate=True),
     Output('state-change-modal', 'style', allow_duplicate=True)],
    [Input('confirm-state-change', 'n_clicks')],
    [State('new-state-dropdown', 'value'),
     State('selected-invoices-store', 'data'),
     State('processed-data-store', 'data')],
    prevent_initial_call=True
)
def update_invoice_states(n_clicks, new_state, selected_invoices, current_data):
    """CORREGIDO: Actualizar estados en Firebase"""
    if not n_clicks or not new_state or not selected_invoices:
        return current_data, {"display": "none"}

    try:
        processor = FacturasProveedoresAnalyzer()
        
        updated_count = 0
        for invoice in selected_invoices:
            factura_id = invoice['factura']
            print(f"Actualizando factura {factura_id} al estado {new_state}")
            success = processor.update_invoice_state(factura_id, new_state)
            if success:
                updated_count += 1
        
        print(f"✅ {updated_count} de {len(selected_invoices)} facturas actualizadas")
        
        # Recargar datos
        start_date = datetime.now().replace(day=1).date()
        end_date = datetime.now().date()
        date_range = (start_date, end_date)
        
        updated_data = processor.process_invoices(date_range=date_range)
        
        return updated_data, {"display": "none"}
        
    except Exception as e:
        print(f"Error actualizando estados: {e}")
        return current_data, {"display": "none"}


# Callbacks para cerrar modales
@callback(
    Output('product-modal', 'style', allow_duplicate=True),
    [Input('close-modal', 'n_clicks')],
    prevent_initial_call=True
)
def close_product_modal(n_clicks):
    if n_clicks:
        return {"display": "none"}
    return dash.no_update

@callback(
    Output('state-change-modal', 'style', allow_duplicate=True),
    [Input('close-state-modal', 'n_clicks'),
     Input('cancel-state-change', 'n_clicks')],
    prevent_initial_call=True
)
def close_state_modal(close_clicks, cancel_clicks):
    if close_clicks or cancel_clicks:
        return {"display": "none"}
    return dash.no_update
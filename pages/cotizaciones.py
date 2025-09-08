# import io
# import time
# import pandas as pd
# from datetime import datetime
# from typing import Dict, Any

# import dash
# from dash import (
#     dcc,
#     html,
#     Input,
#     Output,
#     State,
#     callback,
#     dash_table,
#     clientside_callback
# )
# from analyzers import CotizacionesAnalyzer
# from utils import get_theme_styles

# # Initialize analyzer
# analyzer = CotizacionesAnalyzer()

# try:
#     print("🚀 [CotizacionesPage] Inicializando CotizacionesAnalyzer...")
#     result = analyzer.load_data_from_firebase()
#     print(f"✅ [CotizacionesPage] Carga inicial completada: {result}")
# except Exception as e:
#     print(f"⚠️ [CotizacionesPage] Carga inicial falló: {e}")

# layout = html.Div([
#     # Stores
#     dcc.Store(id='cotizaciones-theme-store', data='light'),
#     dcc.Store(id='cotizaciones-data-store', data={'last_update': 0}),
#     dcc.Store(id='cotizaciones-chat-store', data={
#         'mensajes': [],
#         'session_data': {},
#         'conversacion_activa': False
#     }),

#     # Upload component
#     dcc.Upload(
#         id='cotizaciones-upload',
#         children=html.Div([
#             html.I(className="fas fa-cloud-upload-alt",
#                    style={'fontSize': '24px', 'marginRight': '10px'}),
#             'Arrastra archivos aquí o haz clic para subir (Excel o Imágenes)'
#         ]),
#         style={
#             'width': '100%', 'height': '60px', 'lineHeight': '60px',
#             'borderWidth': '2px', 'borderStyle': 'dashed', 'borderRadius': '10px',
#             'textAlign': 'center', 'margin': '10px', 'display': 'none'
#         },
#         multiple=False
#     ),

#     # Header
#     html.Div([
#         html.Div([
#             html.H1("🤖 Asistente Inteligente de Cotizaciones", style={
#                 'textAlign': 'center', 'fontSize': '2.5rem', 'fontWeight': '700',
#                 'fontFamily': 'Inter', 'margin': '0 0 20px 0',
#                 'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
#                 'webkitBackgroundClip': 'text', 'webkitTextFillColor': 'transparent',
#                 'backgroundClip': 'text'
#             }),
#             html.P("Chatbot conversacional para cotizaciones rápidas y inteligentes", style={
#                 'textAlign': 'center', 'fontSize': '1.1rem', 'color': '#666',
#                 'fontFamily': 'Inter', 'margin': '0 0 10px 0'
#             })
#         ], style={'width': '100%', 'marginBottom': '25px'}),

#         html.Div([
#             # Dropdown vendedor
#             html.Div([
#                 html.Label("Vendedor:", style={
#                     'fontWeight': 'bold', 'marginBottom': '8px',
#                     'fontFamily': 'Inter', 'fontSize': '14px'
#                 }, id='cotizaciones-dropdown-vendedor-label'),
#                 dcc.Dropdown(
#                     id='cotizaciones-dropdown-vendedor',
#                     value='Todos', style={'fontFamily': 'Inter'},
#                     className='custom-dropdown'
#                 )
#             ], style={'flex': '0 0 25%'}, id='cotizaciones-dropdown-vendedor-container'),

#             html.Div(style={'flex': '1'}),

#             # Botones de control
#             html.Button([html.Span('📎', style={'marginRight': '8px'}), 'Subir Archivo'],
#                         id='cotizaciones-btn-toggle-upload', n_clicks=0, style={
#                 'backgroundColor': '#17a2b8', 'color': 'white', 'border': 'none',
#                 'padding': '10px 20px', 'borderRadius': '8px', 'cursor': 'pointer',
#                 'fontFamily': 'Inter', 'fontSize': '14px', 'fontWeight': 'bold',
#                 'marginRight': '10px'
#             }),

#             html.Button([html.Span('💬', style={'marginRight': '8px'}), 'Nueva Conversación'],
#                         id='cotizaciones-btn-nueva-conversacion', n_clicks=0, style={
#                 'backgroundColor': '#28a745', 'color': 'white', 'border': 'none',
#                 'padding': '10px 20px', 'borderRadius': '8px', 'cursor': 'pointer',
#                 'fontFamily': 'Inter', 'fontSize': '14px', 'fontWeight': 'bold',
#                 'marginRight': '15px'
#             }),

#             html.Button([
#                 html.Span('🌙', id='cotizaciones-theme-icon',
#                           style={'fontSize': '18px'}),
#                 html.Span('Oscuro', id='cotizaciones-theme-text',
#                           style={'marginLeft': '8px'})
#             ], id='cotizaciones-theme-toggle', n_clicks=0, style={
#                 'backgroundColor': '#f8f9fa', 'border': '2px solid #e9ecef',
#                 'borderRadius': '12px', 'padding': '10px 16px', 'cursor': 'pointer',
#                 'fontFamily': 'Inter', 'fontSize': '13px', 'height': '40px',
#                 'display': 'flex', 'alignItems': 'center'
#             })

#         ], style={'width': '100%', 'display': 'flex', 'alignItems': 'center'})
#     ], style={'marginBottom': '30px', 'padding': '25px'}, id='cotizaciones-header-container'),

#     # Main content flex
#     html.Div([
#         # Chat section (left)
#         html.Div([
#             html.H3("💬 Chat Inteligente", style={
#                 'textAlign': 'center', 'marginBottom': '20px',
#                 'fontFamily': 'Inter', 'color': '#2c3e50'
#             }),

#             html.Div(id='cotizaciones-chat-status', style={
#                 'textAlign': 'center', 'marginBottom': '10px',
#                 'fontSize': '14px', 'fontFamily': 'Inter', 'color': '#6c757d'
#             }),

#             # Chat messages
#             html.Div(id='cotizaciones-chat-messages', children=[
#                 html.Div([
#                     html.Div("🤖 ¡Hola! Soy tu asistente inteligente para cotizaciones.", style={
#                         'textAlign': 'center', 'color': '#6c757d', 'fontSize': '18px',
#                         'fontFamily': 'Inter', 'fontWeight': '500', 'marginTop': '40px'
#                     }),
#                     html.Div("Presiona 'Nueva Conversación' para comenzar una cotización.", style={
#                         'textAlign': 'center', 'color': '#6c757d', 'fontSize': '14px',
#                         'fontFamily': 'Inter', 'marginTop': '10px'
#                     })
#                 ])
#             ], style={
#                 'height': '400px', 'overflowY': 'auto', 'border': '2px solid #e9ecef',
#                 'borderRadius': '16px', 'padding': '20px', 'backgroundColor': '#f8f9fa',
#                 'marginBottom': '20px', 'scrollBehavior': 'smooth'
#             }),

#             # Laboratory selector cards (outside chat)
#             html.Div(id='cotizaciones-laboratorio-selector', children=[], style={
#                 'marginBottom': '15px', 'display': 'none'
#             }),

#             # Input area integrado
#             html.Div([
#                 dcc.Textarea(
#                     id='cotizaciones-chat-input',
#                     placeholder='Escribe tu mensaje... (usa comas o Enter para separar productos)',
#                     style={
#                         'width': 'calc(100% - 100px)', 'height': '50px', 'padding': '12px',
#                         'border': '2px solid #e9ecef', 'borderRadius': '12px 0 0 12px',
#                         'fontSize': '14px', 'fontFamily': 'Inter', 'resize': 'none',
#                         'outline': 'none', 'float': 'left'
#                     }
#                 ),
#                 html.Button([html.I(className="fas fa-paper-plane")],
#                             id='cotizaciones-btn-enviar', n_clicks=0, style={
#                     'width': '50px', 'height': '50px', 'backgroundColor': '#007bff',
#                     'color': 'white', 'border': 'none', 'borderRadius': '0',
#                     'cursor': 'pointer', 'float': 'left'
#                 }),
#                 html.Button([html.I(className="fas fa-download")],
#                             id='cotizaciones-btn-descargar-excel', n_clicks=0, disabled=True, style={
#                     'width': '50px', 'height': '50px', 'backgroundColor': '#28a745',
#                     'color': 'white', 'border': 'none', 'borderRadius': '0 12px 12px 0',
#                     'cursor': 'pointer', 'float': 'left'
#                 })
#             ], style={'overflow': 'hidden', 'boxShadow': '0 2px 8px rgba(0,0,0,0.1)', 'borderRadius': '12px'}, className='cotizaciones-input-container'),

#             dcc.Download(id="cotizaciones-download-excel"),
#             dcc.Download(id="cotizaciones-download-csv")

#         ], style={
#             'backgroundColor': 'white', 'padding': '25px', 'borderRadius': '16px',
#             'boxShadow': '0 4px 6px rgba(0,0,0,0.1)', 'margin': '10px 0',
#             'flex': '2', 'marginRight': '20px'
#         }, id='cotizaciones-chat-container'),

#         html.Button("🛒", id='cart-toggle-btn', n_clicks=0, style={
#             'position': 'fixed', 'right': '20px', 'top': '50%',
#             'transform': 'translateY(-50%)', 'background': 'linear-gradient(135deg, #007bff, #0056b3)',
#             'color': 'white', 'border': 'none', 'borderRadius': '50%',
#             'width': '60px', 'height': '60px', 'cursor': 'pointer',
#             'boxShadow': '0 6px 20px rgba(0, 123, 255, 0.4)', 'zIndex': '1001',
#             'transition': 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
#             'fontSize': '18px', 'fontWeight': 'bold'
#         }),

#         # Overlay para cuando el carrito esté abierto
#         html.Div(id='cart-overlay', className='cart-overlay', n_clicks=0),

#         # Sidebar del carrito
#         html.Div([
#             html.Div([
#                 html.H3("🛒 Carrito de Cotización", style={
#                     'marginBottom': '20px', 'fontSize': '18px', 'fontWeight': 'bold',
#                     'textAlign': 'center', 'color': '#2c3e50'
#                 }),
#                 html.Button("✕", id='cart-close-btn', n_clicks=0, style={
#                     'position': 'absolute', 'top': '15px', 'right': '15px',
#                     'background': 'none', 'border': 'none', 'fontSize': '20px',
#                     'cursor': 'pointer', 'color': '#6c757d'
#                 })
#             ], style={'position': 'relative', 'marginBottom': '20px'}),
#             html.Div(id='cart-content',
#                      style={'flex': '1', 'overflowY': 'auto'}),
#             html.Div(id='cart-summary', style={'marginTop': '20px'})
#         ], id='cart-sidebar', style={
#             'position': 'fixed', 'right': '-350px', 'top': '0',
#             'width': '350px', 'height': '100vh', 'backgroundColor': '#ffffff',
#             'boxShadow': '-5px 0 25px rgba(0, 0, 0, 0.15)', 'zIndex': '1000',
#             'padding': '20px', 'transition': 'right 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
#             'borderLeft': '4px solid #007bff', 'display': 'flex', 'flexDirection': 'column'
#         })
#     ], style={'display': 'flex', 'gap': '0px', 'alignItems': 'stretch'}, id='cotizaciones-main-flex'),

#     # Historial section
#     html.Div([
#         html.H3("📋 Historial de Cotizaciones", style={
#             'textAlign': 'center', 'marginBottom': '20px',
#             'fontFamily': 'Inter', 'color': '#2c3e50'
#         }),
#         html.Div(id='cotizaciones-tabla-historial')
#     ], style={
#         'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '16px',
#         'boxShadow': '0 4px 6px rgba(0,0,0,0.1)', 'margin': '20px 0'
#     }, id='cotizaciones-historial-container'),

#     # Update button
#     html.Div([
#         html.Button([html.Span("🔄", style={'marginRight': '8px'}), 'Actualizar Datos'],
#                     id='cotizaciones-btn-actualizar', n_clicks=0, style={
#             'backgroundColor': '#6c757d', 'color': 'white', 'border': 'none',
#             'padding': '12px 24px', 'borderRadius': '8px', 'cursor': 'pointer',
#             'fontFamily': 'Inter', 'fontSize': '14px', 'fontWeight': 'bold'
#         })
#     ], style={'textAlign': 'center', 'margin': '20px 0'})

# ], style={
#     'fontFamily': 'Inter', 'backgroundColor': '#f5f5f5',
#     'padding': '20px', 'minHeight': '100vh'
# }, id='cotizaciones-main-container')

# # Enter key handling
# clientside_callback(
#     """
#     function(id) {
#         setTimeout(function() {
#             const textarea = document.getElementById('cotizaciones-chat-input');
#             if (textarea) {
#                 textarea.addEventListener('keydown', function(event) {
#                     if (event.key === 'Enter' && !event.shiftKey) {
#                         event.preventDefault();
#                         const sendButton = document.getElementById('cotizaciones-btn-enviar');
#                         if (sendButton && textarea.value.trim()) {
#                             sendButton.click();
#                         }
#                     }
#                 });
#             }
#         }, 100);
#         return window.dash_clientside.no_update;
#     }
#     """,
#     Output('cotizaciones-chat-input', 'style'),
#     Input('cotizaciones-chat-input', 'id')
# )

# # Auto-scroll chat
# clientside_callback(
#     """
#     function(children) {
#         setTimeout(function() {
#             const chatMessages = document.getElementById('cotizaciones-chat-messages');
#             if (chatMessages) {
#                 chatMessages.scrollTop = chatMessages.scrollHeight;
#             }
#         }, 100);
#         return window.dash_clientside.no_update;
#     }
#     """,
#     Output('cotizaciones-chat-messages', 'className'),
#     Input('cotizaciones-chat-messages', 'children')
# )


# def get_user_info_from_session(session_data: Dict[str, Any]):
#     """
#     Extract user information from session data.
#     """
#     if session_data and \
#             isinstance(session_data, dict):
#         return \
#             {
#                 'seller': session_data.get('seller', session_data.get('username', 'Vendedor')),
#                 'full_name': session_data.get('full_name', session_data.get('username', 'Vendedor')),
#                 'username': session_data.get('username', 'user'),
#                 'role': session_data.get('role', 'user')
#             }
#     return \
#         {
#             'seller': 'Vendedor',
#             'full_name': 'Vendedor',
#             'username': 'user',
#             'role': 'user'
#         }


# def get_selected_vendor(
#         session_data: Dict[str, Any],
#         dropdown_value: Any):
#     """
#     Get vendor based on permissions and selection.
#     """
#     from utils import can_see_all_vendors, get_user_vendor_filter

#     try:
#         if not session_data:
#             return 'Todos'
#         if can_see_all_vendors(session_data):
#             return dropdown_value if dropdown_value else 'Todos'
#         else:
#             return get_user_vendor_filter(session_data)

#     except Exception as e:
#         print(f"Error en get_selected_vendor: {e}")
#         return 'Todos'


# def parse_multiple_products(mensaje):
#     """
#     Parse multiple products from message using separators.
#     """
#     if not mensaje:
#         return []

#     separadores = ['\n', ',', ';']
#     productos = [mensaje]

#     for sep in separadores:
#         nuevos_productos = []

#         for producto in productos:
#             nuevos_productos.extend([p.strip()
#                                     for p in producto.split(sep) if p.strip()])
#         productos = nuevos_productos

#     return [p for p in productos if len(p) > 2]


# def create_message_bubble(mensaje, es_usuario=False, timestamp=None):
#     """
#     Create message bubble for chat display.
#     """
#     if timestamp is None:
#         timestamp = datetime.now().strftime('%H:%M')

#     if es_usuario:
#         return html.Div([
#             html.Div([
#                 html.Div([
#                     html.Span(
#                         '👤', style={'marginRight': '8px', 'fontSize': '16px'}),
#                     html.Span(mensaje, style={
#                               'fontSize': '14px', 'lineHeight': '1.4'})
#                 ], style={
#                     'backgroundColor': '#007bff', 'color': 'white', 'padding': '12px 16px',
#                     'borderRadius': '18px 18px 4px 18px', 'maxWidth': '80%',
#                     'wordWrap': 'break-word', 'fontSize': '14px', 'fontFamily': 'Inter',
#                     'display': 'flex', 'alignItems': 'flex-start',
#                     'boxShadow': '0 2px 8px rgba(0,123,255,0.3)'
#                 }),
#                 html.Div(timestamp, style={
#                     'fontSize': '11px', 'color': '#6c757d', 'textAlign': 'right', 'marginTop': '4px'
#                 })
#             ], style={
#                 'display': 'flex', 'flexDirection': 'column', 'alignItems': 'flex-end', 'marginLeft': '15%'
#             })
#         ], style={'marginBottom': '15px'})
#     else:
#         return html.Div([
#             html.Div([
#                 html.Div([
#                     html.Span(
#                         '🤖', style={'marginRight': '8px', 'fontSize': '16px'}),
#                     dcc.Markdown(mensaje, style={
#                         'margin': '0', 'fontSize': '14px', 'fontFamily': 'Inter', 'lineHeight': '1.5'
#                     })
#                 ], style={
#                     'backgroundColor': '#ffffff', 'color': '#2c3e50', 'padding': '15px 18px',
#                     'borderRadius': '18px 18px 18px 4px', 'maxWidth': '85%',
#                     'wordWrap': 'break-word', 'display': 'flex', 'alignItems': 'flex-start',
#                     'boxShadow': '0 2px 8px rgba(0,0,0,0.1)', 'border': '1px solid #e9ecef'
#                 }),
#                 html.Div(timestamp, style={
#                     'fontSize': '11px', 'color': '#6c757d', 'textAlign': 'left', 'marginTop': '4px'
#                 })
#             ], style={
#                 'display': 'flex', 'flexDirection': 'column', 'alignItems': 'flex-start', 'marginRight': '15%'
#             })
#         ], style={'marginBottom': '15px'})


# def create_laboratory_cards_enhanced(productos_encontrados, session_data):
#     """
#     Create enhanced laboratory selection cards with scrolling and grouping.
#     """
#     if not productos_encontrados:
#         return []

#     # Agrupar por descripción base
#     grupos = {}
#     for producto in productos_encontrados:
#         desc_base = producto.get('descripcion', '').split(
#             ' - ')[0].split(' (')[0]
#         if desc_base not in grupos:
#             grupos[desc_base] = []
#         grupos[desc_base].append(producto)

#     cards = [
#         html.Div("🛒 **Selecciona productos y especifica cantidades:**", style={
#             'fontSize': '18px', 'fontWeight': 'bold', 'marginBottom': '20px',
#             'textAlign': 'center', 'color': '#2c3e50', 'padding': '15px',
#             'backgroundColor': '#e7f3ff', 'borderRadius': '12px', 'border': '2px solid #007bff'
#         }),
#         html.Div("✅ Especifica cantidades y presiona '+ Agregar' para añadir al carrito", style={
#             'fontSize': '14px', 'textAlign': 'center', 'color': '#6c757d', 'marginBottom': '20px'
#         })
#     ]

#     for desc_base, productos in grupos.items():
#         grupo_container = [
#             html.H5(f"📦 {desc_base} ({len(productos)} opciones)", style={
#                 'color': '#007bff', 'margin': '15px 0 10px 0', 'fontSize': '16px',
#                 'fontWeight': '600', 'borderLeft': '4px solid #007bff', 'paddingLeft': '10px'
#             }),
#             html.Div([
#                 html.Div([
#                     html.Div([
#                         # Laboratorio más compacto
#                         html.Div(f"{producto.get('grupo', 'Sin Lab')[:18]}{'...' if len(producto.get('grupo', '')) > 18 else ''}", style={
#                             'fontSize': '10px', 'fontWeight': 'bold', 'color': '#ffffff',
#                             'backgroundColor': '#28a745', 'padding': '3px 6px',
#                             'borderRadius': '8px', 'marginBottom': '6px', 'textAlign': 'center'
#                         }),
#                         # Precio
#                         html.Div(f"${producto.get('precio_mas_iva', 0):,.0f}", style={
#                             'fontSize': '16px', 'fontWeight': 'bold', 'color': '#007bff',
#                             'marginBottom': '6px', 'textAlign': 'center'
#                         }),
#                         # Stock
#                         html.Div(f"Stock: {producto.get('stock', 0)}", style={
#                             'fontSize': '10px', 'color': '#6c757d', 'textAlign': 'center',
#                             'marginBottom': '8px'
#                         }),
#                         # Cantidad y label en la misma fila
#                         # Label cantidad

#                         # Input y botón + en la misma fila
#                         html.Div([
#                             html.Label("Cant:", style={
#                                 'fontSize': '11px', 'fontWeight': 'bold', 'color': '#495057',
#                                 'marginRight': '6px', 'display': 'inline-block', 'minWidth': '30px'
#                             }),
#                             dcc.Input(
#                                 id={'type': 'quantity-input',
#                                     'index': producto.get('codigo', f'{desc_base}-{i}')},
#                                 type='number',
#                                 value=0,
#                                 min=0,
#                                 max=1000,
#                                 style={
#                                     'width': '50px', 'height': '24px', 'fontSize': '11px',
#                                     'textAlign': 'center', 'border': '1px solid #ced4da',
#                                     'borderRadius': '4px', 'padding': '2px',
#                                     'marginRight': '4px'
#                                 }
#                             ),
#                             html.Button("+",
#                                         id={'type': 'add-product-btn',
#                                             'index': producto.get('codigo', f'{desc_base}-{i}')},
#                                         n_clicks=0,
#                                         style={
#                                             'width': '24px', 'height': '24px', 'fontSize': '12px',
#                                             'backgroundColor': '#28a745', 'color': 'white', 'border': 'none',
#                                             'borderRadius': '4px', 'cursor': 'pointer', 'fontWeight': 'bold',
#                                             'transition': 'all 0.2s ease',
#                                             'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'
#                                         }
#                                         )
#                         ], style={
#                             'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
#                             'marginBottom': '8px', 'gap': '0px'  # El gap se maneja con marginRight
#                         })
#                     ])
#                 ],
#                     id={'type': 'product-card',
#                         'index': producto.get('codigo', f'{desc_base}-{i}')},
#                     style={
#                         'backgroundColor': '#f8f9fa', 'border': '2px solid #e9ecef',
#                         'borderRadius': '8px', 'padding': '10px', 'margin': '4px',
#                         'textAlign': 'center', 'transition': 'all 0.3s ease',
#                         'width': '240px', 'height': '120px', 'position': 'relative',
#                         'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'space-between'
#                 },
#                     className='selectable-product-card'
#                 )
#                 for i, producto in enumerate(productos)
#             ], style={
#                 'display': 'flex', 'flexWrap': 'wrap', 'gap': '8px',
#                 'justifyContent': 'flex-start', 'maxHeight': '350px',
#                 'overflowY': 'auto', 'padding': '15px', 'backgroundColor': '#ffffff',
#                 'borderRadius': '8px', 'border': '1px solid #e9ecef'
#             }, className='productos-grupo-scroll')
#         ]
#         cards.extend(grupo_container)

#     return cards


# def agregar_producto_individual_al_carrito(producto, cantidad, session_data):
#     """
#     Add individual product to cart with quantity.
#     """
#     try:
#         carrito = session_data.get('productos_carrito', [])

#         # Verificar producto existente
#         for i, item in enumerate(carrito):
#             if item.get('codigo') == producto.get('codigo'):
#                 # Actualizar cantidad
#                 carrito[i]['cantidad'] += cantidad
#                 carrito[i]['subtotal'] = carrito[i]['precio_unitario'] * \
#                     carrito[i]['cantidad']
#                 session_data['productos_carrito'] = carrito
#                 return {
#                     'success': True,
#                     'message': f"Cantidad actualizada",
#                     'subtotal': carrito[i]['subtotal']
#                 }

#         # Agregar nuevo producto
#         precio_unitario = producto.get('precio_mas_iva', 0)
#         subtotal = precio_unitario * cantidad

#         nuevo_item = {
#             'codigo': producto.get('codigo', ''),
#             'descripcion': producto.get('descripcion', ''),
#             'precio_unitario': precio_unitario,
#             'cantidad': cantidad,
#             'subtotal': subtotal,
#             'iva': producto.get('iva', 19),
#             'p_descuento': producto.get('p_descuento', 0),
#             'grupo': producto.get('grupo', 'Sin Lab')
#         }

#         carrito.append(nuevo_item)
#         session_data['productos_carrito'] = carrito

#         return {
#             'success': True,
#             'message': "Producto agregado",
#             'subtotal': subtotal
#         }

#     except Exception as e:
#         print(f"Error adding to cart: {e}")
#         return {
#             'success': False,
#             'message': f"Error: {str(e)}",
#             'subtotal': 0
#         }


# def create_floating_cart_content(carrito, is_open=False):
#     """
#     Create floating cart sidebar content.
#     """
#     if not carrito:
#         return html.Div([
#             html.Div("🛒 Carrito vacío", style={
#                 'textAlign': 'center', 'color': '#6c757d', 'fontSize': '16px',
#                 'fontFamily': 'Inter', 'marginTop': '50px'
#             })
#         ])

#     cart_items = []
#     for i, item in enumerate(carrito):
#         item_div = html.Div([
#             html.Div([
#                 html.Div(f"{item.get('descripcion', 'Producto')}", style={
#                     'fontSize': '14px', 'fontWeight': '500', 'marginBottom': '5px'
#                 }),
#                 html.Div(f"Cant: {item.get('cantidad', 0)} × ${item.get('precio_unitario', 0):,.0f}", style={
#                     'fontSize': '12px', 'color': '#6c757d', 'marginBottom': '5px'
#                 }),
#                 html.Div(f"Total: ${item.get('subtotal', 0):,.0f}", style={
#                     'fontSize': '14px', 'fontWeight': 'bold', 'color': '#28a745'
#                 })
#             ], style={'flex': '1'}),
#             html.Button("🗑️", id=f'remove-item-{i}', n_clicks=0, style={
#                 'backgroundColor': '#dc3545', 'color': 'white', 'border': 'none',
#                 'borderRadius': '6px', 'padding': '5px 8px', 'cursor': 'pointer',
#                 'fontSize': '12px', 'marginLeft': '10px'
#             })
#         ], style={
#             'display': 'flex', 'alignItems': 'center', 'backgroundColor': '#f8f9fa',
#             'border': '1px solid #e9ecef', 'borderRadius': '8px', 'padding': '12px',
#             'marginBottom': '10px', 'transition': 'all 0.3s ease'
#         }, className='cart-item')
#         cart_items.append(item_div)

#     return html.Div(cart_items, style={'maxHeight': '400px', 'overflowY': 'auto'})


# def create_cart_summary(carrito):
#     """Create cart summary with totals."""
#     if not carrito:
#         return []

#     total_productos = len(carrito)
#     total_cantidad = sum(item.get('cantidad', 0) for item in carrito)
#     subtotal = sum(item.get('subtotal', 0) for item in carrito)
#     iva = subtotal * 0.19
#     total = subtotal + iva

#     return [html.Div([
#         html.Div([
#             html.Span("Productos:", style={'fontWeight': '500'}),
#             html.Span(f" {total_productos}", style={'color': '#2c3e50'})
#         ], style={'marginBottom': '5px'}),
#         html.Div([
#             html.Span("Unidades:", style={'fontWeight': '500'}),
#             html.Span(f" {total_cantidad}", style={'color': '#2c3e50'})
#         ], style={'marginBottom': '5px'}),
#         html.Hr(style={'margin': '10px 0', 'border': '1px solid #e9ecef'}),
#         html.Div([
#             html.Span("Subtotal:", style={'fontWeight': '500'}),
#             html.Span(f" ${subtotal:,.0f}", style={'color': '#2c3e50'})
#         ], style={'marginBottom': '5px'}),
#         html.Div([
#             html.Span("IVA (19%):", style={'fontWeight': '500'}),
#             html.Span(f" ${iva:,.0f}", style={'color': '#2c3e50'})
#         ], style={'marginBottom': '5px'}),
#         html.Div([
#             html.Span("TOTAL:", style={
#                       'fontWeight': 'bold', 'fontSize': '16px'}),
#             html.Span(f" ${total:,.0f}", style={
#                       'fontWeight': 'bold', 'fontSize': '16px', 'color': '#28a745'})
#         ])
#     ], style={'fontSize': '14px', 'fontFamily': 'Inter'})]


# def handle_file_upload_enhanced(contents, filename, chat_store, user_info):
#     """Handle file upload processing."""
#     try:
#         if not contents or not filename:
#             return (
#                 {
#                     'mensajes': chat_store.get('mensajes', []) + [{
#                         'texto': "❌ Error: Archivo no recibido correctamente.",
#                         'es_usuario': False,
#                         'timestamp': datetime.now().strftime('%H:%M')
#                     }],
#                     'session_data': chat_store.get('session_data', {}),
#                     'conversacion_activa': True
#                 },
#                 '',
#                 "❌ Error en archivo"
#             )

#         content_type, content_string = contents.split(',')
#         session_data = chat_store.get('session_data', {})
#         message, new_session_data = analyzer.procesar_archivo_subido(
#             content_string, filename, session_data)

#         mensajes_actuales = chat_store.get('mensajes', [])
#         mensajes_actuales.append({
#             'texto': f"📎 Archivo subido: {filename}",
#             'es_usuario': True,
#             'timestamp': datetime.now().strftime('%H:%M')
#         })
#         mensajes_actuales.append({
#             'texto': message,
#             'es_usuario': False,
#             'timestamp': datetime.now().strftime('%H:%M')
#         })

#         new_chat_store = {
#             'mensajes': mensajes_actuales,
#             'session_data': new_session_data,
#             'conversacion_activa': True
#         }

#         return new_chat_store, '', "📎 Archivo procesado"

#     except Exception as e:
#         print(f"Error en handle_file_upload_enhanced: {e}")
#         error_msg = f"❌ Error procesando archivo: {str(e)}"
#         mensajes_actuales = chat_store.get('mensajes', [])
#         mensajes_actuales.append({
#             'texto': error_msg,
#             'es_usuario': False,
#             'timestamp': datetime.now().strftime('%H:%M')
#         })

#         new_chat_store = {
#             'mensajes': mensajes_actuales,
#             'session_data': chat_store.get('session_data', {}),
#             'conversacion_activa': True
#         }

#         return new_chat_store, '', "❌ Error en archivo"


# def generate_csv_cotizacion(session_data):
#     """Generate CSV file with format: codigo, blank, cantidad, precio, descuento, zeros."""
#     try:
#         cotizacion_final = session_data.get('cotizacion_final')
#         if not cotizacion_final:
#             return None

#         productos = cotizacion_final.get('productos', [])
#         if not productos:
#             return None

#         csv_data = []
#         for producto in productos:
#             csv_data.append([
#                 producto.get('codigo', ''),  # Código
#                 '',  # Columna en blanco
#                 producto.get('cantidad', 1),  # Cantidad
#                 producto.get('precio_unitario', 0),  # Precio
#                 producto.get('p_descuento', 0),  # Descuento
#                 0  # Columna de ceros
#             ])

#         df = pd.DataFrame(csv_data, columns=[
#                           'codigo', 'blank', 'cantidad', 'precio', 'descuento', 'zeros'])

#         csv_buffer = io.StringIO()
#         df.to_csv(csv_buffer, index=False, header=False)
#         csv_string = csv_buffer.getvalue()

#         return csv_string.encode('utf-8')

#     except Exception as e:
#         print(f"Error generating CSV: {e}")
#         return None


# # ===== CALLBACKS =====

# @callback(
#     Output('cotizaciones-data-store', 'data'),
#     [Input('cotizaciones-btn-actualizar', 'n_clicks')],
#     prevent_initial_call=True
# )
# def update_cotizaciones_data(n_clicks):
#     """Central callback to reload ALL data."""
#     if n_clicks > 0:
#         try:
#             start_time = time.time()
#             result = analyzer.reload_data()
#             load_time = time.time() - start_time
#             return {
#                 'last_update': n_clicks,
#                 'timestamp': datetime.now().isoformat(),
#                 'success': result,
#                 'load_time': load_time
#             }
#         except Exception as e:
#             print(f"❌ Error en actualización: {e}")
#             return {
#                 'last_update': n_clicks,
#                 'timestamp': datetime.now().isoformat(),
#                 'error': str(e),
#                 'success': False
#             }
#     return dash.no_update


# @callback(
#     Output('cotizaciones-dropdown-vendedor', 'options'),
#     [Input('session-store', 'data'), Input('cotizaciones-data-store', 'data')]
# )
# def update_vendedor_dropdown_options(session_data, data_store):
#     """Update vendor dropdown options."""
#     try:
#         if not analyzer.df_cotizaciones.empty:
#             vendedores_unicos = analyzer.df_cotizaciones['vendedor'].dropna(
#             ).unique()
#             vendedores_list = [
#                 'Todos'] + sorted([v for v in vendedores_unicos if v and v.strip()])
#         else:
#             vendedores_list = ['Todos']
#         return [{'label': v, 'value': v} for v in vendedores_list]
#     except Exception as e:
#         print(f"Error updating vendor dropdown: {e}")
#         return [{'label': 'Todos', 'value': 'Todos'}]


# @callback(
#     [Output('cotizaciones-dropdown-vendedor-container', 'style'),
#      Output('cotizaciones-dropdown-vendedor-label', 'style')],
#     [Input('session-store', 'data')]
# )
# def update_dropdown_visibility(session_data):
#     """Show/hide dropdown based on user permissions."""
#     from utils import can_see_all_vendors
#     try:
#         if not session_data or not can_see_all_vendors(session_data):
#             return {'display': 'none'}, {'display': 'none'}
#         else:
#             return {'flex': '0 0 25%'}, {
#                 'fontWeight': 'bold', 'marginBottom': '8px',
#                 'fontFamily': 'Inter', 'fontSize': '14px'
#             }
#     except Exception as e:
#         print(f"Error en update_dropdown_visibility: {e}")
#         return {'display': 'none'}, {'display': 'none'}


# @callback(
#     [Output('cotizaciones-chat-store', 'data'),
#      Output('cotizaciones-chat-input', 'value'),
#      Output('cotizaciones-chat-status', 'children')],
#     [Input('cotizaciones-btn-enviar', 'n_clicks'),
#      Input('cotizaciones-btn-nueva-conversacion', 'n_clicks'),
#      Input('cotizaciones-upload', 'contents')],
#     [State('cotizaciones-chat-input', 'value'),
#      State('cotizaciones-chat-store', 'data'),
#      State('session-store', 'data'),
#      State('cotizaciones-upload', 'filename')],
#     prevent_initial_call=True
# )
# def handle_enhanced_chat_interaction(enviar_clicks, nueva_clicks, upload_contents,
#                                      mensaje_input, chat_store, session_data, filename):
#     """Handle enhanced chat interactions."""
#     try:
#         ctx = dash.callback_context
#         if not ctx.triggered:
#             return dash.no_update, dash.no_update, ""

#         button_id = ctx.triggered[0]['prop_id'].split('.')[0]
#         user_info = get_user_info_from_session(session_data)

#         # Validar chat_store
#         if not chat_store or not isinstance(chat_store, dict):
#             chat_store = {
#                 'mensajes': [],
#                 'session_data': {},
#                 'conversacion_activa': False
#             }

#         # Handle file upload
#         if button_id == 'cotizaciones-upload' and upload_contents:
#             return handle_file_upload_enhanced(upload_contents, filename, chat_store, user_info)

#         # Handle new conversation
#         if button_id == 'cotizaciones-btn-nueva-conversacion':
#             try:
#                 respuesta_bot, nueva_session = analyzer.procesar_mensaje_chatbot(
#                     '', {}, user_info)

#                 if not respuesta_bot or not isinstance(nueva_session, dict):
#                     respuesta_bot = "❌ Error iniciando conversación. Intenta de nuevo."
#                     nueva_session = {'estado': 'inicio'}

#                 new_chat_store = {
#                     'mensajes': [{
#                         'texto': respuesta_bot,
#                         'es_usuario': False,
#                         'timestamp': datetime.now().strftime('%H:%M')
#                     }],
#                     'session_data': nueva_session,
#                     'conversacion_activa': True
#                 }

#                 return new_chat_store, '', "🟢 Conversación iniciada"

#             except Exception as e:
#                 print(f"Error en nueva conversación: {e}")
#                 return (
#                     {
#                         'mensajes': [{
#                             'texto': f"❌ Error iniciando conversación: {str(e)}. Intenta de nuevo.",
#                             'es_usuario': False,
#                             'timestamp': datetime.now().strftime('%H:%M')
#                         }],
#                         'session_data': {},
#                         'conversacion_activa': False
#                     },
#                     '',
#                     "❌ Error al iniciar"
#                 )

#         # Handle send message
#         if button_id == 'cotizaciones-btn-enviar' and mensaje_input and mensaje_input.strip():
#             try:
#                 session_chat = chat_store.get('session_data', {})
#                 mensajes_actuales = chat_store.get('mensajes', [])

#                 # Check for multiple products
#                 productos_multiples = parse_multiple_products(
#                     mensaje_input.strip())

#                 if len(productos_multiples) > 1:
#                     mensaje_procesado = ", ".join(productos_multiples)
#                     mensaje_usuario = f"Productos múltiples: {mensaje_procesado}"
#                 else:
#                     mensaje_procesado = mensaje_input.strip()
#                     mensaje_usuario = mensaje_procesado

#                 # Add user message
#                 mensajes_actuales.append({
#                     'texto': mensaje_usuario,
#                     'es_usuario': True,
#                     'timestamp': datetime.now().strftime('%H:%M')
#                 })

#                 # Process with chatbot
#                 respuesta_bot, nueva_session = analyzer.procesar_mensaje_chatbot(
#                     mensaje_procesado, session_chat, user_info
#                 )

#                 if not respuesta_bot:
#                     respuesta_bot = "❌ Error procesando mensaje. Intenta de nuevo."

#                 if not isinstance(nueva_session, dict):
#                     nueva_session = session_chat

#                 # Add AI response
#                 mensajes_actuales.append({
#                     'texto': respuesta_bot,
#                     'es_usuario': False,
#                     'timestamp': datetime.now().strftime('%H:%M')
#                 })

#                 new_chat_store = {
#                     'mensajes': mensajes_actuales,
#                     'session_data': nueva_session,
#                     'conversacion_activa': True
#                 }

#                 # Determine status
#                 estado = nueva_session.get('estado', 'inicio')
#                 status_messages = {
#                     'esperando_nit': "🔍 Esperando NIT del cliente",
#                     'seleccionando_sede': "🏢 Seleccionando sede",
#                     'agregando_productos': "📦 Agregando productos",
#                     'seleccionando_laboratorio': "🏭 Seleccionando laboratorio",
#                     'definiendo_cantidad': "🔢 Definiendo cantidad",
#                     'finalizando': "✅ Cotización lista"
#                 }
#                 status = status_messages.get(estado, "💬 Conversando")

#                 return new_chat_store, '', status

#             except Exception as e:
#                 print(f"Error procesando mensaje: {e}")
#                 mensajes_actuales = chat_store.get('mensajes', [])
#                 mensajes_actuales.append({
#                     'texto': mensaje_input.strip(),
#                     'es_usuario': True,
#                     'timestamp': datetime.now().strftime('%H:%M')
#                 })
#                 mensajes_actuales.append({
#                     'texto': f"❌ Error procesando tu mensaje: {str(e)}. Escribe 'reiniciar' para empezar de nuevo.",
#                     'es_usuario': False,
#                     'timestamp': datetime.now().strftime('%H:%M')
#                 })

#                 return {
#                     'mensajes': mensajes_actuales,
#                     'session_data': chat_store.get('session_data', {}),
#                     'conversacion_activa': True
#                 }, '', "❌ Error procesando"

#         return dash.no_update, dash.no_update, ""

#     except Exception as e:
#         print(f"Error crítico en handle_enhanced_chat_interaction: {e}")
#         return (
#             {
#                 'mensajes': [{
#                     'texto': f"❌ Error crítico del sistema: {str(e)}. Recarga la página.",
#                     'es_usuario': False,
#                     'timestamp': datetime.now().strftime('%H:%M')
#                 }],
#                 'session_data': {},
#                 'conversacion_activa': False
#             },
#             '',
#             "❌ Error crítico"
#         )


# @callback(
#     Output('cotizaciones-chat-messages', 'children'),
#     [Input('cotizaciones-chat-store', 'data')]
# )
# def update_enhanced_chat_messages(chat_store):
#     """Update chat messages display."""
#     mensajes = chat_store.get('mensajes', [])

#     if not mensajes:
#         return [html.Div([
#             html.Div("🤖 ¡Hola! Soy tu asistente inteligente para cotizaciones.", style={
#                 'textAlign': 'center', 'color': '#6c757d', 'fontSize': '18px',
#                 'fontFamily': 'Inter', 'fontWeight': '500', 'marginTop': '40px'
#             }),
#             html.Div("Presiona 'Nueva Conversación' para comenzar una cotización.", style={
#                 'textAlign': 'center', 'color': '#6c757d', 'fontSize': '14px',
#                 'fontFamily': 'Inter', 'marginTop': '10px'
#             })
#         ])]

#     message_bubbles = []
#     for mensaje in mensajes:
#         bubble = create_message_bubble(
#             mensaje['texto'],
#             mensaje['es_usuario'],
#             mensaje['timestamp']
#         )
#         message_bubbles.append(bubble)

#     return message_bubbles


# @callback(
#     [Output('cotizaciones-laboratorio-selector', 'children'),
#      Output('cotizaciones-laboratorio-selector', 'style')],
#     [Input('cotizaciones-chat-store', 'data')]
# )
# def update_laboratory_selector(chat_store):
#     """Update laboratory selector cards outside chat."""
#     session_data = chat_store.get('session_data', {})
#     estado = session_data.get('estado', '')
#     productos_encontrados = session_data.get('productos_encontrados', [])

#     if estado == 'seleccionando_laboratorio' and len(productos_encontrados) > 1:
#         cards = create_laboratory_cards_enhanced(
#             productos_encontrados, session_data)
#         return cards, {'marginBottom': '15px', 'display': 'block'}
#     else:
#         return [], {'marginBottom': '15px', 'display': 'none'}


# @callback(
#     [Output('cotizaciones-carrito-content', 'children'),
#      Output('cotizaciones-carrito-resumen', 'children')],
#     [Input('cotizaciones-chat-store', 'data')]
# )
# def update_cart_display(chat_store):
#     """Update cart display with current products."""
#     session_data = chat_store.get('session_data', {})
#     carrito = session_data.get('productos_carrito', [])

#     cart_content = create_floating_cart_content(carrito)
#     cart_summary = create_cart_summary(carrito)

#     return cart_content, cart_summary


# # @callback(
# #     Output('cotizaciones-btn-descargar-excel', 'disabled'),
# #     [Input('cotizaciones-chat-store', 'data')]
# # )
# # def update_download_button_state(chat_store):
# #     """Update download button state."""
# #     session_data = chat_store.get('session_data', {})
# #     cotizacion_final = session_data.get('cotizacion_final')
# #     return cotizacion_final is None

# @callback(
#     Output('cotizaciones-btn-descargar-excel', 'disabled'),
#     [Input('cotizaciones-chat-store', 'data')]
# )
# def update_download_button_state(chat_store):
#     """Update download button state - fixed."""
#     try:
#         # Validar que chat_store sea dict
#         if not isinstance(chat_store, dict):
#             return True

#         session_data = chat_store.get('session_data', {})

#         # Validar que session_data sea dict
#         if not isinstance(session_data, dict):
#             return True

#         cotizacion_final = session_data.get('cotizacion_final')
#         return cotizacion_final is None

#     except Exception as e:
#         print(f"Error in update_download_button_state: {e}")
#         return True


# @callback(
#     [Output("cotizaciones-download-excel", "data"),
#      Output("cotizaciones-download-csv", "data")],
#     [Input("cotizaciones-btn-descargar-excel", "n_clicks")],
#     [State('cotizaciones-chat-store', 'data')],
#     prevent_initial_call=True
# )
# def generate_enhanced_downloads(n_clicks, chat_store):
#     """Generate Excel and CSV downloads."""
#     if n_clicks == 0:
#         return dash.no_update, dash.no_update

#     session_chat = chat_store.get('session_data', {})
#     cotizacion_final = session_chat.get('cotizacion_final')

#     if not cotizacion_final:
#         return dash.no_update, dash.no_update

#     try:
#         # Generate Excel
#         excel_bytes = analyzer.generar_excel_cotizacion(session_chat)
#         excel_download = None

#         if excel_bytes:
#             numero = cotizacion_final.get('numero_cotizacion', 'cotizacion')
#             timestamp = datetime.now().strftime('%Y%m%d_%H%M')
#             filename = f"Cotizacion_{numero}_{timestamp}.xlsx"
#             excel_download = dcc.send_bytes(excel_bytes, filename=filename)

#         # Generate CSV
#         csv_bytes = generate_csv_cotizacion(session_chat)
#         csv_download = None

#         if csv_bytes:
#             numero = cotizacion_final.get('numero_cotizacion', 'cotizacion')
#             timestamp = datetime.now().strftime('%Y%m%d_%H%M')
#             filename = f"Cotizacion_{numero}_{timestamp}.csv"
#             csv_download = dcc.send_bytes(csv_bytes, filename=filename)

#         return excel_download, csv_download

#     except Exception as e:
#         print(f"Error generating downloads: {e}")
#         return dash.no_update, dash.no_update


# @callback(
#     Output('cotizaciones-tabla-historial', 'children'),
#     [Input('session-store', 'data'),
#      Input('cotizaciones-dropdown-vendedor', 'value'),
#      Input('cotizaciones-data-store', 'data'),
#      Input('cotizaciones-theme-store', 'data')]
# )
# def update_enhanced_historial_table(session_data, dropdown_value, data_store, theme):
#     """Update history table."""
#     try:
#         vendedor = get_selected_vendor(session_data, dropdown_value)
#         df_historial = analyzer.get_historial_cotizaciones(vendedor, limite=50)

#         if df_historial.empty:
#             return html.Div([
#                 html.Div("📋 No hay cotizaciones registradas", style={
#                     'textAlign': 'center', 'color': '#6c757d', 'fontSize': '16px',
#                     'fontFamily': 'Inter', 'padding': '40px', 'fontStyle': 'italic'
#                 }),
#                 html.Div("Las cotizaciones aparecerán aquí cuando se generen", style={
#                     'textAlign': 'center', 'color': '#6c757d', 'fontSize': '14px', 'fontFamily': 'Inter'
#                 })
#             ])

#         # Prepare data
#         df_display = df_historial.copy()

#         if 'fecha' in df_display.columns:
#             df_display['fecha_formato'] = pd.to_datetime(
#                 df_display['fecha']).dt.strftime('%Y-%m-%d %H:%M')
#         else:
#             df_display['fecha_formato'] = 'N/A'

#         df_display['total_formato'] = df_display['total'].apply(
#             lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")

#         table = dash_table.DataTable(
#             data=df_display.to_dict('records'),
#             columns=[
#                 {'name': 'Número', 'id': 'numero_cotizacion'},
#                 {'name': 'Fecha', 'id': 'fecha_formato'},
#                 {'name': 'Cliente', 'id': 'cliente_nombre'},
#                 {'name': 'NIT', 'id': 'cliente_nit'},
#                 {'name': 'Vendedor', 'id': 'vendedor'},
#                 {'name': 'Productos', 'id': 'num_productos', 'type': 'numeric'},
#                 {'name': 'Total', 'id': 'total_formato'},
#                 {'name': 'Estado', 'id': 'estado'},
#                 {'name': 'Canal', 'id': 'canal'}
#             ],
#             style_cell={
#                 'textAlign': 'center', 'padding': '12px', 'fontFamily': 'Inter',
#                 'fontSize': '13px', 'border': '1px solid #e9ecef'
#             },
#             style_header={
#                 'backgroundColor': '#4CAF50', 'color': 'white',
#                 'fontWeight': 'bold', 'fontSize': '14px'
#             },
#             style_data={'backgroundColor': '#ffffff'},
#             style_data_conditional=[
#                 {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'},
#                 {
#                     'if': {'filter_query': '{estado} = generada'},
#                     'backgroundColor': '#d4edda', 'color': '#155724'
#                 },
#                 {
#                     'if': {'filter_query': '{canal} = chatbot'},
#                     'fontWeight': 'bold', 'backgroundColor': '#e7f3ff'
#                 }
#             ],
#             sort_action="native", page_action="native",
#             page_current=0, page_size=25
#         )

#         return table

#     except Exception as e:
#         print(f"Error updating historial table: {e}")
#         return html.Div([
#             html.P("❌ Error al cargar el historial", style={
#                 'textAlign': 'center', 'color': '#e74c3c',
#                 'fontSize': '16px', 'fontFamily': 'Inter'
#             })
#         ])


# @callback(
#     [Output('cotizaciones-theme-store', 'data'),
#      Output('cotizaciones-theme-icon', 'children'),
#      Output('cotizaciones-theme-text', 'children'),
#      Output('cotizaciones-theme-toggle', 'style'),
#      Output('cotizaciones-main-container', 'style'),
#      Output('cotizaciones-header-container', 'style')],
#     [Input('cotizaciones-theme-toggle', 'n_clicks')],
#     [State('cotizaciones-theme-store', 'data')]
# )
# def toggle_enhanced_theme(n_clicks, current_theme):
#     """Toggle theme."""
#     if n_clicks % 2 == 1:
#         new_theme = 'dark'
#         icon = '☀️'
#         text = 'Claro'
#         button_style = {
#             'backgroundColor': '#495057', 'border': '2px solid #6c757d',
#             'borderRadius': '12px', 'padding': '10px 16px', 'cursor': 'pointer',
#             'fontFamily': 'Inter', 'fontSize': '13px', 'height': '40px',
#             'display': 'flex', 'alignItems': 'center', 'color': '#ffffff'
#         }
#     else:
#         new_theme = 'light'
#         icon = '🌙'
#         text = 'Oscuro'
#         button_style = {
#             'backgroundColor': '#f8f9fa', 'border': '2px solid #e9ecef',
#             'borderRadius': '12px', 'padding': '10px 16px', 'cursor': 'pointer',
#             'fontFamily': 'Inter', 'fontSize': '13px', 'height': '40px',
#             'display': 'flex', 'alignItems': 'center', 'color': '#212529'
#         }

#     theme_styles = get_theme_styles(new_theme)

#     main_style = {
#         'fontFamily': 'Inter', 'backgroundColor': theme_styles['bg_color'],
#         'padding': '20px', 'color': theme_styles['text_color'], 'minHeight': '100vh'
#     }

#     header_style = {
#         'marginBottom': '30px', 'padding': '25px',
#         'backgroundColor': theme_styles['paper_color'],
#         'borderRadius': '16px', 'boxShadow': theme_styles['card_shadow']
#     }

#     return new_theme, icon, text, button_style, main_style, header_style


# @callback(
#     [Output({'type': 'product-card', 'index': dash.ALL}, 'style'),
#      Output({'type': 'product-card', 'index': dash.ALL}, 'className')],
#     [Input({'type': 'quantity-input', 'index': dash.ALL}, 'value')],
#     [State({'type': 'product-card', 'index': dash.ALL}, 'id')],
#     prevent_initial_call=True
# )
# def update_product_card_styles_consolidated(quantities, card_ids):
#     """
#     Consolidated callback for product card styles.
#     """
#     try:
#         if not card_ids:
#             return [], []

#         if not isinstance(quantities, list):
#             quantities = []

#         styles = []
#         classes = []

#         for i, card_id in enumerate(card_ids):
#             quantity = \
#                 quantities[i] if i < len(
#                     quantities) and quantities[i] is not None else 0

#             base_style = {
#                 'backgroundColor': '#f8f9fa', 'border': '2px solid #e9ecef',
#                 'borderRadius': '8px', 'padding': '10px', 'margin': '4px',
#                 'textAlign': 'center', 'transition': 'all 0.3s ease',
#                 'width': '240px', 'height': '120px', 'position': 'relative',
#                 'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'space-between'
#             }

#             if quantity is not None and quantity > 0:
#                 base_style.update({
#                     'backgroundColor': '#e8f5e8',
#                     'borderColor': '#28a745',
#                     'boxShadow': '0 0 0 2px rgba(40, 167, 69, 0.1)'
#                 })
#                 class_name = 'selectable-product-card with-quantity'
#             else:
#                 class_name = 'selectable-product-card'

#             styles.append(base_style)
#             classes.append(class_name)

#         return styles, classes

#     except Exception as e:
#         print(f"Error updating card styles: {e}")
#         return [], []


# @callback(
#     Output('cotizaciones-upload', 'style'),
#     [Input('cotizaciones-btn-toggle-upload', 'n_clicks')]
# )
# def toggle_upload_visibility(n_clicks):
#     """Toggle upload area visibility."""
#     if n_clicks % 2 == 1:
#         return {
#             'width': '100%', 'height': '60px', 'lineHeight': '60px',
#             'borderWidth': '2px', 'borderStyle': 'dashed', 'borderRadius': '10px',
#             'textAlign': 'center', 'margin': '10px', 'backgroundColor': '#f8f9fa',
#             'borderColor': '#17a2b8', 'color': '#17a2b8', 'fontFamily': 'Inter',
#             'fontSize': '14px', 'cursor': 'pointer'
#         }
#     else:
#         return {
#             'width': '100%', 'height': '60px', 'lineHeight': '60px',
#             'borderWidth': '2px', 'borderStyle': 'dashed', 'borderRadius': '10px',
#             'textAlign': 'center', 'margin': '10px', 'display': 'none'
#         }


# def handle_multiple_product_selection(productos_seleccionados, session_data):
#     """Handle multiple product selection and move to quantity definition."""
#     try:
#         if not productos_seleccionados:
#             return "❌ No has seleccionado ningún producto.", session_data

#         # Agrupar productos por descripción para mostrar mejor
#         grupos = {}
#         for producto in productos_seleccionados:
#             desc_base = producto.get('descripcion', '').split(' - ')[0]
#             if desc_base not in grupos:
#                 grupos[desc_base] = []
#             grupos[desc_base].append(producto)

#         mensaje_respuesta = f"✅ **Productos seleccionados ({len(productos_seleccionados)}):**\n\n"

#         for desc_base, productos in grupos.items():
#             mensaje_respuesta += f"📦 **{desc_base}** ({len(productos)} opciones)\n"
#             for producto in productos:
#                 laboratorio = producto.get('grupo', 'Sin Lab')
#                 precio = producto.get('precio_mas_iva', 0)
#                 mensaje_respuesta += f"   • 🏭 {laboratorio} - ${precio:,.0f}\n"
#             mensaje_respuesta += "\n"

#         mensaje_respuesta += "🔢 **Ahora define las cantidades:**\n"
#         mensaje_respuesta += "Escribe las cantidades separadas por comas en el mismo orden mostrado arriba.\n"
#         mensaje_respuesta += "**Ejemplo:** `5, 10, 3` (para los productos en orden)"

#         # Limpiar selección temporal y guardar productos finales
#         session_data.pop('productos_encontrados', None)
#         session_data['productos_para_cantidades'] = productos_seleccionados
#         session_data['estado'] = 'definiendo_cantidades_multiples'

#         return mensaje_respuesta, session_data

#     except Exception as e:
#         print(f"Error in handle_multiple_product_selection: {e}")
#         return f"❌ Error procesando selección: {str(e)}", session_data


# @callback(
#     [Output('cotizaciones-chat-store', 'data', allow_duplicate=True),
#      Output({'type': 'quantity-input', 'index': dash.ALL}, 'value')],
#     [Input({'type': 'add-product-btn', 'index': dash.ALL}, 'n_clicks')],
#     [State({'type': 'quantity-input', 'index': dash.ALL}, 'value'),
#      State({'type': 'add-product-btn', 'index': dash.ALL}, 'id'),
#      State('cotizaciones-chat-store', 'data')],
#     prevent_initial_call=True
# )
# def handle_add_product_to_cart(btn_clicks, quantities, btn_ids, chat_store):
#     """Handle adding products - fixed return values."""
#     try:
#         ctx = dash.callback_context

#         # SIEMPRE inicializar las listas de retorno
#         if not isinstance(quantities, list):
#             quantities = []

#         # Crear copia de quantities para retorno
#         return_quantities = list(quantities) if quantities else []

#         # Si no hay trigger válido, devolver valores actuales
#         if not ctx.triggered or not btn_clicks:
#             return dash.no_update, return_quantities

#         # Validar entrada
#         if not isinstance(chat_store, dict):
#             chat_store = {'mensajes': [], 'session_data': {},
#                           'conversacion_activa': True}

#         if not isinstance(btn_clicks, list):
#             return dash.no_update, return_quantities

#         # Encontrar botón clickeado
#         clicked_index = None
#         for i, clicks in enumerate(btn_clicks):
#             if clicks and clicks > 0:
#                 clicked_index = i
#                 break

#         # Si no hay click válido, devolver valores actuales
#         if clicked_index is None:
#             return dash.no_update, return_quantities

#         # Obtener datos del producto con validación mejorada
#         try:
#             btn_id = btn_ids[clicked_index]
#             producto_codigo = btn_id['index']

#             # Validación mejorada de cantidad
#             raw_cantidad = quantities[clicked_index] if clicked_index < len(
#                 quantities) else None
#             if raw_cantidad is None or raw_cantidad == '':
#                 cantidad = 0
#             else:
#                 try:
#                     cantidad = int(raw_cantidad)
#                 except (ValueError, TypeError):
#                     cantidad = 0

#         except (IndexError, KeyError):
#             return dash.no_update, return_quantities

#         # Validar cantidad
#         if cantidad <= 0:
#             mensajes_actuales = chat_store.get('mensajes', [])
#             mensajes_actuales.append({
#                 'texto': "❌ Especifica una cantidad válida (mayor a 0).",
#                 'es_usuario': False,
#                 'timestamp': datetime.now().strftime('%H:%M')
#             })

#             return {
#                 'mensajes': mensajes_actuales,
#                 'session_data': chat_store.get('session_data', {}),
#                 'conversacion_activa': True
#             }, return_quantities  # Devolver lista, no dash.no_update

#         # Buscar producto
#         session_data = chat_store.get('session_data', {})
#         productos_encontrados = session_data.get('productos_encontrados', [])

#         producto_seleccionado = None
#         for producto in productos_encontrados:
#             if str(producto.get('codigo', '')) == str(producto_codigo):
#                 producto_seleccionado = producto
#                 break

#         if not producto_seleccionado:
#             return dash.no_update, return_quantities

#         # Agregar al carrito
#         resultado = agregar_producto_individual_al_carrito(
#             producto_seleccionado, cantidad, session_data
#         )

#         mensajes_actuales = chat_store.get('mensajes', [])

#         if resultado['success']:
#             mensajes_actuales.append({
#                 'texto': f"✅ **{producto_seleccionado.get('descripcion', 'Producto')}** (x{cantidad}) agregado.\n💰 ${resultado.get('subtotal', 0):,.0f}",
#                 'es_usuario': False,
#                 'timestamp': datetime.now().strftime('%H:%M')
#             })

#             # Resetear el input que fue usado
#             if clicked_index < len(return_quantities):
#                 return_quantities[clicked_index] = 0

#             return {
#                 'mensajes': mensajes_actuales,
#                 'session_data': session_data,
#                 'conversacion_activa': True
#             }, return_quantities  # Devolver lista con reset
#         else:
#             mensajes_actuales.append({
#                 'texto': f"❌ {resultado['message']}",
#                 'es_usuario': False,
#                 'timestamp': datetime.now().strftime('%H:%M')
#             })

#             return {
#                 'mensajes': mensajes_actuales,
#                 'session_data': session_data,
#                 'conversacion_activa': True
#             }, return_quantities  # Devolver lista original

#     except Exception as e:
#         print(f"Error adding product: {e}")
#         # En caso de error, devolver listas válidas
#         safe_quantities = list(quantities) if isinstance(
#             quantities, list) else []
#         return dash.no_update, safe_quantities


# @callback(
#     [Output('cart-sidebar', 'className'),
#      Output('cart-overlay', 'className'),
#      Output('cart-toggle-btn', 'children'),
#      Output('cart-toggle-btn', 'style')],
#     [Input('cart-toggle-btn', 'n_clicks'),
#      Input('cart-overlay', 'n_clicks')],
#     [State('cart-sidebar', 'className'),
#      State('cotizaciones-chat-store', 'data')],
#     prevent_initial_call=True
# )
# def toggle_cart_sidebar(toggle_clicks, overlay_clicks, current_class, chat_store):
#     """Toggle cart sidebar visibility."""
#     try:
#         ctx = dash.callback_context
#         if not ctx.triggered:
#             return dash.no_update, dash.no_update, dash.no_update, dash.no_update

#         # Determinar si el carrito está actualmente abierto
#         is_open = current_class and 'open' in current_class

#         # Obtener número de productos en carrito para el badge
#         session_data = chat_store.get('session_data', {}) if chat_store else {}
#         carrito = session_data.get('productos_carrito', [])
#         num_productos = len(carrito)

#         # Toggle estado
#         if not is_open:
#             # Abrir carrito
#             cart_class = 'open'
#             overlay_class = 'cart-overlay active'

#             # Botón cuando está expandido
#             button_content = [
#                 html.Span("✕", style={'fontSize': '18px'}),
#                 html.Span(f" ({num_productos})" if num_productos > 0 else "")
#             ]
#             button_style = {
#                 'position': 'fixed', 'right': '370px', 'top': '50%',
#                 'transform': 'translateY(-50%)', 'background': 'linear-gradient(135deg, #dc3545, #c82333)',
#                 'color': 'white', 'border': 'none', 'borderRadius': '12px',
#                 'width': 'auto', 'height': 'auto', 'padding': '12px 20px',
#                 'cursor': 'pointer', 'boxShadow': '0 6px 20px rgba(220, 53, 69, 0.4)',
#                 'zIndex': '1001', 'transition': 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
#                 'fontSize': '14px', 'fontWeight': 'bold'
#             }
#         else:
#             # Cerrar carrito
#             cart_class = ''
#             overlay_class = 'cart-overlay'

#             # Botón cuando está colapsado
#             button_content = [
#                 html.Span("🛒", style={'fontSize': '18px'}),
#                 html.Span(f" {num_productos}" if num_productos > 0 else "", style={
#                     'position': 'absolute', 'top': '-5px', 'right': '-5px',
#                     'backgroundColor': '#dc3545', 'color': 'white', 'borderRadius': '50%',
#                     'width': '20px', 'height': '20px', 'fontSize': '10px',
#                     'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
#                     'fontWeight': 'bold'
#                 } if num_productos > 0 else {'display': 'none'})
#             ]
#             button_style = {
#                 'position': 'fixed', 'right': '20px', 'top': '50%',
#                 'transform': 'translateY(-50%)', 'background': 'linear-gradient(135deg, #007bff, #0056b3)',
#                 'color': 'white', 'border': 'none', 'borderRadius': '50%',
#                 'width': '60px', 'height': '60px', 'cursor': 'pointer',
#                 'boxShadow': '0 6px 20px rgba(0, 123, 255, 0.4)', 'zIndex': '1001',
#                 'transition': 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
#                 'fontSize': '18px', 'fontWeight': 'bold', 'position': 'relative'
#             }

#         return cart_class, overlay_class, button_content, button_style

#     except Exception as e:
#         print(f"Error in toggle_cart_sidebar: {e}")
#         return dash.no_update, dash.no_update, dash.no_update, dash.no_update


# @callback(
#     Output('cotizaciones-chat-store', 'data', allow_duplicate=True),
#     [Input({'type': 'remove-item', 'index': dash.ALL}, 'n_clicks')],
#     [State('cotizaciones-chat-store', 'data'),
#      State({'type': 'remove-item', 'index': dash.ALL}, 'id')],
#     prevent_initial_call=True
# )
# def handle_remove_cart_item(remove_clicks, chat_store, button_ids):
#     """
#     Handle removing items from cart.
#     """
#     try:
#         ctx = dash.callback_context
#         if not ctx.triggered or not any(remove_clicks):
#             return dash.no_update

#         # Encontrar qué botón fue clickeado
#         triggered_index = None
#         for i, click in enumerate(remove_clicks):
#             if click and click > 0:
#                 triggered_index = i
#                 break

#         if triggered_index is None:
#             return dash.no_update

#         session_data = chat_store.get('session_data', {})
#         carrito = session_data.get('productos_carrito', [])

#         # Eliminar producto del carrito
#         if 0 <= triggered_index < len(carrito):
#             producto_eliminado = carrito.pop(triggered_index)
#             session_data['productos_carrito'] = carrito

#             # Agregar mensaje al chat
#             mensajes_actuales = chat_store.get('mensajes', [])
#             mensajes_actuales.append({
#                 'texto': f"🗑️ Producto eliminado del carrito: {producto_eliminado.get('descripcion', 'Producto')}",
#                 'es_usuario': False,
#                 'timestamp': datetime.now().strftime('%H:%M')
#             })

#             return {
#                 'mensajes': mensajes_actuales,
#                 'session_data': session_data,
#                 'conversacion_activa': chat_store.get('conversacion_activa', True)
#             }

#         return dash.no_update

#     except Exception as e:
#         print(f"Error removing cart item: {e}")
#         return dash.no_update


# @callback(
#     Output('cart-content', 'children'),
#     [Input('cotizaciones-chat-store', 'data'),
#      Input('cart-sidebar', 'className')]
# )
# def update_floating_cart_content(chat_store, cart_class):
#     """
#     Update floating cart content.
#     """
#     try:
#         session_data = chat_store.get('session_data', {}) if chat_store else {}
#         carrito = session_data.get('productos_carrito', [])

#         if not carrito:
#             return html.Div([
#                 html.Div("🛒", style={
#                          'fontSize': '48px', 'textAlign': 'center', 'marginBottom': '20px'}),
#                 html.Div("Tu carrito está vacío", style={
#                     'textAlign': 'center', 'color': '#6c757d', 'fontSize': '16px',
#                     'fontFamily': 'Inter'
#                 })
#             ], style={'padding': '40px 20px'})

#         cart_items = []
#         for i, item in enumerate(carrito):
#             item_div = html.Div([
#                 html.Div([
#                     html.Div(f"{item.get('descripcion', 'Producto')}", style={
#                         'fontSize': '14px', 'fontWeight': '500', 'marginBottom': '5px',
#                         'lineHeight': '1.3'
#                     }),
#                     html.Div(f"Código: {item.get('codigo', 'N/A')}", style={
#                         'fontSize': '11px', 'color': '#6c757d', 'marginBottom': '3px'
#                     }),
#                     html.Div(f"Cant: {item.get('cantidad', 0)} × ${item.get('precio_unitario', 0):,.0f}", style={
#                         'fontSize': '12px', 'color': '#6c757d', 'marginBottom': '5px'
#                     }),
#                     html.Div(f"Total: ${item.get('subtotal', 0):,.0f}", style={
#                         'fontSize': '14px', 'fontWeight': 'bold', 'color': '#28a745'
#                     })
#                 ], style={'flex': '1'}),
#                 html.Button("🗑️",
#                             id={'type': 'remove-item', 'index': i},
#                             n_clicks=0,
#                             style={
#                                 'backgroundColor': '#dc3545', 'color': 'white', 'border': 'none',
#                                 'borderRadius': '6px', 'padding': '8px 10px', 'cursor': 'pointer',
#                                 'fontSize': '12px', 'marginLeft': '10px', 'transition': 'all 0.3s ease'
#                             }
#                             )
#             ], style={
#                 'display': 'flex', 'alignItems': 'center', 'backgroundColor': '#f8f9fa',
#                 'border': '1px solid #e9ecef', 'borderRadius': '8px', 'padding': '12px',
#                 'marginBottom': '10px', 'transition': 'all 0.3s ease'
#             }, className='cart-item')
#             cart_items.append(item_div)

#         # Agregar resumen al final
#         total_cantidad = sum(item.get('cantidad', 0) for item in carrito)
#         subtotal = sum(item.get('subtotal', 0) for item in carrito)
#         iva = subtotal * 0.19
#         total = subtotal + iva

#         resumen = html.Div([
#             html.Hr(style={'margin': '15px 0', 'border': '1px solid #e9ecef'}),
#             html.Div([
#                 html.Div(f"Productos: {len(carrito)}", style={
#                          'fontSize': '14px', 'marginBottom': '5px'}),
#                 html.Div(f"Unidades: {total_cantidad}", style={
#                          'fontSize': '14px', 'marginBottom': '5px'}),
#                 html.Div(f"Subtotal: ${subtotal:,.0f}", style={
#                          'fontSize': '14px', 'marginBottom': '5px'}),
#                 html.Div(f"IVA: ${iva:,.0f}", style={
#                          'fontSize': '14px', 'marginBottom': '5px'}),
#                 html.Div(f"TOTAL: ${total:,.0f}", style={
#                     'fontSize': '16px', 'fontWeight': 'bold', 'color': '#28a745'
#                 })
#             ], style={'backgroundColor': '#f8f9fa', 'padding': '10px', 'borderRadius': '8px'})
#         ])

#         cart_items.append(resumen)

#         return html.Div(cart_items, style={'maxHeight': '400px', 'overflowY': 'auto'})

#     except Exception as e:
#         print(f"Error updating cart content: {e}")
#         return html.Div("Error cargando carrito")

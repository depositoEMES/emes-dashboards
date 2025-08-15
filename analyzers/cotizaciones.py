import re
import io
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from openpyxl.styles import Font

from .excel_processor import ExcelProcessor
from .image_processor import ImageProcessor


class CotizacionesAnalyzer:

    def __init__(self):
        self.df_productos = pd.DataFrame()
        self.df_clientes = pd.DataFrame()
        self.df_cotizaciones = pd.DataFrame()
        self._last_update = None

    def reload_data(self):
        try:
            self.df_productos = pd.DataFrame()
            self.df_clientes = pd.DataFrame()
            self.df_cotizaciones = pd.DataFrame()
            result = self.load_data_from_firebase()
            self._last_update = datetime.now()
            return result
        except:
            return False

    def _get_db(self):
        try:
            from server import get_db
            return get_db()
        except:
            return None

    def load_data_from_firebase(self, force_reload=False):
        try:
            if not force_reload and not self.df_productos.empty:
                return True

            db = self._get_db()
            if not db:
                return False

            # Cargar datos
            listas_data = db.get_by_path("listas")
            if listas_data:
                self.process_listas_data(listas_data)

            clientes_data = db.get_by_path("clientes")
            if clientes_data:
                self.process_clientes_data(clientes_data)

            cotizaciones_data = db.get_by_path("cotizaciones")
            if cotizaciones_data:
                self.process_cotizaciones_data(cotizaciones_data)

            return True
        except:
            return False

    def process_listas_data(self, listas_data):
        try:
            productos_list = []
            for lista_id, lista_content in enumerate(listas_data):
                if str(lista_content) == "0" or not isinstance(lista_content, dict):
                    continue

                for producto_id, producto_info in lista_content.items():
                    if isinstance(producto_info, dict):
                        productos_list.append({
                            'codigo': producto_id,
                            'descripcion': producto_info.get('descripcion', ''),
                            'grupo': producto_info.get('grupo', ''),
                            'precio': float(producto_info.get('precio', 0)),
                            'precio_mas_iva': float(producto_info.get('precio_mas_iva', 0)),
                            'iva': producto_info.get('iva', 0),
                            'stock': producto_info.get('stock', 0),
                            # Agregado para CSV
                            'p_descuento': producto_info.get('p_descuento', 0),
                            'lista_precio': lista_id
                        })
            self.df_productos = pd.DataFrame(productos_list)
        except:
            pass

    def process_clientes_data(self, clientes_data):
        try:
            clientes_list = []
            for nit_principal, sedes_data in clientes_data.items():
                if isinstance(sedes_data, dict):
                    for sede_id, sede_info in sedes_data.items():
                        if isinstance(sede_info, dict):
                            clientes_list.append({
                                'nit_principal': nit_principal,
                                'sede_id': sede_id,
                                'nombre': sede_info.get('nombre', ''),
                                'razon': sede_info.get('razon', ''),
                                'ciudad': sede_info.get('ciudad', ''),
                                'lista': sede_info.get('lista', '1'),
                                'vendedor': sede_info.get('vendedor', ''),
                                'forma_pago': sede_info.get('forma_pago', ''),
                                'estado': sede_info.get('estado', ''),
                                'direccion': sede_info.get('direccion', ''),
                                'tel': sede_info.get('tel', ''),
                                'cupo': sede_info.get('cupo', 0)
                            })
            self.df_clientes = pd.DataFrame(clientes_list)
        except:
            pass

    def process_cotizaciones_data(self, cotizaciones_data):
        try:
            cotizaciones_list = []
            for cotizacion_id, cotizacion_info in cotizaciones_data.items():
                if isinstance(cotizacion_info, dict):
                    cotizaciones_list.append({
                        'numero_cotizacion': cotizacion_id,
                        'fecha': cotizacion_info.get('fecha', ''),
                        'cliente_nit': cotizacion_info.get('cliente_nit', ''),
                        'cliente_nombre': cotizacion_info.get('cliente_nombre', ''),
                        'vendedor': cotizacion_info.get('vendedor', ''),
                        'subtotal': float(cotizacion_info.get('subtotal', 0)),
                        'iva': float(cotizacion_info.get('iva', 0)),
                        'total': float(cotizacion_info.get('total', 0)),
                        'estado': cotizacion_info.get('estado', 'generada'),
                        'canal': cotizacion_info.get('canal', 'web'),
                        'num_productos': len(cotizacion_info.get('productos', []))
                    })
            self.df_cotizaciones = pd.DataFrame(cotizaciones_list)
        except:
            pass

    # MÉTODO PRINCIPAL QUE SIEMPRE RETORNA TUPLA
    def procesar_mensaje_chatbot(self, mensaje: str, session_data: dict, vendedor_info: dict) -> Tuple[str, dict]:
        """
        MÉTODO PRINCIPAL MEJORADO - SIEMPRE retorna Tuple[str, dict]
        """
        try:
            # Asegurar que los parámetros sean válidos
            if not isinstance(session_data, dict):
                session_data = {}
            if not isinstance(vendedor_info, dict):
                vendedor_info = {'seller': 'Vendedor'}
            if mensaje is None:
                mensaje = ""

            mensaje = str(mensaje).strip()
            estado = session_data.get('estado', 'inicio')

            # Comandos globales
            if mensaje.lower() in ['ayuda', 'help']:
                return "🆘 **Ayuda disponible** - Escribe el NIT del cliente para comenzar", session_data

            if mensaje.lower() in ['reiniciar', 'nuevo']:
                session_data.clear()
                session_data['estado'] = 'inicio'
                return "🔄 **Nueva conversación iniciada** - Escribe el NIT del cliente", session_data

            # Estados
            if estado == 'inicio':
                return self.procesar_inicio(vendedor_info, session_data)
            elif estado == 'esperando_nit':
                return self.procesar_nit(mensaje, session_data)
            elif estado == 'seleccionando_sede':
                return self.procesar_sede(mensaje, session_data)
            elif estado == 'agregando_productos':
                return self.procesar_productos_mejorado(mensaje, session_data)
            elif estado == 'seleccionando_laboratorio':
                return self.procesar_laboratorio(mensaje, session_data)
            elif estado == 'definiendo_cantidad':
                return self.procesar_cantidad(mensaje, session_data)
            elif estado == 'confirmando_productos_archivo':
                return self.procesar_confirmacion_archivo(mensaje, session_data)
            elif estado == 'finalizando':
                return self.procesar_finalizacion(mensaje, session_data)
            else:
                session_data['estado'] = 'inicio'
                return "❌ Error de estado - Reiniciando conversación", session_data

        except Exception as e:
            # FALLBACK DE EMERGENCIA - SIEMPRE RETORNA TUPLA
            print(f"Error en procesar_mensaje_chatbot: {e}")
            session_data_safe = {'estado': 'inicio'}
            return f"❌ Error: {str(e)}. Escribe 'reiniciar' para empezar", session_data_safe

    def procesar_inicio(self, vendedor_info: dict, session_data: dict) -> Tuple[str, dict]:
        """SIEMPRE retorna tupla"""
        try:
            nombre = vendedor_info.get('seller', 'Vendedor')
            session_data['estado'] = 'esperando_nit'
            session_data['vendedor_info'] = vendedor_info
            session_data['productos_carrito'] = []

            mensaje = f"""¡Hola {nombre}! 🤖

Para comenzar, necesito el **NIT del cliente**.

Ejemplo: 900123456"""

            return mensaje, session_data
        except Exception as e:
            return f"Error iniciando: {str(e)}", session_data

    def procesar_nit(self, nit: str, session_data: dict) -> Tuple[str, dict]:
        """SIEMPRE retorna tupla"""
        try:
            # Extraer números del NIT
            nit_numeros = re.sub(r'[^\d]', '', nit)

            if len(nit_numeros) < 6:
                return "❌ NIT inválido. Intenta de nuevo:", session_data

            # Buscar cliente
            encontrado, sedes = self.buscar_cliente(nit_numeros)

            if not encontrado:
                return f"❌ Cliente con NIT {nit_numeros} no encontrado. Intenta otro:", session_data

            session_data['sedes_disponibles'] = sedes

            if len(sedes) == 1:
                # Una sola sede
                sede = sedes[0]
                session_data['sede_seleccionada'] = sede
                session_data['estado'] = 'agregando_productos'

                mensaje = f"""✅ Cliente: {sede['razon']}
🏢 Ciudad: {sede['ciudad']}
💰 Lista: {sede['lista']}

Ahora puedes:
📝 **Escribir productos** (separados por comas o salto de línea)
📎 **Subir archivo** (Excel o imagen)
📋 **Ejemplo:** "acetaminofén 500mg, ibuprofeno 400mg"

¿Qué productos necesitas?"""
                return mensaje, session_data
            else:
                # Multiple sedes
                session_data['estado'] = 'seleccionando_sede'
                mensaje = f"✅ Cliente encontrado con {len(sedes)} sedes:\n\n"
                for i, sede in enumerate(sedes, 1):
                    mensaje += f"{i}. {sede['razon']} - {sede['ciudad']}\n"
                mensaje += "\nEscribe el número de la sede:"
                return mensaje, session_data

        except Exception as e:
            return f"Error procesando NIT: {str(e)}", session_data

    def procesar_sede(self, opcion: str, session_data: dict) -> Tuple[str, dict]:
        """SIEMPRE retorna tupla"""
        try:
            numero = int(opcion) - 1
            sedes = session_data.get('sedes_disponibles', [])

            if 0 <= numero < len(sedes):
                sede = sedes[numero]
                session_data['sede_seleccionada'] = sede
                session_data['estado'] = 'agregando_productos'

                mensaje = f"""✅ Sede seleccionada: {sede['razon']}
🏢 Ciudad: {sede['ciudad']}
💰 Lista: {sede['lista']}

Ahora puedes:
📝 **Escribir productos** (separados por comas o salto de línea)
📎 **Subir archivo** (Excel o imagen)
📋 **Ejemplo:** "acetaminofén 500mg, ibuprofeno 400mg"

¿Qué productos necesitas?"""
                return mensaje, session_data
            else:
                return f"❌ Opción inválida. Escribe un número entre 1 y {len(sedes)}:", session_data

        except ValueError:
            return "❌ Solo números. Escribe el número de la sede:", session_data
        except Exception as e:
            return f"Error seleccionando sede: {str(e)}", session_data

    def procesar_productos_mejorado(self, mensaje: str, session_data: dict) -> Tuple[str, dict]:
        """
        Procesar productos mejorado con soporte para múltiples productos y archivos.
        """
        try:
            if mensaje.lower() in ['terminar', 'finalizar']:
                return self.procesar_finalizacion("", session_data)

            if mensaje.lower() in ['carrito', 'ver carrito']:
                return self.mostrar_carrito(session_data)

            # Verificar si hay productos desde archivo pendientes
            productos_archivo = session_data.get('productos_desde_archivo')
            if productos_archivo and mensaje.lower() in ['si', 'sí', 'ok', 'confirmar']:
                return self.procesar_productos_desde_archivo(session_data)

            if productos_archivo and mensaje.lower() in ['no', 'cancelar']:
                session_data.pop('productos_desde_archivo', None)
                return "✅ Productos del archivo cancelados. Escribe manualmente los productos que necesitas:", session_data

            # Parsear múltiples productos del mensaje
            productos_textos = self.parse_multiple_products_from_message(
                mensaje)

            if not productos_textos:
                return f"❌ No encontré productos válidos en '{mensaje}'. Intenta de nuevo:", session_data

            # Procesar cada producto y recopilar TODOS los resultados
            todos_los_productos = []
            productos_sin_encontrar = []

            for producto_texto in productos_textos:
                resultado = self.procesar_producto_individual(
                    producto_texto, session_data)
                if resultado['encontrado']:
                    todos_los_productos.extend(resultado['productos'])
                else:
                    productos_sin_encontrar.append(producto_texto)

            # Si se encontraron productos, mostrar para selección
            if todos_los_productos:
                # Guardar todos los productos encontrados para selección
                session_data['productos_encontrados'] = todos_los_productos
                session_data['estado'] = 'seleccionando_laboratorio'

                # Mensaje de productos encontrados
                mensaje_respuesta = f"🔍 **Encontré {len(todos_los_productos)} opciones disponibles.**\n\n"

                if productos_sin_encontrar:
                    mensaje_respuesta += f"⚠️ **No encontrados:** {', '.join(productos_sin_encontrar)}\n\n"

                mensaje_respuesta += "👇 **Usa los controles de abajo para agregar productos al carrito**\n"
                mensaje_respuesta += "• Especifica la cantidad en cada producto\n"
                mensaje_respuesta += "• Presiona '+ Agregar' para añadir al carrito\n"
                mensaje_respuesta += "• Escribe 'terminar' cuando hayas terminado"

                return mensaje_respuesta, session_data
            else:
                # No se encontró ningún producto
                mensaje_error = f"""❌ No encontré ningún producto de los solicitados:
    {chr(10).join(f'• {p}' for p in productos_sin_encontrar)}

    💡 **Sugerencias:**
    - Verifica la ortografía
    - Usa términos más específicos
    - Intenta con el nombre comercial

    🔍 **Ejemplo:** "acetaminofen", "dolex", "ibuprofeno"

    Intenta de nuevo:"""
                return mensaje_error, session_data

        except Exception as e:
            print(f"Error procesando productos: {e}")
            return f"Error procesando productos: {str(e)}", session_data

    def parse_multiple_products_from_message(self, mensaje: str) -> List[str]:
        """Parsear múltiples productos del mensaje usando separadores."""
        if not mensaje:
            return []

        # Separadores comunes
        separadores = ['\n', ',', ';', '|']
        productos = [mensaje]

        for sep in separadores:
            nuevos_productos = []
            for producto in productos:
                nuevos_productos.extend(
                    [p.strip() for p in producto.split(sep) if p.strip()])
            productos = nuevos_productos

        # Filtrar productos muy cortos
        productos_validos = [p for p in productos if len(p) > 2]

        return productos_validos

    def procesar_producto_individual(self, producto_texto: str, session_data: dict) -> Dict:
        """Procesar un producto individual."""
        try:
            sede = session_data.get('sede_seleccionada', {})
            lista = sede.get('lista', '1')

            # Buscar productos
            productos = self.buscar_productos(producto_texto, lista)

            if not productos:
                return {'encontrado': False, 'productos': []}

            return {'encontrado': True, 'productos': productos}

        except Exception as e:
            print(f"Error procesando producto individual: {e}")
            return {'encontrado': False, 'productos': []}

    def manejar_productos_encontrados(self, productos_encontrados: List[Dict], productos_sin_encontrar: List[str], session_data: dict) -> Tuple[str, dict]:
        """Manejar productos encontrados y generar respuesta apropiada."""

        # Si solo hay un producto encontrado, procesarlo directamente
        if len(productos_encontrados) == 1:
            producto = productos_encontrados[0]
            session_data['producto_temporal'] = producto
            session_data['estado'] = 'definiendo_cantidad'

            mensaje = f"""✅ Producto encontrado:
📦 {producto['descripcion']}
💰 ${producto['precio_mas_iva']:,.0f}
📊 Stock: {producto['stock']}

¿Cuántas unidades necesitas?"""

            if productos_sin_encontrar:
                mensaje += f"\n\n⚠️ **No encontrados:** {', '.join(productos_sin_encontrar)}"

            return mensaje, session_data

        # Si hay múltiples productos, mostrar opciones de laboratorio
        elif len(productos_encontrados) > 1:
            session_data['productos_encontrados'] = productos_encontrados
            session_data['estado'] = 'seleccionando_laboratorio'

            mensaje = f"🔍 Encontré **{len(productos_encontrados)} opciones**:\n\n"
            for i, prod in enumerate(productos_encontrados[:5], 1):
                mensaje += f"**{i}.** {prod['descripcion']} - ${prod['precio_mas_iva']:,.0f} (Stock: {prod['stock']})\n"

            mensaje += "\n🏭 **Selecciona usando los botones externos** o escribe el número:"

            if productos_sin_encontrar:
                mensaje += f"\n\n⚠️ **No encontrados:** {', '.join(productos_sin_encontrar)}"

            return mensaje, session_data

        return "❌ Error procesando productos encontrados", session_data

    def procesar_productos_desde_archivo(self, session_data: dict) -> Tuple[str, dict]:
        """Procesar productos confirmados desde archivo."""
        try:
            productos_archivo = session_data.get('productos_desde_archivo', {})
            productos_texto = productos_archivo.get('texto', '')

            if not productos_texto:
                session_data.pop('productos_desde_archivo', None)
                return "❌ Error: No hay productos del archivo para procesar.", session_data

            # Procesar como mensaje normal
            session_data.pop('productos_desde_archivo', None)
            return self.procesar_productos_mejorado(productos_texto, session_data)

        except Exception as e:
            return f"Error procesando productos desde archivo: {str(e)}", session_data

    def procesar_confirmacion_archivo(self, mensaje: str, session_data: dict) -> Tuple[str, dict]:
        """Procesar confirmación de productos desde archivo."""
        try:
            if mensaje.lower() in ['si', 'sí', 'ok', 'confirmar', 'yes']:
                return self.procesar_productos_desde_archivo(session_data)
            elif mensaje.lower() in ['no', 'cancelar', 'cancel']:
                session_data.pop('productos_desde_archivo', None)
                session_data['estado'] = 'agregando_productos'
                return "✅ Productos del archivo cancelados. Escribe manualmente los productos que necesitas:", session_data
            else:
                return "❓ Responde 'sí' para confirmar los productos o 'no' para cancelar:", session_data

        except Exception as e:
            return f"Error en confirmación de archivo: {str(e)}", session_data

    def procesar_laboratorio(self, opcion: str, session_data: dict) -> Tuple[str, dict]:
        """SIEMPRE retorna tupla"""
        try:
            numero = int(opcion) - 1
            productos = session_data.get('productos_encontrados', [])

            if 0 <= numero < len(productos):
                producto = productos[numero]
                session_data['producto_temporal'] = producto
                session_data['estado'] = 'definiendo_cantidad'
                session_data.pop('productos_encontrados', None)

                mensaje = f"""✅ Producto seleccionado:
📦 {producto['descripcion']}
💰 ${producto['precio_mas_iva']:,.0f}
📊 Stock: {producto['stock']}

¿Cuántas unidades necesitas?"""
                return mensaje, session_data
            else:
                return f"❌ Opción inválida. Escribe un número entre 1 y {len(productos)}:", session_data

        except ValueError:
            return "❌ Solo números. Escribe el número del producto:", session_data
        except Exception as e:
            return f"Error seleccionando producto: {str(e)}", session_data

    def procesar_cantidad(self, cantidad_str: str, session_data: dict) -> Tuple[str, dict]:
        """SIEMPRE retorna tupla"""
        try:
            cantidad = int(cantidad_str)

            if cantidad <= 0:
                return "❌ La cantidad debe ser mayor a 0:", session_data

            if cantidad > 1000:
                return "❌ Cantidad muy alta. Máximo 1000 unidades:", session_data

            # Agregar al carrito
            resultado = self.agregar_al_carrito(session_data, cantidad)

            if resultado:
                session_data.pop('producto_temporal', None)
                session_data['estado'] = 'agregando_productos'

                carrito = session_data.get('productos_carrito', [])
                total_productos = len(carrito)
                total_cantidad = sum(p.get('cantidad', 0) for p in carrito)
                total_valor = sum(p.get('subtotal', 0) for p in carrito)

                mensaje = f"""✅ Producto agregado al carrito!

🛒 **Carrito actual:**
• {total_productos} productos
• {total_cantidad} unidades
• Total: ${total_valor:,.0f}

**Opciones:**
📝 Agregar más productos (escribe el nombre)
🛒 Ver carrito completo (escribe 'carrito')
✅ Finalizar cotización (escribe 'terminar')"""
                return mensaje, session_data
            else:
                return "❌ Error agregando producto. Intenta de nuevo:", session_data

        except ValueError:
            return "❌ Solo números. ¿Cuántas unidades necesitas?", session_data
        except Exception as e:
            return f"Error procesando cantidad: {str(e)}", session_data

    def procesar_finalizacion(self, mensaje: str, session_data: dict) -> Tuple[str, dict]:
        """SIEMPRE retorna tupla"""
        try:
            carrito = session_data.get('productos_carrito', [])

            if not carrito:
                session_data['estado'] = 'agregando_productos'
                return "❌ No hay productos en el carrito. Agrega algunos productos primero:", session_data

            # Generar cotización
            cotizacion = self.generar_cotizacion(session_data)

            if cotizacion:
                session_data['cotizacion_final'] = cotizacion
                session_data['estado'] = 'finalizando'

                # Guardar en Firebase
                self.guardar_cotizacion(cotizacion)

                mensaje = f"""🎉 **¡Cotización generada exitosamente!**

📋 **Número:** {cotizacion['numero_cotizacion']}
👤 **Cliente:** {cotizacion['cliente_nombre']}
📦 **Productos:** {len(carrito)}
💰 **Total:** ${cotizacion['total']:,.0f}

✅ **La cotización está lista**
📊 **Archivos disponibles:** Excel + CSV

🔽 **Presiona "Guardar" para descargar**

💬 **Escribe 'nueva' para crear otra cotización**"""
                return mensaje, session_data
            else:
                return "❌ Error generando cotización. Intenta de nuevo:", session_data

        except Exception as e:
            return f"Error finalizando cotización: {str(e)}", session_data

    def mostrar_carrito(self, session_data: dict) -> Tuple[str, dict]:
        """SIEMPRE retorna tupla"""
        try:
            carrito = session_data.get('productos_carrito', [])

            if not carrito:
                return "🛒 Tu carrito está vacío. Agrega productos escribiendo su nombre:", session_data

            mensaje = f"🛒 **Carrito ({len(carrito)} productos):**\n\n"
            total = 0

            for i, item in enumerate(carrito, 1):
                cantidad = item.get('cantidad', 0)
                precio = item.get('precio_unitario', 0)
                subtotal = item.get('subtotal', 0)
                mensaje += f"**{i}.** {item.get('descripcion', 'Producto')}\n"
                mensaje += f"   📦 Cantidad: {cantidad} × ${precio:,.0f} = ${subtotal:,.0f}\n\n"
                total += subtotal

            iva = total * 0.19
            total_final = total + iva

            mensaje += f"""**💰 Resumen:**
Subtotal: ${total:,.0f}
IVA (19%): ${iva:,.0f}
**TOTAL: ${total_final:,.0f}**

**Opciones:**
📝 Agregar más productos (escribe el nombre)
✅ Finalizar cotización (escribe 'terminar')"""

            return mensaje, session_data

        except Exception as e:
            return f"Error mostrando carrito: {str(e)}", session_data

    # MÉTODOS AUXILIARES
    def buscar_cliente(self, nit: str) -> Tuple[bool, List[Dict]]:
        """Buscar cliente por NIT"""
        try:
            if self.df_clientes.empty:
                return False, []

            clientes = self.df_clientes[
                self.df_clientes['nit_principal'].str.replace(
                    r'[^\d]', '', regex=True) == nit
            ]

            if clientes.empty:
                return False, []

            activos = clientes[clientes['estado'].str.upper() == 'ACTIVO']

            if activos.empty:
                return False, []

            return True, activos.to_dict('records')
        except:
            return False, []

    def buscar_productos(self, texto: str, lista_precio: str) -> List[Dict]:
        """Buscar productos por texto mejorado"""
        try:
            if self.df_productos.empty:
                return []

            productos_lista = self.df_productos[
                self.df_productos['lista_precio'] == int(lista_precio)
            ]

            if productos_lista.empty:
                return []

            # Búsqueda mejorada por descripción
            texto_lower = texto.lower()

            # Búsqueda exacta primero
            productos_exactos = productos_lista[
                productos_lista['descripcion'].str.lower().str.contains(
                    re.escape(texto_lower), na=False, regex=True)
            ]

            if not productos_exactos.empty:
                return productos_exactos.head(10).to_dict('records')

            # Búsqueda por palabras clave
            palabras = texto_lower.split()
            if len(palabras) > 1:
                patron = '.*'.join([re.escape(palabra)
                                   for palabra in palabras])
                productos_palabras = productos_lista[
                    productos_lista['descripcion'].str.lower().str.contains(
                        patron, na=False, regex=True)
                ]

                if not productos_palabras.empty:
                    return productos_palabras.head(10).to_dict('records')

            # Búsqueda fuzzy por primera palabra
            if palabras:
                primera_palabra = palabras[0]
                if len(primera_palabra) > 3:
                    productos_fuzzy = productos_lista[
                        productos_lista['descripcion'].str.lower().str.contains(
                            primera_palabra, na=False)
                    ]

                    if not productos_fuzzy.empty:
                        return productos_fuzzy.head(10).to_dict('records')

            return []
        except Exception as e:
            print(f"Error en buscar_productos: {e}")
            return []

    def agregar_al_carrito(self, session_data: dict, cantidad: int) -> bool:
        """Agregar producto al carrito"""
        try:
            producto = session_data.get('producto_temporal', {})
            carrito = session_data.get('productos_carrito', [])

            precio_unitario = producto.get('precio_mas_iva', 0)
            subtotal = precio_unitario * cantidad

            nuevo_item = {
                'codigo': producto.get('codigo', ''),
                'descripcion': producto.get('descripcion', ''),
                'precio_unitario': precio_unitario,
                'cantidad': cantidad,
                'subtotal': subtotal,
                'iva': producto.get('iva', 19),
                'p_descuento': producto.get('p_descuento', 0)  # Para el CSV
            }

            carrito.append(nuevo_item)
            session_data['productos_carrito'] = carrito
            return True
        except Exception as e:
            print(f"Error agregando al carrito: {e}")
            return False

    def generar_cotizacion(self, session_data: dict) -> Optional[Dict]:
        """Generar cotización final"""
        try:
            carrito = session_data.get('productos_carrito', [])
            sede = session_data.get('sede_seleccionada', {})
            vendedor_info = session_data.get('vendedor_info', {})

            if not carrito:
                return None

            subtotal = sum(item.get('subtotal', 0) for item in carrito)
            iva = subtotal * 0.19
            total = subtotal + iva

            numero = f"COT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            return {
                'numero_cotizacion': numero,
                'fecha': datetime.now().isoformat(),
                'cliente_nit': sede.get('nit_principal', ''),
                'cliente_nombre': sede.get('razon', ''),
                'vendedor': vendedor_info.get('seller', ''),
                'productos': carrito,
                'subtotal': subtotal,
                'iva': iva,
                'total': total,
                'estado': 'generada',
                'canal': 'chatbot'
            }
        except Exception as e:
            print(f"Error generando cotización: {e}")
            return None

    def guardar_cotizacion(self, cotizacion: Dict) -> bool:
        """Guardar cotización en Firebase"""
        try:
            db = self._get_db()
            if not db:
                return False

            path = f"cotizaciones/{cotizacion['numero_cotizacion']}"
            return db.update_by_path(path, cotizacion)
        except Exception as e:
            print(f"Error guardando cotización: {e}")
            return False

    def generar_excel_cotizacion(self, session_data: dict) -> Optional[bytes]:
        """Generar Excel de cotización mejorado"""
        try:
            cotizacion = session_data.get('cotizacion_final')
            if not cotizacion:
                return None

            df = pd.DataFrame(cotizacion['productos'])

            # Renombrar columnas
            df = df.rename(columns={
                'codigo': 'Código',
                'descripcion': 'Descripción',
                'cantidad': 'Cantidad',
                'precio_unitario': 'Precio Unitario',
                'subtotal': 'Precio Total'
            })

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Cotización',
                            index=False, startrow=8)

                workbook = writer.book
                worksheet = writer.sheets['Cotización']

                # Encabezado mejorado
                worksheet['A1'] = 'COTIZACIÓN EMES S.A.S'
                worksheet['A1'].font = Font(size=16, bold=True)

                worksheet['A3'] = f"Número: {cotizacion['numero_cotizacion']}"
                worksheet['A4'] = f"Cliente: {cotizacion['cliente_nombre']}"
                worksheet['A5'] = f"Vendedor: {cotizacion['vendedor']}"
                worksheet['A6'] = f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}"

                # Totales
                start_row = 9 + len(df)
                worksheet[f'D{start_row + 1}'] = 'Subtotal:'
                worksheet[f'E{start_row + 1}'] = cotizacion['subtotal']
                worksheet[f'D{start_row + 2}'] = 'IVA:'
                worksheet[f'E{start_row + 2}'] = cotizacion['iva']
                worksheet[f'D{start_row + 3}'] = 'TOTAL:'
                worksheet[f'E{start_row + 3}'] = cotizacion['total']

                # Estilo para totales
                for row in range(start_row + 1, start_row + 4):
                    worksheet[f'D{row}'].font = Font(bold=True)
                    worksheet[f'E{row}'].font = Font(bold=True)

            output.seek(0)
            return output.read()
        except Exception as e:
            print(f"Error generando Excel: {e}")
            return None

    def get_historial_cotizaciones(self, vendedor='Todos', limite=50):
        """Obtener historial"""
        try:
            if self.df_cotizaciones.empty:
                return pd.DataFrame()

            df = self.df_cotizaciones.copy()
            if vendedor != 'Todos':
                df = df[df['vendedor'] == vendedor]

            return df.sort_values('fecha', ascending=False).head(limite)
        except:
            return pd.DataFrame()

    # NUEVOS MÉTODOS PARA MANEJO DE ARCHIVOS
    def procesar_archivo_subido(self, archivo_base64: str, filename: str, session_data: dict) -> Tuple[str, dict]:
        """
        Procesar archivo subido (imagen o Excel) y extraer productos.
        """
        try:
            excel_processor = ExcelProcessor()
            image_processor = ImageProcessor()

            if filename.lower().endswith(('.xlsx', '.xls')):
                # Procesar Excel
                import base64
                excel_data = base64.b64decode(archivo_base64)
                resultado = excel_processor.process_excel_file(
                    excel_data, filename)

                if resultado['success']:
                    productos_texto = excel_processor.create_products_text_for_chatbot(
                        resultado['productos'])

                    # Guardar en session_data para confirmación
                    session_data['productos_desde_archivo'] = {
                        'texto': productos_texto,
                        'productos': resultado['productos'],
                        'tipo': 'excel'
                    }
                    session_data['estado'] = 'confirmando_productos_archivo'

                    mensaje = resultado['mensaje'] + \
                        "\n\n🤖 **¿Continuar con estos productos?** (sí/no)"
                    return mensaje, session_data
                else:
                    return resultado['mensaje'], session_data

            elif filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                # Procesar imagen
                resultado = image_processor.process_image_base64(
                    archivo_base64, filename)

                if resultado['success']:
                    productos_texto = image_processor.create_products_text_for_chatbot(
                        resultado['productos'])

                    # Guardar en session_data para confirmación
                    session_data['productos_desde_archivo'] = {
                        'texto': productos_texto,
                        'productos': resultado['productos'],
                        'tipo': 'imagen'
                    }
                    session_data['estado'] = 'confirmando_productos_archivo'

                    mensaje = resultado['mensaje'] + \
                        "\n\n🤖 **¿Continuar con estos productos?** (sí/no)"
                    return mensaje, session_data
                else:
                    return resultado['mensaje'], session_data
            else:
                return f"❌ Tipo de archivo no soportado: {filename}", session_data

        except Exception as e:
            return f"❌ Error procesando archivo: {str(e)}", session_data

    # MÉTODO ALIAS PARA COMPATIBILIDAD
    def procesar_mensaje_agente(self, mensaje: str, session_data: dict, vendedor_info: dict) -> Tuple[str, dict]:
        """Alias para compatibilidad"""
        return self.procesar_mensaje_chatbot(mensaje, session_data, vendedor_info)

import re
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from server import get_db


class FacturasProveedoresAnalyzer:
    """
    Procesador de facturas que obtiene datos directamente de Firebase
    """

    def __init__(self):
        """
        Initialize the Firebase Invoice Processor
        """
        self.db = get_db()
        if not self.db:
            raise Exception("No se pudo conectar a la base de datos")

        self.processed_data = {}
        self.proveedores_data = {}

    def process_invoices(self, proveedor_filter: str = None, date_range: tuple = None) -> Dict[str, Dict[str, Any]]:
        """
        Procesar facturas desde Firebase siguiendo la lógica original

        Args:
            proveedor_filter (str, optional): Filtro para proveedor específico
            date_range (tuple, optional): Tupla con (fecha_inicio, fecha_fin) para filtrar por fecha_cargue

        Returns:
            Dict[str, Dict[str, Any]]: Datos procesados de facturas
        """
        try:
            # Cargar datos desde Firebase
            facturas_data = self._load_facturas_data()
            recibos_data = self._load_recibos_data()

            if not facturas_data:
                print("⚠️ No se encontraron facturas en Firebase")
                return {}

            # Cargar términos de pago de proveedores
            self._load_proveedores_data()

            # Procesar y hacer matching
            processed_invoices = self._process_facturas_like_original(
                facturas_data,
                recibos_data,
                proveedor_filter,
                date_range
            )

            return processed_invoices

        except Exception as e:
            logging.error(
                f"Error procesando facturas desde Firebase: {e}", exc_info=True)
            return {}

    def _load_facturas_data(self) -> Dict[str, Any]:
        """
        Cargar datos de facturas desde Firebase
        Estructura esperada: recepcion/facturas/[orden_key]/invoices/[invoice_id]
        """
        try:
            facturas = self.db.get_by_path("recepcion/facturas")

            if not facturas:
                print("⚠️ No se encontraron datos en recepcion/facturas")
                return {}

            return facturas

        except Exception as e:
            print(f"❌ Error cargando facturas: {e}")
            logging.error(f"Error cargando facturas: {e}")
            return {}

    def _load_recibos_data(self) -> Dict[str, Any]:
        """
        Cargar datos de recibos/órdenes desde Firebase
        Estructura esperada: recepcion/recibos/[recibo_id]
        """
        try:
            recibos = self.db.get_by_path("recepcion/recibos")

            if not recibos:
                print("⚠️ No se encontraron datos en recepcion/recibos")
                return {}

            return recibos

        except Exception as e:
            print(f"❌ Error cargando recibos: {e}")
            logging.error(f"Error cargando recibos: {e}")
            return {}

    def _load_proveedores_data(self) -> None:
        """
        Cargar datos de proveedores para obtener términos de pago
        """
        try:
            # Buscar en permisos/cuentas como en auth_manager.py
            accounts = self.db.get_by_path("permisos/cuentas")

            if accounts:
                self.proveedores_data.update(accounts)

            # Intentar otras rutas posibles
            proveedores_paths = [
                "proveedores",
                "proveedores_id",
                "configuracion/proveedores"
            ]

            for path in proveedores_paths:
                proveedores = self.db.get_by_path(path)

                if proveedores:
                    self.proveedores_data.update(proveedores)

        except Exception as e:
            print(f"❌ Error cargando proveedores: {e}")
            logging.error(f"Error cargando proveedores: {e}")

    def _process_facturas_like_original(
        self,
        facturas_data: Dict[str, Any],
        recibos_data: Dict[str, Any],
        proveedor_filter: str = None,
        date_range: tuple = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Procesar facturas siguiendo la lógica del código original
        """
        processed_invoices = {}

        try:
            # Crear lookup de recibos por proveedor
            recibos_by_supplier = self._create_recibos_lookup(recibos_data)

            # Procesar facturas
            for orden_key, orden_data in facturas_data.items():
                if not isinstance(orden_data, dict):
                    continue

                # Buscar invoices dentro de orden_data
                invoices = orden_data.get('invoices', {})
                if not invoices:
                    continue

                # Obtener supplier name y forma de pago
                supplier_name = orden_data.get('supplier', '')
                forma_pago = orden_data.get('forma_pago', '')
                
                if not forma_pago:
                    continue
                
                if not supplier_name:
                    continue

                # Aplicar filtro de proveedor si existe
                if proveedor_filter != "Todos":
                    if proveedor_filter and supplier_name != proveedor_filter:
                        continue

                for invoice_id, invoice_data in invoices.items():
                    if not isinstance(invoice_data, dict):
                        continue

                    # Obtener fecha_cargue de la factura
                    fecha_cargue_str = invoice_data.get('fecha_cargue', '')
                    
                    if not fecha_cargue_str:
                        continue
                    
                    # Aplicar filtro de fecha si existe
                    if date_range and fecha_cargue_str:
                        try:
                            # Intentar diferentes formatos de fecha
                            fecha_cargue = None
                            for formato in ["%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                                try:
                                    fecha_cargue = datetime.strptime(fecha_cargue_str, formato)
                                    break
                                except ValueError:
                                    continue
                            
                            if fecha_cargue:
                                fecha_inicio, fecha_fin = date_range
                                
                                # Asegurar que las fechas de rango sean objetos date
                                if hasattr(fecha_inicio, 'date'):
                                    fecha_inicio = fecha_inicio.date()
                                if hasattr(fecha_fin, 'date'):
                                    fecha_fin = fecha_fin.date()
                                
                                if not (fecha_inicio <= fecha_cargue.date() <= fecha_fin):
                                    continue
                            else:
                                print(f"No se pudo parsear fecha_cargue: {fecha_cargue_str}")
                                
                        except Exception as e:
                            print(f"Error procesando fecha_cargue {fecha_cargue_str}: {e}")
                            # Si hay error parseando, incluir la factura

                    # Calcular fecha de vencimiento
                    fecha_vcto_str, dias_vencidos = self._calculate_fecha_vencimiento(
                        fecha_cargue_str, forma_pago
                    )

                    # Calcular días desde cargue
                    dias_cargue = self._calculate_dias_cargue(fecha_cargue_str)

                    # Obtener productos de la factura
                    products = invoice_data.get('products', {})

                    # Calcular valores siguiendo la lógica original
                    valor_factura = self._calculate_invoice_total_original(products)

                    # Calcular valor nota siguiendo la lógica original
                    valor_nota = self._calculate_nota_original(
                        invoice_id,
                        products,
                        forma_pago,
                        [orden_key],  # El orden_key es la orden principal
                        recibos_data
                    )

                    processed_invoices[invoice_id] = {
                        'factura': invoice_id,
                        'orden': orden_key,  # El key principal es la orden
                        'proveedor': supplier_name,
                        'valor_factura': valor_factura,
                        'valor_nota': valor_nota,
                        'forma_pago': forma_pago,
                        'fecha_vcto': fecha_vcto_str,
                        'dias_vencidos': dias_vencidos,
                        'fecha_cargue': fecha_cargue_str,
                        'dias_cargue': dias_cargue,
                        'productos': products,
                        'estado': invoice_data.get('state', 1),  # Incluir el estado de la factura
                        'orden_key': orden_key  # Guardar orden_key para actualizaciones
                    }

            return processed_invoices

        except Exception as e:
            print(f"❌ Error en _process_facturas_like_original: {e}")
            logging.error(
                f"Error en _process_facturas_like_original: {e}", exc_info=True)
            return {}

    def _calculate_fecha_vencimiento(self, fecha_cargue_str: str, forma_pago: str) -> tuple:
        """
        Calcular fecha de vencimiento y días vencidos
        
        Args:
            fecha_cargue_str: String de fecha en formato "DD/MM/YYYY HH:MM"
            forma_pago: String como "Prov 60 días neto"
            
        Returns:
            tuple: (fecha_vcto_str, dias_vencidos)
        """
        if not fecha_cargue_str:
            return '', 0
            
        try:
            # Intentar diferentes formatos de fecha
            fecha_cargue = None
            
            for formato in ["%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                try:
                    fecha_cargue = datetime.strptime(fecha_cargue_str, formato)
                    break
                except ValueError:
                    continue
            
            if not fecha_cargue:
                print(f"No se pudo parsear fecha_cargue: {fecha_cargue_str}")
                return '', 0
            
            # Extraer días de la forma de pago
            dias_pago = self._extract_dias_from_forma_pago(forma_pago)
            
            # Calcular fecha de vencimiento
            fecha_vcto = fecha_cargue + timedelta(days=dias_pago)
            fecha_vcto_str = fecha_vcto.strftime("%d/%m/%Y")
            
            # Calcular días vencidos (negativos si aún no vence)
            hoy = datetime.now()
            dias_vencidos = (hoy - fecha_vcto).days
            
            return fecha_vcto_str, dias_vencidos
            
        except Exception as e:
            print(f"Error parseando fecha_cargue: {fecha_cargue_str} - {e}")
            return '', 0

    def _extract_dias_from_forma_pago(self, forma_pago: str) -> int:
        """
        Extraer número de días de la forma de pago - MEJORADO para manejar "días" y "dias"
        
        Args:
            forma_pago: String como "Prov 60 días neto", "Prov 30 dias 2%" o "Contado 0%"
            
        Returns:
            int: Número de días
        """
        if not forma_pago:
            return 0
            
        # Buscar patrón de días - MEJORADO para capturar ambos casos
        # Patrones posibles: "30 días", "30 dias", "30dias", "30 día", "30 dia"
        patterns = [
            r'(\d+)\s*d[ií]as?',  # "30 días", "30 dias", "30 día", "30 dia"
            r'(\d+)\s*d[ií]a',    # "30 día", "30 dia" (singular)
            r'(\d+)d[ií]as?',     # "30días", "30dias" (sin espacio)
            r'(\d+)\s*day?s?'     # Por si acaso hay algo en inglés
        ]
        
        forma_pago_lower = forma_pago.lower()
        
        for pattern in patterns:
            match = re.search(pattern, forma_pago_lower)
            
            if match:
                dias = int(match.group(1))
                return dias
        
        # Si es contado, son 0 días
        if 'contado' in forma_pago_lower:
            return 0
            
        return 0

    def _calculate_dias_cargue(self, fecha_cargue_str: str) -> int:
        """
        Calcular días transcurridos desde el cargue
        
        Args:
            fecha_cargue_str: String de fecha en formato "DD/MM/YYYY HH:MM"
            
        Returns:
            int: Días desde el cargue
        """
        if not fecha_cargue_str:
            return 0
            
        try:
            # Intentar diferentes formatos de fecha
            fecha_cargue = None
            for formato in ["%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
                try:
                    fecha_cargue = datetime.strptime(fecha_cargue_str, formato)
                    break
                except ValueError:
                    continue
            
            if not fecha_cargue:
                print(f"No se pudo parsear fecha_cargue: {fecha_cargue_str}")
                return 0
                
            hoy = datetime.now()
            dias_cargue = (hoy - fecha_cargue).days
            return max(0, dias_cargue)  # No puede ser negativo
            
        except Exception as e:
            print(f"Error parseando fecha_cargue: {fecha_cargue_str} - {e}")
            return 0

    def _create_recibos_lookup(self, recibos_data: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """
        Crear lookup de recibos organizados por proveedor
        """
        lookup = {}

        for recibo_id, recibo_data in recibos_data.items():
            if not isinstance(recibo_data, dict):
                continue

            supplier = recibo_data.get('supplier', '')
            if supplier:
                if supplier not in lookup:
                    lookup[supplier] = []

                recibo_info = {
                    'recibo_id': recibo_id,
                    'order': recibo_data.get('order', ''),
                    'products': recibo_data.get('products', {}),
                    'fecha': recibo_data.get('fecha', ''),
                    'estado': recibo_data.get('estado', 1)
                }
                lookup[supplier].append(recibo_info)

        return lookup

    def _find_orders_for_supplier(self, supplier_name: str, recibos_lookup: Dict[str, List[Dict]]) -> List[str]:
        """
        Encontrar números de orden para un proveedor específico
        """
        orders = []

        if supplier_name in recibos_lookup:
            for recibo in recibos_lookup[supplier_name]:
                order_num = recibo.get('order', '')
                if order_num and order_num not in orders:
                    orders.append(order_num)

        return orders

    def _calculate_invoice_total_original(self, products: Dict[str, Any]) -> float:
        """
        Calcular total de la factura siguiendo la lógica original
        """
        total = 0.0

        for product_data in products.values():
            if isinstance(product_data, dict):
                subtotal = product_data.get('subtotal', 0.0)
                total += subtotal

        return total

    def _get_payment_terms_original(self, supplier_name: str) -> str:
        """
        Obtener términos de pago del proveedor siguiendo la lógica original
        """
        # Buscar en los datos de proveedores cargados
        for proveedor_id, proveedor_data in self.proveedores_data.items():
            if isinstance(proveedor_data, dict):
                stored_supplier = proveedor_data.get('supplier', '')
                if stored_supplier == supplier_name:
                    return proveedor_data.get('forma_pago', 'Contado 0%')

        return 'Contado 0%'

    def _calculate_nota_original(
        self,
        invoice_id: str,
        invoice_products: Dict[str, Any],
        forma_pago: str,
        related_orders: List[str],
        recibos_data: Dict[str, Any]
    ) -> float:
        """
        Calcular valor de nota siguiendo exactamente la lógica original
        """
        # Extraer porcentaje de descuento
        discount_match = re.search(r'(\d+)%', forma_pago or "0%")
        discount_percentage = float(
            discount_match.group(1)) if discount_match else 0
        discount_factor = 1 - (discount_percentage / 100)

        # Crear lookup de productos en órdenes relacionadas
        order_products_lookup = {}
        for recibo_data in recibos_data.values():
            if isinstance(recibo_data, dict):
                order_num = recibo_data.get('order', '')
                if order_num in related_orders:
                    products = recibo_data.get('products', {})
                    for product_code, product_data in products.items():
                        if isinstance(product_data, dict):
                            if product_code not in order_products_lookup:
                                order_products_lookup[product_code] = []
                            order_products_lookup[product_code].append({
                                'cost': product_data.get('cost', 0),
                                'quantity': product_data.get('quantity', 0)
                            })

        # Procesar productos de la factura
        differences = []

        for product_code, invoice_product in invoice_products.items():
            if not isinstance(invoice_product, dict):
                continue

            # Obtener datos de la factura
            valor_factura = invoice_product.get('cost', 0.0)

            # Calcular cantidad de la factura
            cantidad = 0
            distribution = invoice_product.get('distribution', {})
            for dist_data in distribution.values():
                if isinstance(dist_data, dict):
                    cantidad += dist_data.get('cantidad', 0)

            # Buscar valor de orden correspondiente
            valor_orden = 0.0
            if product_code in order_products_lookup:
                # Usar el primer producto encontrado en las órdenes
                order_product = order_products_lookup[product_code][0]
                valor_orden = order_product.get('cost', 0.0)

            # Aplicar la lógica original: if (valor_factura - valor_orden) >= 50
            if (valor_factura - valor_orden) >= 50:
                # valor_factura * cantidad * (1 – d) – valor_orden * cantidad
                diferencia = (
                    valor_factura * cantidad * discount_factor -
                    valor_orden * cantidad
                )
                differences.append(diferencia)

        return sum(differences)

    def get_suppliers_list(self) -> List[str]:
        """
        Obtener lista de proveedores únicos
        """
        suppliers = set()

        try:
            facturas_data = self._load_facturas_data()
            for orden_data in facturas_data.values():
                if isinstance(orden_data, dict):
                    supplier_name = orden_data.get('supplier', '')
                    if supplier_name:
                        suppliers.add(supplier_name)

        except Exception as e:
            print(f"❌ Error obteniendo lista de proveedores: {e}")
            logging.error(f"Error obteniendo lista de proveedores: {e}")

        return sorted(list(suppliers))

    def update_invoice_state(self, invoice_id: str, new_state: int) -> bool:
        """
        Actualizar el estado de una factura en Firebase
        
        Args:
            invoice_id: ID de la factura
            new_state: Nuevo estado (1-4)
            
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            # Cargar datos de facturas para encontrar la ruta correcta
            facturas_data = self._load_facturas_data()
            
            # Buscar la factura en los datos
            for orden_key, orden_data in facturas_data.items():
                if isinstance(orden_data, dict):
                    invoices = orden_data.get('invoices', {})
                    if invoice_id in invoices:
                        # Construir la ruta completa
                        path = f"recepcion/facturas/{orden_key}/invoices/{invoice_id}"
                        
                        # Actualizar solo el campo state
                        update_data = {"state": new_state}
                        
                        success = self.db.update_by_path(path, update_data)
                        
                        if success:
                            print(f"✅ Estado de factura {invoice_id} actualizado a {new_state}")
                        else:
                            print(f"❌ Error actualizando estado de factura {invoice_id}")
                            
                        return success
            
            print(f"❌ Factura {invoice_id} no encontrada")
            return False
            
        except Exception as e:
            print(f"❌ Error actualizando estado de factura {invoice_id}: {e}")
            logging.error(f"Error actualizando estado de factura {invoice_id}: {e}")
            return False

    def get_invoice_details(self, invoice_id: str) -> Dict[str, Any]:
        """
        Obtener detalles completos de una factura específica
        
        Args:
            invoice_id: ID de la factura
            
        Returns:
            Dict con los detalles de la factura
        """
        try:
            facturas_data = self._load_facturas_data()
            
            for orden_key, orden_data in facturas_data.items():
                if isinstance(orden_data, dict):
                    invoices = orden_data.get('invoices', {})
                    if invoice_id in invoices:
                        invoice_data = invoices[invoice_id]
                        
                        return {
                            'invoice_id': invoice_id,
                            'orden_key': orden_key,
                            'supplier': orden_data.get('supplier', ''),
                            'forma_pago': orden_data.get('forma_pago', ''),
                            'fecha_cargue': invoice_data.get('fecha_cargue', ''),
                            'state': invoice_data.get('state', 1),
                            'products': invoice_data.get('products', {})
                        }
            
            return {}
            
        except Exception as e:
            print(f"❌ Error obteniendo detalles de factura {invoice_id}: {e}")
            return {}
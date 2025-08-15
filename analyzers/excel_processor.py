import pandas as pd
import io
import re
from typing import List, Dict, Tuple, Optional


class ExcelProcessor:
    """
    Procesador avanzado de archivos Excel para extraer productos y cotizaciones.
    """

    def __init__(self):
        # Columnas posibles para productos
        self.product_columns = [
            'producto', 'productos', 'medicamento', 'medicamentos',
            'descripcion', 'descripción', 'item', 'items',
            'codigo', 'código', 'cod', 'sku', 'referencia'
        ]

        # Columnas posibles para cantidades
        self.quantity_columns = [
            'cantidad', 'cant', 'qty', 'quantity', 'unidades',
            'uni', 'piezas', 'pzs', 'cajas', 'cx'
        ]

        # Columnas posibles para laboratorios
        self.lab_columns = [
            'laboratorio', 'lab', 'marca', 'proveedor',
            'fabricante', 'casa', 'empresa'
        ]

        # Columnas posibles para precios
        self.price_columns = [
            'precio', 'valor', 'costo', 'price', 'cost',
            'precio_unitario', 'valor_unitario', 'pu'
        ]

    def process_excel_file(self, excel_data: bytes, filename: str = '') -> Dict:
        """
        Procesar archivo Excel y extraer información de productos.
        """
        try:
            # Leer archivo Excel
            excel_buffer = io.BytesIO(excel_data)

            # Intentar leer con diferentes engines
            df = self._read_excel_safely(excel_buffer)

            if df is None or df.empty:
                return {
                    'success': False,
                    'error': 'No se pudo leer el archivo o está vacío',
                    'mensaje': f"❌ Error: El archivo {filename} está vacío o no es válido"
                }

            # Analizar estructura del archivo
            estructura = self._analyze_structure(df)

            # Extraer productos según la estructura identificada
            productos = self._extract_products_from_dataframe(df, estructura)

            # Generar mensaje de resultado
            mensaje = self._generate_result_message(
                productos, estructura, filename)

            return {
                'success': True,
                'productos': productos,
                'estructura': estructura,
                'mensaje': mensaje,
                'dataframe_info': {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'columns_names': df.columns.tolist()
                }
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'mensaje': f"❌ Error procesando Excel {filename}: {str(e)}"
            }

    def _read_excel_safely(self, excel_buffer: io.BytesIO) -> Optional[pd.DataFrame]:
        """
        Leer archivo Excel de forma segura con diferentes métodos.
        """
        engines = ['openpyxl', 'xlrd']

        for engine in engines:
            try:
                excel_buffer.seek(0)  # Resetear posición

                # Intentar leer todas las hojas
                excel_file = pd.ExcelFile(excel_buffer, engine=engine)

                # Usar la primera hoja con datos
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    if not df.empty and len(df.columns) > 0:
                        return self._clean_dataframe(df)

            except Exception as e:
                print(f"Error con engine {engine}: {e}")
                continue

        return None

    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpiar DataFrame eliminando filas y columnas vacías.
        """
        # Eliminar filas completamente vacías
        df = df.dropna(how='all')

        # Eliminar columnas completamente vacías
        df = df.dropna(axis=1, how='all')

        # Limpiar nombres de columnas
        df.columns = [str(col).strip().lower() for col in df.columns]

        # Resetear índice
        df = df.reset_index(drop=True)

        return df

    def _analyze_structure(self, df: pd.DataFrame) -> Dict:
        """
        Analizar la estructura del DataFrame para identificar columnas relevantes.
        """
        estructura = {
            'tipo_archivo': 'desconocido',
            'columna_producto': None,
            'columna_cantidad': None,
            'columna_laboratorio': None,
            'columna_precio': None,
            'tiene_encabezados': True,
            'filas_datos': len(df),
            'confianza': 0.0
        }

        columnas = df.columns.tolist()

        # Identificar columna de productos
        for col in columnas:
            for pattern in self.product_columns:
                if pattern in col.lower():
                    estructura['columna_producto'] = col
                    estructura['confianza'] += 0.3
                    break
            if estructura['columna_producto']:
                break

        # Identificar columna de cantidad
        for col in columnas:
            for pattern in self.quantity_columns:
                if pattern in col.lower():
                    estructura['columna_cantidad'] = col
                    estructura['confianza'] += 0.2
                    break
            if estructura['columna_cantidad']:
                break

        # Identificar columna de laboratorio
        for col in columnas:
            for pattern in self.lab_columns:
                if pattern in col.lower():
                    estructura['columna_laboratorio'] = col
                    estructura['confianza'] += 0.2
                    break
            if estructura['columna_laboratorio']:
                break

        # Identificar columna de precio
        for col in columnas:
            for pattern in self.price_columns:
                if pattern in col.lower():
                    estructura['columna_precio'] = col
                    estructura['confianza'] += 0.2
                    break
            if estructura['columna_precio']:
                break

        # Si no se encontró columna de producto, usar la primera
        if not estructura['columna_producto'] and len(columnas) > 0:
            estructura['columna_producto'] = columnas[0]
            estructura['confianza'] += 0.1

        # Determinar tipo de archivo
        if estructura['columna_producto'] and estructura['columna_cantidad']:
            if estructura['columna_laboratorio']:
                estructura['tipo_archivo'] = 'cotizacion_completa'
            else:
                estructura['tipo_archivo'] = 'lista_productos'
        elif estructura['columna_producto']:
            estructura['tipo_archivo'] = 'lista_simple'

        return estructura

    def _extract_products_from_dataframe(self, df: pd.DataFrame, estructura: Dict) -> List[Dict]:
        """
        Extraer productos del DataFrame según la estructura identificada.
        """
        productos = []

        if not estructura['columna_producto']:
            return productos

        for idx, row in df.iterrows():
            try:
                # Obtener nombre del producto
                producto_raw = row[estructura['columna_producto']]
                if pd.isna(producto_raw) or str(producto_raw).strip() == '':
                    continue

                producto_nombre = str(producto_raw).strip()

                # Saltear filas que parecen encabezados
                if self._is_header_row(producto_nombre):
                    continue

                # Extraer información del producto
                producto_info = self._parse_product_info(producto_nombre)

                # Obtener cantidad
                cantidad = self._extract_quantity_from_row(row, estructura)

                # Obtener laboratorio si existe
                laboratorio = self._extract_lab_from_row(row, estructura)

                # Obtener precio si existe
                precio = self._extract_price_from_row(row, estructura)

                # Crear objeto producto
                producto = {
                    'producto_original': producto_nombre,
                    'producto_limpio': producto_info['nombre'],
                    'dosificacion': producto_info['dosificacion'],
                    'presentacion': producto_info['presentacion'],
                    'cantidad': cantidad,
                    'laboratorio': laboratorio,
                    'precio_sugerido': precio,
                    'fila_origen': idx + 1,
                    'confianza': self._calculate_product_confidence(producto_info, cantidad, laboratorio)
                }

                productos.append(producto)

            except Exception as e:
                print(f"Error procesando fila {idx}: {e}")
                continue

        return productos

    def _is_header_row(self, texto: str) -> bool:
        """
        Determinar si una fila es probablemente un encabezado.
        """
        texto_lower = texto.lower()
        header_keywords = [
            'producto', 'medicamento', 'descripcion', 'cantidad',
            'laboratorio', 'precio', 'item', 'codigo'
        ]

        return any(keyword in texto_lower for keyword in header_keywords)

    def _parse_product_info(self, producto_raw: str) -> Dict:
        """
        Extraer información detallada del nombre del producto.
        """
        # Limpiar texto
        producto = re.sub(r'[^\w\s\-\.\,\(\)\/]', ' ', producto_raw)
        producto = re.sub(r'\s+', ' ', producto).strip()

        # Extraer dosificación
        dosificacion_patterns = [
            r'\d+\s*mg', r'\d+\s*gr?', r'\d+\s*ml',
            r'\d+\s*mcg', r'\d+\s*ug', r'\d+\s*ui',
            r'\d+\s*%', r'\d+\s*x\s*\d+'
        ]

        dosificacion = ""
        for pattern in dosificacion_patterns:
            match = re.search(pattern, producto, re.IGNORECASE)
            if match:
                dosificacion = match.group().strip()
                # Remover de nombre principal
                producto = re.sub(pattern, ' ', producto,
                                  flags=re.IGNORECASE).strip()
                break

        # Extraer presentación
        presentaciones = [
            'tabletas', 'tablet', 'tab', 'caps', 'capsulas', 'capsula',
            'jarabe', 'suspension', 'gotas', 'ampolla', 'inyectable',
            'crema', 'pomada', 'gel', 'unguento', 'solucion'
        ]

        presentacion = ""
        for pres in presentaciones:
            if pres in producto.lower():
                presentacion = pres.upper()
                # Remover de nombre principal
                producto = re.sub(pres, ' ', producto,
                                  flags=re.IGNORECASE).strip()
                break

        # Limpiar nombre final
        nombre = re.sub(r'\s+', ' ', producto).strip()

        return {
            'nombre': nombre.upper(),
            'dosificacion': dosificacion.upper(),
            'presentacion': presentacion or 'TABLETAS'
        }

    def _extract_quantity_from_row(self, row: pd.Series, estructura: Dict) -> int:
        """
        Extraer cantidad de la fila.
        """
        if estructura['columna_cantidad']:
            try:
                cantidad_raw = row[estructura['columna_cantidad']]
                if pd.notna(cantidad_raw):
                    # Extraer número de la celda
                    cantidad_str = str(cantidad_raw)
                    match = re.search(r'(\d+)', cantidad_str)
                    if match:
                        return int(match.group(1))
            except:
                pass

        return 1  # Cantidad por defecto

    def _extract_lab_from_row(self, row: pd.Series, estructura: Dict) -> str:
        """
        Extraer laboratorio de la fila.
        """
        if estructura['columna_laboratorio']:
            try:
                lab_raw = row[estructura['columna_laboratorio']]
                if pd.notna(lab_raw):
                    return str(lab_raw).strip().upper()
            except:
                pass

        return ""

    def _extract_price_from_row(self, row: pd.Series, estructura: Dict) -> float:
        """
        Extraer precio de la fila.
        """
        if estructura['columna_precio']:
            try:
                precio_raw = row[estructura['columna_precio']]
                if pd.notna(precio_raw):
                    # Limpiar y convertir precio
                    precio_str = str(precio_raw).replace(
                        ',', '').replace('$', '')
                    match = re.search(r'(\d+\.?\d*)', precio_str)
                    if match:
                        return float(match.group(1))
            except:
                pass

        return 0.0

    def _calculate_product_confidence(self, producto_info: Dict, cantidad: int, laboratorio: str) -> float:
        """
        Calcular confianza de extracción del producto.
        """
        confianza = 0.3  # Base

        # Bonificación por nombre válido
        if len(producto_info['nombre']) > 3:
            confianza += 0.3

        # Bonificación por dosificación
        if producto_info['dosificacion']:
            confianza += 0.2

        # Bonificación por cantidad válida
        if cantidad > 0:
            confianza += 0.1

        # Bonificación por laboratorio
        if laboratorio:
            confianza += 0.1

        return min(confianza, 1.0)

    def _generate_result_message(self, productos: List[Dict], estructura: Dict, filename: str) -> str:
        """
        Generar mensaje amigable con los resultados del procesamiento.
        """
        if not productos:
            return f"""📊 **Archivo Excel procesado: {filename}**

❌ **No se encontraron productos válidos**

📋 **Información del archivo:**
• Filas: {estructura['filas_datos']}
• Tipo detectado: {estructura['tipo_archivo']}
• Confianza: {estructura['confianza']*100:.0f}%

💡 **Sugerencias:**
• Verifica que haya una columna con nombres de productos
• Asegúrate de que el archivo no esté vacío
• Intenta con un formato más claro

🤖 **¿Puedes escribir manualmente los productos?**"""

        mensaje = f"""📊 **¡Excel procesado exitosamente!** {filename}

✅ **{len(productos)} productos extraídos** (Confianza: {estructura['confianza']*100:.0f}%)

📋 **Tipo de archivo:** {estructura['tipo_archivo'].replace('_', ' ').title()}

"""

        # Mostrar primeros productos
        productos_mostrar = productos[:5]
        for i, producto in enumerate(productos_mostrar, 1):
            confianza = producto['confianza'] * 100
            emoji_confianza = "🟢" if confianza > 70 else "🟡" if confianza > 40 else "🔴"

            descripcion_completa = producto['producto_limpio']
            if producto['dosificacion']:
                descripcion_completa += f" {producto['dosificacion']}"
            if producto['presentacion']:
                descripcion_completa += f" {producto['presentacion']}"

            mensaje += f"""**{i}.** {emoji_confianza} {descripcion_completa}
   🔢 Cantidad: {producto['cantidad']}"""

            if producto['laboratorio']:
                mensaje += f"\n   🏭 Laboratorio: {producto['laboratorio']}"

            mensaje += f"\n   🎯 Confianza: {confianza:.0f}%\n\n"

        if len(productos) > 5:
            mensaje += f"_... y {len(productos) - 5} productos más_\n\n"

        mensaje += """🤖 **¿Los productos identificados son correctos?**

💬 **Opciones:**
• Escribe "sí" para continuar con estos productos
• Escribe "no" para hacer correcciones
• Agrega productos adicionales si faltan algunos

🚀 **¡Continuemos con la cotización!**"""

        return mensaje

    def create_products_text_for_chatbot(self, productos: List[Dict]) -> str:
        """
        Crear texto de productos para que el chatbot lo procese.
        """
        if not productos:
            return ""

        productos_texto = []
        for producto in productos:
            # Construir descripción completa
            descripcion = producto['producto_limpio']
            if producto['dosificacion']:
                descripcion += f" {producto['dosificacion']}"
            if producto['presentacion']:
                descripcion += f" {producto['presentacion']}"

            # Agregar cantidad si es diferente de 1
            if producto['cantidad'] > 1:
                descripcion += f" cantidad {producto['cantidad']}"

            # Agregar laboratorio si está especificado
            if producto['laboratorio']:
                descripcion += f" laboratorio {producto['laboratorio']}"

            productos_texto.append(descripcion)

        return ", ".join(productos_texto)

    def export_to_excel_template(self, productos: List[Dict]) -> bytes:
        """
        Exportar productos a un template de Excel para revisión.
        """
        try:
            # Crear DataFrame
            df_productos = pd.DataFrame([
                {
                    'Producto': p['producto_limpio'],
                    'Dosificación': p['dosificacion'],
                    'Presentación': p['presentacion'],
                    'Cantidad': p['cantidad'],
                    'Laboratorio': p['laboratorio'],
                    'Producto Original': p['producto_original'],
                    'Confianza %': f"{p['confianza']*100:.0f}%"
                }
                for p in productos
            ])

            # Crear archivo Excel en memoria
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_productos.to_excel(
                    writer, sheet_name='Productos Extraídos', index=False)

                # Obtener workbook y worksheet
                workbook = writer.book
                worksheet = writer.sheets['Productos Extraídos']

                # Ajustar anchos de columna
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

            output.seek(0)
            return output.read()

        except Exception as e:
            print(f"Error exportando template: {e}")
            return None

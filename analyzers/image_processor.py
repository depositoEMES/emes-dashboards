import cv2
import numpy as np
import base64
import io
from PIL import Image
import re
from typing import List, Dict, Tuple


class ImageProcessor:
    """
    Procesador de imágenes con OCR para extraer productos de recetas y listas.
    """

    def __init__(self):
        self.medicament_patterns = [
            r'\b\w*cilina?\b',  # Penicilinas, amoxicilina, etc.
            r'\b\w*fén\b',      # Acetaminofén, ibuprofén, etc.
            r'\b\w*zol\b',      # Omeprazol, etc.
            r'\b\w*ina\b',      # Aspirina, cafeína, etc.
            r'\b\w*ol\b',       # Paracetamol, etc.
            r'\b\w*aco\b',      # Diclofenaco, etc.
        ]

        # Palabras clave de medicamentos comunes
        self.common_medicines = [
            'acetaminofen', 'acetaminofén', 'paracetamol',
            'ibuprofeno', 'ibuprofen', 'advil', 'motrin',
            'aspirina', 'asa', 'dolex', 'winadol',
            'amoxicilina', 'amoxicilin', 'amoxil',
            'diclofenaco', 'diclofenac', 'voltaren',
            'omeprazol', 'losec', 'prilosec',
            'loratadina', 'claritin', 'alavert',
            'cetirizina', 'zyrtec', 'reactine',
            'dexametasona', 'betametasona',
            'prednisolona', 'prednisona',
            'captopril', 'enalapril', 'losartan',
            'metformina', 'glibenclamida',
            'simvastatina', 'atorvastatina'
        ]

        # Unidades y presentaciones
        self.units_patterns = [
            r'\d+\s*mg', r'\d+\s*gr?', r'\d+\s*ml',
            r'\d+\s*mcg', r'\d+\s*ug', r'\d+\s*ui',
            r'\d+\s*%', r'\d+\s*x\s*\d+'
        ]

        self.presentations = [
            'tabletas', 'tablet', 'tab', 'caps', 'capsulas', 'capsula',
            'jarabe', 'suspension', 'gotas', 'ampolla', 'inyectable',
            'crema', 'pomada', 'gel', 'unguento', 'solucion',
            'spray', 'inhalador', 'parche', 'supositorio'
        ]

    def process_image_base64(self, base64_string: str, filename: str = '') -> Dict:
        """
        Procesar imagen desde string base64.
        """
        try:
            # Decodificar imagen
            image_data = base64.b64decode(base64_string)
            image = Image.open(io.BytesIO(image_data))

            # Convertir a array numpy
            img_array = np.array(image)

            # Procesar imagen
            resultado = self.extract_products_from_image(img_array, filename)

            return {
                'success': True,
                'productos': resultado['productos'],
                'texto_extraido': resultado['texto_raw'],
                'confianza': resultado['confianza'],
                'mensaje': self._generar_mensaje_resultado(resultado, filename)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'mensaje': f"❌ Error procesando imagen {filename}: {str(e)}"
            }

    def extract_products_from_image(self, image: np.ndarray, filename: str = '') -> Dict:
        """
        Extraer productos de una imagen usando OCR y procesamiento inteligente.
        """
        try:
            # Preprocesar imagen para mejorar OCR
            processed_image = self._preprocess_image(image)

            # Simular OCR (en una implementación real usarías pytesseract)
            # texto_extraido = pytesseract.image_to_string(processed_image, lang='spa')

            # Para la demostración, simularemos diferentes tipos de texto extraído
            texto_simulado = self._simular_texto_extraido(filename)

            # Extraer productos del texto
            productos = self._extract_products_from_text(texto_simulado)

            # Calcular confianza
            confianza = self._calculate_confidence(productos, texto_simulado)

            return {
                'productos': productos,
                'texto_raw': texto_simulado,
                'confianza': confianza,
                'imagen_procesada': processed_image.shape
            }

        except Exception as e:
            return {
                'productos': [],
                'texto_raw': '',
                'confianza': 0,
                'error': str(e)
            }

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocesar imagen para mejorar la calidad del OCR.
        """
        try:
            # Convertir a escala de grises si es necesario
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image.copy()

            # Aplicar filtros para mejorar la legibilidad
            # Reducir ruido
            denoised = cv2.medianBlur(gray, 3)

            # Mejorar contraste
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)

            # Binarización adaptativa
            binary = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )

            return binary

        except Exception as e:
            print(f"Error en preprocesamiento: {e}")
            return image

    def _simular_texto_extraido(self, filename: str) -> str:
        """
        Simular diferentes tipos de texto extraído según el tipo de imagen.
        En una implementación real, esto sería reemplazado por pytesseract.
        """
        # Simular diferentes tipos de contenido según el nombre del archivo
        if 'receta' in filename.lower():
            return """
            RECETA MÉDICA
            Dr. Juan Pérez
            
            Acetaminofén 500mg - 20 tabletas
            Tomar 1 cada 8 horas
            
            Ibuprofeno 400mg - 15 cápsulas  
            Tomar 1 cada 12 horas
            
            Omeprazol 20mg - 14 cápsulas
            Tomar 1 en ayunas
            
            Firma: _______________
            """
        elif 'lista' in filename.lower():
            return """
            LISTA DE PRODUCTOS NECESARIOS
            
            - Acetaminofén 500mg x 50
            - Dolex tabletas x 20
            - Amoxicilina 500mg x 21 cápsulas
            - Diclofenaco gel x 2 tubos
            - Loratadina 10mg x 30 tabletas
            - Dexametasona 4mg x 10 ampollas
            """
        else:
            return """
            Medicamentos requeridos:
            
            Acetaminofén 500mg - cantidad 25
            Ibuprofeno 400mg - cantidad 30
            Aspirina 100mg - cantidad 50
            Amoxicilina cápsulas - cantidad 21
            Omeprazol 20mg - cantidad 14
            """

    def _extract_products_from_text(self, texto: str) -> List[Dict]:
        """
        Extraer productos del texto usando patrones y análisis inteligente.
        """
        productos = []
        lineas = texto.split('\n')

        for linea in lineas:
            linea = linea.strip().lower()
            if not linea or len(linea) < 3:
                continue

            # Buscar patrones de medicamentos
            producto = self._parse_medicine_line(linea)
            if producto:
                productos.append(producto)

        # Eliminar duplicados y limpiar
        productos_unicos = self._remove_duplicates(productos)

        return productos_unicos

    def _parse_medicine_line(self, linea: str) -> Dict:
        """
        Analizar una línea para extraer información del medicamento.
        """
        # Limpiar línea
        linea = re.sub(r'[^\w\s\-\.\,\(\)\/]', ' ', linea)
        linea = re.sub(r'\s+', ' ', linea).strip()

        if len(linea) < 3:
            return None

        # Buscar medicamentos conocidos
        medicamento_encontrado = None
        for med in self.common_medicines:
            if med.lower() in linea:
                medicamento_encontrado = med
                break

        # Si no se encuentra un medicamento conocido, buscar patrones
        if not medicamento_encontrado:
            for pattern in self.medicament_patterns:
                match = re.search(pattern, linea, re.IGNORECASE)
                if match:
                    medicamento_encontrado = match.group()
                    break

        if not medicamento_encontrado:
            # Verificar si la línea parece contener un medicamento
            palabras = linea.split()
            if len(palabras) > 0 and len(palabras[0]) > 3:
                # Usar la primera palabra como posible medicamento
                medicamento_encontrado = palabras[0]
            else:
                return None

        # Extraer dosificación
        dosificacion = self._extract_dosage(linea)

        # Extraer cantidad
        cantidad = self._extract_quantity(linea)

        # Extraer presentación
        presentacion = self._extract_presentation(linea)

        # Construir descripción
        descripcion_parts = [medicamento_encontrado.upper()]
        if dosificacion:
            descripcion_parts.append(dosificacion)
        if presentacion:
            descripcion_parts.append(presentacion)

        return {
            'medicamento': medicamento_encontrado.upper(),
            'dosificacion': dosificacion,
            'cantidad': cantidad,
            'presentacion': presentacion,
            'descripcion_completa': ' '.join(descripcion_parts),
            'linea_original': linea,
            'confianza': self._calculate_line_confidence(linea, medicamento_encontrado)
        }

    def _extract_dosage(self, texto: str) -> str:
        """Extraer dosificación del texto."""
        for pattern in self.units_patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                return match.group().upper()
        return ""

    def _extract_quantity(self, texto: str) -> int:
        """Extraer cantidad del texto."""
        # Buscar patrones de cantidad
        patterns = [
            r'x\s*(\d+)',
            r'cantidad\s*:?\s*(\d+)',
            r'cant\s*:?\s*(\d+)',
            r'(\d+)\s*unidades',
            r'(\d+)\s*tabs?',
            r'(\d+)\s*caps?',
            r'-\s*(\d+)',
            r'(\d+)$'  # Número al final de la línea
        ]

        for pattern in patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue

        return 1  # Cantidad por defecto

    def _extract_presentation(self, texto: str) -> str:
        """Extraer presentación del texto."""
        for pres in self.presentations:
            if pres in texto.lower():
                return pres.upper()
        return "TABLETAS"  # Presentación por defecto

    def _calculate_line_confidence(self, linea: str, medicamento: str) -> float:
        """Calcular confianza de extracción para una línea."""
        confianza = 0.0

        # Confianza base por encontrar medicamento
        if medicamento.lower() in self.common_medicines:
            confianza += 0.6
        else:
            confianza += 0.3

        # Bonificación por encontrar dosificación
        if any(re.search(pattern, linea, re.IGNORECASE) for pattern in self.units_patterns):
            confianza += 0.2

        # Bonificación por encontrar presentación
        if any(pres in linea.lower() for pres in self.presentations):
            confianza += 0.1

        # Bonificación por encontrar cantidad
        if re.search(r'\d+', linea):
            confianza += 0.1

        return min(confianza, 1.0)

    def _remove_duplicates(self, productos: List[Dict]) -> List[Dict]:
        """Eliminar productos duplicados."""
        productos_unicos = []
        vistos = set()

        for producto in productos:
            key = f"{producto['medicamento']}_{producto['dosificacion']}_{producto['presentacion']}"
            if key not in vistos:
                vistos.add(key)
                productos_unicos.append(producto)

        return productos_unicos

    def _calculate_confidence(self, productos: List[Dict], texto: str) -> float:
        """Calcular confianza general del procesamiento."""
        if not productos:
            return 0.0

        # Confianza promedio de productos individuales
        confianza_promedio = sum(p['confianza']
                                 for p in productos) / len(productos)

        # Ajustar según la calidad del texto
        lineas_utiles = len([l for l in texto.split(
            '\n') if l.strip() and len(l.strip()) > 3])
        if lineas_utiles > 0:
            factor_texto = min(len(productos) / lineas_utiles, 1.0)
        else:
            factor_texto = 0.5

        return confianza_promedio * factor_texto

    def _generar_mensaje_resultado(self, resultado: Dict, filename: str) -> str:
        """Generar mensaje amigable con los resultados."""
        productos = resultado['productos']
        confianza = resultado['confianza']

        if not productos:
            return f"""📸 **Imagen procesada: {filename}**

❌ **No pude identificar productos claramente**

🔍 **Texto detectado:**
```
{resultado['texto_extraido'][:200]}...
```

💡 **Sugerencias:**
• Asegúrate de que la imagen tenga buena iluminación
• Verifica que el texto sea legible
• Intenta con una imagen más clara

🤖 **¿Puedes escribir manualmente los productos que ves?**"""

        mensaje = f"""📸 **¡Imagen procesada exitosamente!** {filename}

✅ **Productos identificados** (Confianza: {confianza*100:.0f}%):

"""

        for i, producto in enumerate(productos, 1):
            confianza_producto = producto['confianza'] * 100
            emoji_confianza = "🟢" if confianza_producto > 70 else "🟡" if confianza_producto > 40 else "🔴"

            mensaje += f"""**{i}.** {emoji_confianza} {producto['descripcion_completa']}
   📦 Cantidad detectada: {producto['cantidad']}
   🎯 Confianza: {confianza_producto:.0f}%

"""

        mensaje += f"""🤖 **¿Los productos identificados son correctos?**

💬 **Puedes:**
• Escribir "sí" para continuar con estos productos
• Escribir "no" para corregir manualmente
• Escribir productos adicionales si faltan algunos

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
            texto_producto = producto['descripcion_completa']
            if producto['cantidad'] > 1:
                texto_producto += f" cantidad {producto['cantidad']}"
            productos_texto.append(texto_producto)

        return ", ".join(productos_texto)

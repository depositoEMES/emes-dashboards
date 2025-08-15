from .cartera import *
from .ventas_unified import *
from .ventas import *
from .transferencias import *
from .proveedores import *
from .cotizaciones import *
from .image_processor import *
from .excel_processor import *
from .facturas_proveedores import *

# Para mantener compatibilidad con imports existentes
__all__ = [
    'UnifiedVentasAnalyzer',
    'VentasAnalyzer', 
    'TransferenciasAnalyzer'
]

# Crear instancia global del analyzer unificado para uso compartido
_unified_instance = None

def get_unified_analyzer():
    """
    Obtener instancia singleton del analyzer unificado.
    Esto garantiza que ambos dashboards usen la misma instancia y datos.
    """
    global _unified_instance
    if _unified_instance is None:
        _unified_instance = UnifiedVentasAnalyzer()
        print("✅ Instancia unificada de analyzer creada")
    return _unified_instance

def reload_unified_data():
    """
    Forzar recarga de datos en la instancia unificada.
    Útil para actualizaciones manuales.
    """
    global _unified_instance
    if _unified_instance is not None:
        result = _unified_instance.reload_data()
        print("🔄 Datos unificados recargados")
        return result
    else:
        print("⚠️ No hay instancia unificada para recargar")
        return None

def clear_unified_cache():
    """
    Limpiar cache de la instancia unificada.
    """
    global _unified_instance
    if _unified_instance is not None:
        _unified_instance.clear_all_cache()
        print("🧹 Cache unificado limpiado")
    else:
        print("⚠️ No hay instancia unificada para limpiar")

def get_unified_status():
    """
    Obtener estado de la instancia unificada.
    """
    global _unified_instance
    if _unified_instance is not None:
        return _unified_instance.get_cache_status()
    else:
        return {"status": "No hay instancia unificada creada"}
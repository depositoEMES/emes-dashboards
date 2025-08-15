from datetime import datetime

def get_ultimos_3_meses():
    """
    Obtener los últimos 3 meses (simple y efectivo)
    """
    mes_actual = datetime.now().month
    
    # Siempre mostrar 3 meses hacia atrás desde el actual
    if mes_actual >= 3:
        return [mes_actual - 2, mes_actual]
    else:
        # Si estamos en enero/febrero, mostrar desde el mes actual
        return [mes_actual, mes_actual + 2 if mes_actual <= 10 else 12]
import holidays
import calendar
import pandas as pd
from datetime import datetime, date, timedelta


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


def get_ultimo_mes_finalizado():
    """
    Obtener el último mes completamente finalizado.

    Returns:
        tuple: (fecha_inicio_mes, fecha_fin_mes)
    """
    hoy = datetime.now()

    # Si estamos en los primeros días del mes, considerar mes anterior
    if hoy.day <= 3:
        # Usar mes anterior al anterior (más conservador)
        ultimo_mes = (hoy.replace(day=1) - timedelta(days=1)).replace(day=1)
        mes_anterior = (ultimo_mes - timedelta(days=1)).replace(day=1)
        fecha_inicio = mes_anterior
    else:
        # Usar mes anterior
        fecha_inicio = (hoy.replace(day=1) - timedelta(days=1)).replace(day=1)

    # Calcular último día del mes
    if fecha_inicio.month == 12:
        fecha_fin = fecha_inicio.replace(
            year=fecha_inicio.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        fecha_fin = fecha_inicio.replace(
            month=fecha_inicio.month + 1, day=1) - timedelta(days=1)

    return fecha_inicio, fecha_fin


def is_complete_month(fecha_analisis=None):
    """
    Verify if a month is completely finished.

    Args:
        Date_analysis: Date to verify (default: current month).

    Returns:
        Bool: True if the month is completely finished.
    """
    from datetime import datetime

    if fecha_analisis is None:
        fecha_analisis = datetime.now()

    hoy = datetime.now()

    # Si la fecha de análisis es de un mes anterior al actual, está completo
    if fecha_analisis.year < hoy.year or (fecha_analisis.year == hoy.year and fecha_analisis.month < hoy.month):
        return True

    # Si es del mes actual, no está completo
    return False


def calcular_dias_habiles_colombia_automatico(año, mes):
    """
    Calcular días hábiles en Colombia usando la librería holidays.
    Incluye Lunes-Sábado, excluye Domingos y festivos colombianos.
    """
    try:
        # Crear objeto de festivos para Colombia
        colombia_holidays = holidays.Colombia(years=año)

        # Obtener días del mes
        dias_mes = calendar.monthrange(año, mes)[1]
        dias_habiles = 0
        dias_habiles_transcurridos = 0

        hoy = datetime.now()

        for dia in range(1, dias_mes + 1):
            fecha = date(año, mes, dia)
            dia_semana = fecha.weekday()  # 0=Lunes, 6=Domingo

            # Contar Lunes-Sábado (0-5), excluir Domingo (6) y festivos
            if dia_semana != 6 and fecha not in colombia_holidays:
                dias_habiles += 1

                # Si es el mes actual, contar días hábiles transcurridos
                if año == hoy.year and mes == hoy.month and dia <= hoy.day:
                    dias_habiles_transcurridos += 1
                elif año < hoy.year or (año == hoy.year and mes < hoy.month):
                    dias_habiles_transcurridos = dias_habiles  # Mes completo

        return dias_habiles, dias_habiles_transcurridos

    except Exception as e:
        print(f"Error calculando días hábiles con holidays: {e}")
        # Fallback: cálculo simple sin festivos
        return calcular_dias_habiles_simple(año, mes)


def calcular_dias_habiles_simple(año, mes):
    """
    Fallback: cálculo simple sin festivos (solo excluye domingos).
    """
    dias_mes = calendar.monthrange(año, mes)[1]
    dias_habiles = 0
    dias_habiles_transcurridos = 0

    hoy = datetime.now()

    for dia in range(1, dias_mes + 1):
        fecha = date(año, mes, dia)
        dia_semana = fecha.weekday()

        # Solo excluir domingos
        if dia_semana != 6:
            dias_habiles += 1

            if año == hoy.year and mes == hoy.month and dia <= hoy.day:
                dias_habiles_transcurridos += 1
            elif año < hoy.year or (año == hoy.year and mes < hoy.month):
                dias_habiles_transcurridos = dias_habiles

    return dias_habiles, dias_habiles_transcurridos


def calcular_dias_habiles_pandas(año, mes):
    """
    Alternativa usando pandas.bdate_range para días hábiles.
    Nota: pandas considera Lunes-Viernes como días hábiles por defecto.
    """
    try:
        import pandas as pd

        # Crear rango de fechas del mes
        inicio_mes = pd.Timestamp(año, mes, 1)
        if mes == 12:
            fin_mes = pd.Timestamp(año + 1, 1, 1) - pd.Timedelta(days=1)
        else:
            fin_mes = pd.Timestamp(año, mes + 1, 1) - pd.Timedelta(days=1)

        # Generar días hábiles (Lunes-Viernes por defecto)
        dias_habiles_pandas = pd.bdate_range(inicio_mes, fin_mes)

        # Si necesitas incluir sábados, usar un enfoque diferente
        todas_fechas = pd.date_range(inicio_mes, fin_mes)
        # 0-5 (Lunes-Sábado)
        dias_habiles_con_sabados = todas_fechas[todas_fechas.dayofweek < 6]

        # Calcular días hábiles transcurridos
        hoy = datetime.now()

        if año == hoy.year and mes == hoy.month:
            fecha_corte = pd.Timestamp(hoy.date())
            dias_transcurridos = len(
                [d for d in dias_habiles_con_sabados if d <= fecha_corte])
        else:
            dias_transcurridos = len(dias_habiles_con_sabados)

        return len(dias_habiles_con_sabados), dias_transcurridos

    except ImportError:
        print("pandas no disponible, usando método simple")
        return calcular_dias_habiles_simple(año, mes)
    except Exception as e:
        print(f"Error con pandas: {e}")
        return calcular_dias_habiles_simple(año, mes)


def calcular_dias_habiles_colombia(año, mes):
    """
    Función principal que intenta usar holidays, luego pandas, luego fallback simple.
    """
    # Intentar con holidays (más preciso)
    try:
        return \
            calcular_dias_habiles_colombia_automatico(año, mes)
    except ImportError:
        try:
            return \
                calcular_dias_habiles_pandas(año, mes)
        except:
            return \
                calcular_dias_habiles_simple(año, mes)
    except Exception as e:
        print(f"Error con holidays: {e}, usando método alternativo")
        return calcular_dias_habiles_pandas(año, mes)


def safe_pct(num: float, den: float) -> float:
    """
    Safe division to calculate percentage.

    Returns:
        float: Percentage.
    """
    return \
        float(num) / float(den) * 100 if den else 0.0


def normalize_0_100(series: pd.Series) -> pd.Series:
    """
    Normalise between 0 and 100.

    Args:
        series (pd.Series): Data as series.

    Returns:
        pd.Series: Serie to normalise.
    """
    if series.empty or series.nunique() == 1:
        return pd.Series([50]*len(series), index=series.index, dtype=float)

    q1, q3 = series.quantile(0.25), series.quantile(0.75)

    iqr = max(q3 - q1, 1e-6)

    clipped = series.clip(lower=q1-1.5*iqr, upper=q3+1.5*iqr)

    return \
        (clipped - clipped.min())/(clipped.max()-clipped.min()) * 100

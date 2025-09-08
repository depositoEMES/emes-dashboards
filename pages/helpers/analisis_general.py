class VentasAnalysisHelper:

    @staticmethod
    def generar_analisis_rapido(resumen, variacion_ajustada=None):
        """
        Genera puntos de análisis en español simple para vendedores
        """
        analisis_items = []

        # Análisis de efectividad
        efectividad = ((resumen['total_ventas'] - resumen['total_devoluciones']) /
                       resumen['total_ventas'] * 100) if resumen['total_ventas'] > 0 else 0
        tasa_devolucion = (resumen['total_devoluciones'] / resumen['total_ventas']
                           * 100) if resumen['total_ventas'] > 0 else 0

        if tasa_devolucion > 10:
            analisis_items.append({
                'icon': '⚠️',
                'color': '#ef4444',
                'texto': f'Devoluciones altas ({tasa_devolucion:.1f}%). Revisar con clientes qué está pasando.'
            })
        elif tasa_devolucion < 2:
            analisis_items.append({
                'icon': '✅',
                'color': '#22c55e',
                'texto': f'Excelente calidad. Solo {tasa_devolucion:.1f}% de devoluciones.'
            })

        # Análisis de ticket promedio
        ticket = resumen['ticket_promedio']
        if ticket < 500000:
            analisis_items.append({
                'icon': '💡',
                'color': '#f59e0b',
                'texto': 'Ticket promedio bajo. Ofrece productos adicionales en cada venta.'
            })
        elif ticket > 2000000:
            analisis_items.append({
                'icon': '💎',
                'color': '#3b82f6',
                'texto': 'Excelente ticket promedio. Estás vendiendo bien.'
            })

        # Análisis de frecuencia
        if resumen['num_clientes'] > 0:
            facturas_por_cliente = resumen['num_facturas'] / \
                resumen['num_clientes']
            if facturas_por_cliente > 2:
                analisis_items.append({
                    'icon': '🔄',
                    'color': '#10b981',
                    'texto': f'Clientes fieles: {facturas_por_cliente:.1f} compras por cliente.'
                })
            elif facturas_por_cliente < 1.5:
                analisis_items.append({
                    'icon': '📞',
                    'color': '#f59e0b',
                    'texto': 'Pocos pedidos por cliente. Haz seguimiento más frecuente.'
                })

        # Análisis de tendencia
        if variacion_ajustada is not None:
            if variacion_ajustada > 10:
                analisis_items.append({
                    'icon': '🚀',
                    'color': '#22c55e',
                    'texto': f'Vas muy bien! Crecimiento del {variacion_ajustada:.1f}% ajustado.'
                })
            elif variacion_ajustada < -10:
                analisis_items.append({
                    'icon': '📉',
                    'color': '#ef4444',
                    'texto': f'Ventas bajando {abs(variacion_ajustada):.1f}%. Activa a tus clientes.'
                })

        # Análisis de descuentos
        if resumen['porcentaje_descuento'] > 15:
            analisis_items.append({
                'icon': '🏷️',
                'color': '#ef4444',
                'texto': f'Descuentos muy altos ({resumen["porcentaje_descuento"]:.1f}%). Cuidado con márgenes.'
            })

        return analisis_items

    @staticmethod
    def calcular_variacion_ajustada(ventas_actual, ventas_anterior, dias_transcurridos, dias_mes):
        """
        Calcula variación ajustada por días transcurridos del mes
        """
        if ventas_anterior == 0:
            return 0

        # Proyectar ventas del mes actual
        if dias_transcurridos > 0 and dias_mes > 0:
            porcentaje_mes = dias_transcurridos / dias_mes
            ventas_proyectadas = ventas_actual / \
                porcentaje_mes if porcentaje_mes > 0 else ventas_actual
        else:
            ventas_proyectadas = ventas_actual

        # Calcular variación con proyección
        variacion = ((ventas_proyectadas - ventas_anterior) /
                     ventas_anterior * 100)
        return variacion

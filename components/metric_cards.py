# components/metric_cards.py
"""
Componente reutilizable para cards de métricas con glassmorphism effect
Basado en el diseño de facturas_proveedores.py
"""

from dash import html
from typing import List, Dict, Optional


def create_metric_card(
    title: str,
    value: str,
    icon: str = "",
    color: str = "#3b82f6",
    is_dark: bool = False,
    subtitle: str = None,
    trend_indicator: str = None,
    card_id: str = None
):
    """
    Crear una card de métrica individual con glassmorphism effect
    
    Args:
        title: Título de la métrica (ej: "Total Facturas")
        value: Valor de la métrica (ej: "1,234" o "$50,000")
        icon: Emoji o símbolo para mostrar (ej: "📄", "💰")
        color: Color del borde superior y accent (hex)
        is_dark: Si está en modo oscuro
        subtitle: Texto adicional debajo del valor
        trend_indicator: Indicador de tendencia (ej: "↗️ +5%")
        card_id: ID único para la card (opcional)
    
    Returns:
        html.Div: Card component
    """
    
    # Estilos según tema
    if is_dark:
        theme_styles = {
            'card_bg': 'linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(51, 65, 85, 0.6))',
            'text_primary': '#f8fafc',
            'text_secondary': '#e2e8f0',
            'text_muted': '#94a3b8',
            'shadow': '0 8px 32px rgba(0, 0, 0, 0.3)',
            'border': 'rgba(148, 163, 184, 0.2)',
            'backdrop_filter': 'blur(15px)'
        }
    else:
        theme_styles = {
            'card_bg': 'linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.8))',
            'text_primary': '#1e293b',
            'text_secondary': '#374151',
            'text_muted': '#6b7280',
            'shadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
            'border': 'rgba(59, 130, 246, 0.2)',
            'backdrop_filter': 'blur(15px)'
        }
    
    # Contenido de la card
    card_content = [
        # Borde superior con color accent
        html.Div(style={
            'position': 'absolute',
            'top': '0',
            'left': '0',
            'right': '0',
            'height': '4px',
            'background': color,
            'borderRadius': '16px 16px 0 0'
        }),
        
        # Valor principal
        html.H3(value, style={
            'fontSize': '28px',
            'fontWeight': '800',
            'color': theme_styles['text_primary'],
            'margin': '0 0 8px 0',
            'textShadow': '0 2px 4px rgba(0, 0, 0, 0.3)' if is_dark else 'none',
            'fontFamily': 'Inter, sans-serif'
        }),
        
        # Título
        html.P(title, style={
            'fontSize': '14px',
            'color': theme_styles['text_muted'],
            'fontWeight': '500',
            'margin': '0 0 8px 0',
            'fontFamily': 'Inter, sans-serif'
        })
    ]
    
    # Subtítulo opcional
    if subtitle:
        card_content.append(
            html.P(subtitle, style={
                'fontSize': '12px',
                'color': theme_styles['text_muted'],
                'fontWeight': '400',
                'margin': '0 0 8px 0',
                'fontFamily': 'Inter, sans-serif',
                'opacity': '0.8'
            })
        )
    
    # Indicador de tendencia opcional
    if trend_indicator:
        card_content.append(
            html.P(trend_indicator, style={
                'fontSize': '12px',
                'color': '#10b981' if '↗️' in trend_indicator or '+' in trend_indicator else '#ef4444',
                'fontWeight': '600',
                'margin': '0',
                'fontFamily': 'Inter, sans-serif'
            })
        )
    
    # Icono en la esquina
    if icon:
        card_content.append(
            html.Div(icon, style={
                'position': 'absolute',
                'top': '20px',
                'right': '20px',
                'fontSize': '24px',
                'opacity': '0.7'
            })
        )
    
    return html.Div(
        card_content,
        id=card_id,
        style={
            'background': theme_styles['card_bg'],
            'backdropFilter': theme_styles['backdrop_filter'],
            'WebkitBackdropFilter': theme_styles['backdrop_filter'],
            'border': f"1px solid {theme_styles['border']}",
            'borderRadius': '16px',
            'padding': '24px',
            'boxShadow': theme_styles['shadow'],
            'position': 'relative',
            'overflow': 'hidden',
            'transition': 'all 0.3s ease',
            'cursor': 'pointer',
            'minHeight': '120px',
            'display': 'flex',
            'flexDirection': 'column',
            'justifyContent': 'center'
        },
        className='glass-card metric-card'  # Para CSS adicional si es necesario
    )


def create_metrics_grid(
    metrics: List[Dict],
    is_dark: bool = False,
    columns: int = None,
    gap: str = "20px"
):
    """
    Crear una grilla de cards de métricas
    
    Args:
        metrics: Lista de diccionarios con datos de métricas
                 Cada dict debe tener: title, value, y opcionalmente: icon, color, subtitle, trend_indicator, card_id
        is_dark: Si está en modo oscuro
        columns: Número de columnas (auto-fit si None)
        gap: Espacio entre cards
    
    Returns:
        html.Div: Container con grilla de cards
    
    Example:
        metrics_data = [
            {
                'title': 'Total Ventas',
                'value': '$125,000',
                'icon': '💰',
                'color': '#10b981',
                'trend_indicator': '↗️ +15%'
            },
            {
                'title': 'Facturas',
                'value': '1,234',
                'icon': '📄',
                'color': '#3b82f6',
                'subtitle': 'Este mes'
            }
        ]
        
        grid = create_metrics_grid(metrics_data, is_dark=False)
    """
    
    # Crear cards individuales
    cards = []
    for i, metric in enumerate(metrics):
        card = create_metric_card(
            title=metric.get('title', f'Métrica {i+1}'),
            value=metric.get('value', '0'),
            icon=metric.get('icon', ''),
            color=metric.get('color', '#3b82f6'),
            is_dark=is_dark,
            subtitle=metric.get('subtitle'),
            trend_indicator=metric.get('trend_indicator'),
            card_id=metric.get('card_id')
        )
        cards.append(card)
    
    # Determinar grid columns
    if columns:
        grid_template = f'repeat({columns}, 1fr)'
    else:
        min_width = '250px'  # Ancho mínimo por card
        grid_template = f'repeat(auto-fit, minmax({min_width}, 1fr))'
    
    return html.Div(
        cards,
        style={
            'display': 'grid',
            'gridTemplateColumns': grid_template,
            'gap': gap,
            'marginBottom': '24px'
        },
        className='metrics-grid'
    )


def create_empty_metrics(is_dark: bool = False, count: int = 4):
    """
    Crear métricas vacías/placeholder
    
    Args:
        is_dark: Si está en modo oscuro
        count: Número de cards vacías a crear
    
    Returns:
        html.Div: Grid con cards vacías
    """
    
    placeholders = [
        {'title': 'Cargando...', 'value': '---', 'color': '#6b7280'}
        for _ in range(count)
    ]
    
    return create_metrics_grid(placeholders, is_dark=is_dark)


# Colores predefinidos para diferentes tipos de métricas
METRIC_COLORS = {
    'success': '#10b981',    # Verde - para valores positivos, éxitos
    'primary': '#3b82f6',    # Azul - para métricas principales
    'warning': '#f59e0b',    # Amarillo - para alertas, pendientes
    'danger': '#ef4444',     # Rojo - para errores, valores negativos
    'purple': '#8b5cf6',     # Púrpura - para métricas especiales
    'indigo': '#6366f1',     # Índigo - para datos secundarios
    'teal': '#14b8a6',       # Verde azulado - para balances
    'orange': '#f97316',     # Naranja - para métricas de tiempo
    'pink': '#ec4899',       # Rosa - para métricas de usuarios
    'gray': '#6b7280'        # Gris - para datos neutros
}


# Iconos comunes para diferentes tipos de métricas
METRIC_ICONS = {
    'money': '💰',
    'sales': '📈',
    'invoice': '📄',
    'client': '👥',
    'product': '📦',
    'time': '⏰',
    'percent': '📊',
    'count': '🔢',
    'trend_up': '📈',
    'trend_down': '📉',
    'warning': '⚠️',
    'success': '✅',
    'pending': '⏳',
    'building': '🏢',
    'calendar': '📅',
    'location': '📍'
}
LIGHT_THEME = {
    'bg_color': '#f8fafc',
    'paper_color': '#ffffff',
    'text_color': '#111827',
    'card_shadow': '0 8px 32px rgba(0, 0, 0, 0.1)',
    'plot_bg': '#ffffff',
    'grid_color': '#f0f2f5',
    'line_color': '#d1d5db',
    'border_color': '#e5e7eb'
}

DARK_THEME = {
    'bg_color': '#0f172a',
    'paper_color': '#1e293b',
    'text_color': '#f8fafc',
    'card_shadow': '0 8px 32px rgba(0, 0, 0, 0.3)',
    'plot_bg': '#1e293b',
    'grid_color': 'rgba(59, 130, 246, 0.1)',
    'line_color': 'rgba(59, 130, 246, 0.2)',
    'border_color': 'rgba(59, 130, 246, 0.2)'
}

def get_theme_styles(theme):
    """
    Get theme-specific styles.
    """
    return DARK_THEME if theme == 'dark' else LIGHT_THEME

def get_dropdown_style(theme):
    """
    Get dropdown styles based on theme with glassmorphism effect.
    """
    if theme == 'dark':
        return {
            'backgroundColor': 'rgba(148, 163, 184, 0.15)',  # Efecto glass tenue
            'color': '#f8fafc',
            'border': '1px solid rgba(148, 163, 184, 0.25)',
            'borderRadius': '12px',                          # Bordes redondeados
            'fontSize': '13px',                              # Letra más pequeña
            'backdropFilter': 'blur(10px)',                  # Efecto glass
            'transition': 'all 0.3s ease',
            'boxShadow': '0 2px 8px rgba(0, 0, 0, 0.1)'
        }
    else:
        return {
            'backgroundColor': 'rgba(255, 255, 255, 0.8)',   # Glass effect light
            'color': '#374151',
            'border': '1px solid rgba(203, 213, 225, 0.4)',
            'borderRadius': '12px',                          # Bordes redondeados
            'fontSize': '13px',                              # Letra más pequeña
            'backdropFilter': 'blur(8px)',                   # Efecto glass
            'transition': 'all 0.3s ease',
            'boxShadow': '0 2px 8px rgba(0, 0, 0, 0.05)'
        } 
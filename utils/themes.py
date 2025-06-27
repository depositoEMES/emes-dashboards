LIGHT_THEME = \
    {
        'bg_color': '#f5f5f5',
        'paper_color': 'white',
        'text_color': '#2c3e50',
        'card_shadow': '0 2px 4px rgba(0,0,0,0.1)',
        'plot_bg': 'rgba(0,0,0,0)',
        'grid_color': '#F0F0F0',
        'line_color': '#E5E5E5'
    }

DARK_THEME = \
    {
        'bg_color': '#1e1e1e',
        'paper_color': '#2d2d2d',
        'text_color': '#ffffff',
        'card_shadow': '0 2px 4px rgba(255,255,255,0.1)',
        'plot_bg': 'rgba(0,0,0,0)',
        'grid_color': '#404040',
        'line_color': '#505050'
    }


def get_theme_styles(theme):
    """
    Get theme-specific styles.
    """
    return \
        DARK_THEME if theme == 'dark' else LIGHT_THEME

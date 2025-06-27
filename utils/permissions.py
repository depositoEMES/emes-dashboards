def get_user_vendor_filter(session_data):
    """
    Determina el filtro de vendedor basado en la sesión del usuario.

    Returns:
        str: 'Todos' si el usuario puede ver todo, o el nombre del vendedor específico
    """
    if not session_data:
        return 'Todos'  # Fallback

    seller = session_data.get('seller', '')

    # Admin account
    return \
        'Todos' if seller in ['JESUS IVAN GOMEZ VELASQUEZ',
                              'YAMITH SCHNEIDER MESA ESCOBAR'] else seller


def can_see_all_vendors(session_data):
    """
    Verifica si el usuario puede ver todos los vendedores.
    """
    if not session_data:
        return False

    seller = \
        session_data.get('seller', '')

    return \
        seller in ['JESUS IVAN GOMEZ VELASQUEZ',
                   'YAMITH SCHNEIDER MESA ESCOBAR']

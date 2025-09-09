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
        'Todos' if seller in \
        [
            'JESUS IVAN GOMEZ VELASQUEZ',
            'YAMITH SCHNEIDER MESA ESCOBAR',
            'DINA NARANJO'
        ] else seller


def can_see_all_vendors(session_data):
    """
    Verifica si el usuario puede ver todos los vendedores.
    """
    if not session_data:
        return False

    seller = \
        session_data.get('seller', '')

    return \
        seller in \
        [
            'JESUS IVAN GOMEZ VELASQUEZ',
            'YAMITH SCHNEIDER MESA ESCOBAR',
            'DINA NARANJO'
        ]


def get_selected_vendor(session_data, dropdown_value):
    """
    Get seller based on permissions.
    """
    try:
        if not session_data:
            return 'Todos'

        if can_see_all_vendors(session_data):
            # For admin users, use dropdown selection
            return dropdown_value if dropdown_value else 'Todos'
        else:
            # For regular users, return their specific seller
            return get_user_vendor_filter(session_data)

    except Exception as e:
        print(f"Error en get_selected_vendor: {e}")
        return 'Todos'

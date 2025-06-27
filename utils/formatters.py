import pandas as pd


def format_currency(value):
    """
    Format numbers as Colombian currency.

    Args:
        value (float): The numeric value to format

    Returns:
        str: Formatted currency string (e.g., $1.234.567,89)
    """
    if pd.isna(value) or value == 0:
        return "$0"

    # Format: $1.234.567,89 (. for thousands, , for decimals)
    formatted = \
        f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    return f"${formatted}"


def format_currency_int(value):
    """
    Format integer numbers as currency.

    Args:
        value (float): The numeric value to format

    Returns:
        str: Formatted currency string without decimals (e.g., $1.234.567)
    """
    if pd.isna(value) or value == 0:
        return "$0"

    # Format: $1.234.567 (. for thousands)
    formatted = f"{value:,.0f}".replace(",", ".")

    return f"${formatted}"

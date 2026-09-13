"""Formatting helpers shared by the dashboard."""


def money(value) -> str:
    """Format a number as US dollars, e.g. 1234.5 -> '$1,234.50'."""
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def count(value) -> str:
    """Format an integer with thousands separators, e.g. 42000 -> '42,000'."""
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "0"

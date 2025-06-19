from typing import Union

Number = Union[int, float]

def format_currency(value: Number) -> str:
    """Format a number as USD currency following the UI spec.

    Rules:
    • Prefix with $ sign.
    • Thousands separator.
    • If absolute value >= 1,000 show no decimals.
    • Otherwise show two decimals.
    """
    try:
        abs_val = abs(float(value))
    except (ValueError, TypeError):
        return "$0"

    has_decimals = abs_val < 1000
    return "$" + f"{abs_val:,.2f}" if has_decimals else "$" + f"{abs_val:,.0f}"


def format_delta(value: Number, is_percent: bool = False) -> str:
    """Return a color-aware delta string (HTML ready).

    Positive numbers are prefixed with + and wrapped in <span class='delta-positive'>.
    Negative numbers are prefixed with – (en-dash) and wrapped in <span class='delta-negative'>.
    Zero returns an unstyled '0'.
    When is_percent is True a single decimal percentage is appended.
    """
    try:
        numeric = float(value)
    except (ValueError, TypeError):
        numeric = 0.0

    if numeric == 0:
        formatted = "0.0%" if is_percent else "$0"
        return formatted

    cls = "delta-positive" if numeric > 0 else "delta-negative"
    sign = "+" if numeric > 0 else "–"  # en dash per spec
    abs_val = abs(numeric)
    if is_percent:
        body = f"{abs_val:.1f}%"
    else:
        body = format_currency(abs_val)

    return f"<span class='{cls}'>{sign}{body}</span>" 
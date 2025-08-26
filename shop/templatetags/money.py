from django import template

register = template.Library()


@register.filter
def money_minor(value: int) -> str:
    try:
        return f"{int(value) / 100:.2f}"
    except Exception:
        return str(value)

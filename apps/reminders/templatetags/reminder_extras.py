from django import template

register = template.Library()


@register.filter(name="abs")
def absval(value):
    """Return the absolute value of a number. Usage: {{ value|abs }}"""
    try:
        return abs(value)
    except (TypeError, ValueError):
        return value

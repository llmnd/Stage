from django import template

register = template.Library()

@register.filter
def split(value, separator=","):
    """Découpe une chaîne `value` en liste selon `separator`."""
    if not value:
        return []
    return [item.strip() for item in value.split(separator)]

@register.filter
def trim(value):
    """Enlève les espaces au début et à la fin d'une chaîne."""
    if not isinstance(value, str):
        return value
    return value.strip()

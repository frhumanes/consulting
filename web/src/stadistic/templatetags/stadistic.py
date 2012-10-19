from django import template

register = template.Library()

@register.simple_tag
def dictvalue(d, key):
    if key in d:
        if isinstance(d[key], float):
            return "%.2f" % d[key]
        else:
            return d[key]
    return "&mdash;"

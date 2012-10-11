from django import template

register = template.Library()

@register.simple_tag
def dictvalue(d, key):
    if key in d and d[key] >= 0:
        return "%.2f" % d[key]
    else:
        return ''

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

@register.filter
def get_available_options(user):
    blocks = user.get_profile().get_scored_blocks(statistic=True)
    return blocks

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    else:
        return ''

@register.filter
def sorteditems(dictionary):
    keys = dictionary.keys()
    keys.sort(reverse=True)
    return [(k, dictionary[k]) for k in keys]  
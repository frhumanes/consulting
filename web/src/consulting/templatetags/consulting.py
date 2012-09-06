from django import template

register = template.Library()


@register.simple_tag
def active_root(request, pattern):
    split_path = request.path.split('/')
    split_pattern = pattern.split('/')

    if split_path[1] == split_pattern[1] and  split_path[1] != '':
        return 'active'

    return ''


@register.simple_tag
def active_child(request, pattern):
    split_path = request.path.split('/')
    split_pattern = pattern.split('/')

    if split_path[1] == split_pattern[1] and split_path[2] == split_pattern[2]:
        return 'active'

    return ''


@register.simple_tag
def active_granchild(request, pattern):
    split_path = request.path.split('/')
    split_pattern = pattern.split('/')

    if split_path[1] == split_pattern[1] and\
        split_path[2] == split_pattern[2] and\
        split_path[3] == split_pattern[3]:
        return 'active'

    return ''


@register.simple_tag
def active_greatgranchild(request, pattern):
    split_path = request.path.split('/')
    split_pattern = pattern.split('/')

    if split_path[1] == split_pattern[1] and\
        split_path[2] == split_pattern[2] and\
        split_path[3] == split_pattern[3] and\
        split_path[4] == split_pattern[4]:
        return 'active'

    return ''

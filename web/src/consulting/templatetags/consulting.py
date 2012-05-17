from django import template

register = template.Library()


@register.simple_tag
def active(request, pattern):
    # import re
    # if re.search(pattern, request.path):
    #     return 'active'
    # # return ''

    # print '******REQUEST.PATH******'
    # print request.path
    # print '******PATTERN******'
    # print pattern
    # print '-------------------------------------------'
    if pattern == request.path:
        return 'active'

    return ''

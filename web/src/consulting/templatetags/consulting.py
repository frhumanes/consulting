from django import template
from django.conf import settings
from django.contrib.sites.models import Site
BRAND = Site.objects.get_current().name
DOMAIN = Site.objects.get_current().domain

register = template.Library()


@register.simple_tag
def active_root(request, pattern):
    split_path = request.path.split('/')
    split_pattern = pattern.split('/')

    if split_path[1] == split_pattern[1] and  split_path[1] != '':
        return 'active'

    return ''

@register.simple_tag
def active_leaf(request, pattern):
    split_path = request.path.split('/')
    split_pattern = pattern.split('/')

    if split_path[-2] == split_pattern[-2] and  split_path[-2] != '':
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


@register.simple_tag
def get_anxiety_status_at(patient, date, i=0):
    try:
        return patient.get_profile().get_anxiety_status(at_date=date)[i]
    except:
        return ' '

@register.simple_tag
def get_depression_status_at(patient, date, i=0):
    try:
        return patient.get_profile().get_depression_status(at_date=date)[i]
    except:
        return ' '

@register.simple_tag
def get_brand():
    return BRAND

@register.simple_tag
def get_domain():
    return DOMAIN

@register.filter
def sexify(value, patient):
    oa = {settings.MAN: 'o', settings.WOMAN: 'a'}
    ella = {settings.MAN: 'el', settings.WOMAN: 'la'}
    sex = patient.get_profile().sex
    value = value.replace('el/la', ella[sex])
    return value.replace('o/a', oa[sex])
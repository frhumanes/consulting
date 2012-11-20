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
def get_anxiety_status_at(patient, date, i=None):
    try:
        if isinstance(i, int):
            return patient.get_profile().get_anxiety_status(at_date=date)[i]
        else:
            return patient.get_profile().get_anxiety_status(at_date=date, html=True)
    except:
        return ' '

@register.simple_tag
def get_depression_status_at(patient, date, i=None):
    try:
        if isinstance(i, int):
            return patient.get_profile().get_depression_status(at_date=date)[i]
        else:
            return patient.get_profile().get_depression_status(at_date=date, html=True)
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

@register.filter
def get_pages_list(objects):
    o = objects.paginator.page_range
    n_min = max(0, objects.number - 1 - settings.MAX_VISIBLE_PAGES / 3)
    n_max = min(objects.paginator.num_pages, objects.number + settings.MAX_VISIBLE_PAGES * 2/3)

    n_min = min(n_min, objects.paginator.num_pages - settings.MAX_VISIBLE_PAGES)
    n_max = max(n_max, settings.MAX_VISIBLE_PAGES)

    return [o[:n_min], o[n_min:n_max], o[n_max:]]
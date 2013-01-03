from django import template
from django.conf import settings
from django.contrib.sites.models import Site
import Image
import StringIO
import os
import base64

BRAND = Site.objects.get_current().name
DOMAIN = Site.objects.get_current().domain

register = template.Library()


@register.simple_tag
def active_root(request, pattern):
    split_path = request.path.split('/')
    split_pattern = pattern.split('/')

    if split_path[1] == split_pattern[1] and  split_path[1] != '':
        return 'active'
    elif request.path == pattern:
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
    if sex and sex in (settings.MAN, settings.WOMAN):
        value = value.replace('el/la', ella[sex])
        return value.replace('o/a', oa[sex])
    return value

@register.filter
def get_pages_list(objects):
    o = objects.paginator.page_range
    n_min = max(0, objects.number - 2)
    n_max = min(objects.paginator.num_pages, objects.number + settings.MAX_VISIBLE_PAGES - 2)

    n_min = min(n_min, max(0, objects.paginator.num_pages - settings.MAX_VISIBLE_PAGES))
    n_max = max(n_max, min(settings.MAX_VISIBLE_PAGES, objects.paginator.num_pages))

    return [o[:n_min], o[n_min:n_max], o[n_max:]]

@register.simple_tag
def embed_image(imfile, width=None, height=None, format='PNG'):
    if os.path.exists(imfile):
        im = Image.open(imfile)
        if width and height:
            im.thumbnail((width, height), Image.ANTIALIAS)
        buf = StringIO.StringIO()
        im.save(buf, format=format)
        r = buf.getvalue()
        buf.close()
        return base64.b64encode(r)[:-1]

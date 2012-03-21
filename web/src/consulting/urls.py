# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import *
from consulting.views import *


urlpatterns = patterns('',
    url(r'^$', administrative, name='administrative_index'),
    # url(r'^$', prueba, name='administrative_index'),
    # url(r'^newpatient/', newpatient, name='newpatient'),
    url(r'^prueba/', prueba, name='prueba'),
)

# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import *
from consulting.views import *


urlpatterns = patterns('',
    url(r'^$', administrative, name='administrative_index'),
    url(r'^newpatient/', newpatient, name='newpatient'),
    url(r'^newappointment/(?P<id_newpatient>\d+)$', newappointment,
        name='newappointment'),
    url(r'^appointments_doctor/', appointments_doctor,
        name='appointments_doctor'),
    url(r'^searcher/', searcher, name='searcher'),
)

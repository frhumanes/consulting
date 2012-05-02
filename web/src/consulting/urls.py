# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import *
import views


urlpatterns = patterns('',
    url(r'^newpatient/', views.newpatient, name='newpatient'),
    url(r'^newappointment/(?P<id_newpatient>\d+)$', views.newappointment,
        name='newappointment'),
    url(r'^appointments_doctor/', views.appointments_doctor,
        name='appointments_doctor'),
    url(r'^searcher/', views.searcher, name='searcher'),
    url(r'^patient_appointments/', views.patient_appointments,
        name='patient_appointments'),
    url(r'^patient_management/', views.patient_management,
        name='patient_management'),
)

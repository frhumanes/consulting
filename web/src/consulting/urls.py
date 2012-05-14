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
    url(r'^searcher_medicine/', views.searcher_medicine,
        name='searcher_medicine'),
    url(r'^patient_appointments/', views.patient_appointments,
        name='patient_appointments'),
    url(r'^patient_management/', views.patient_management,
        name='patient_management'),
    url(r'^personal_data_pm/(?P<patient_id>\d+)$', views.personal_data_pm,
        name='personal_data_pm'),
    url(r'^details_medicine_pm/(?P<medicine_id>\d+)$',
        views.details_medicine_pm, name='details_medicine_pm'),
    url(r'^newtreatment_pm/', views.newtreatment_pm, name='newtreatment_pm'),
    url(r'^remove_medication/', views.remove_medication,
        name='remove_medication'),
)

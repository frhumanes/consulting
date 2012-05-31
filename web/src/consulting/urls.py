# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from consulting import views as consulting_views

urlpatterns = patterns('',
    url(r'^$', consulting_views.index, name='consulting_index'),

    url(r'^newpatient/', consulting_views.newpatient,
        name='consulting_newpatient'),

    url(r'^newappointment/(?P<id_newpatient>\d+)$',
        consulting_views.newappointment,
        name='consulting_newappointment'),

    url(r'^appointments_doctor/', consulting_views.appointments_doctor,
        name='consulting_appointments_doctor'),

    url(r'^searcher/', consulting_views.searcher,
        name='consulting_searcher'),

    url(r'^searcher_component/', consulting_views.searcher_component,
        name='consulting_searcher_component'),

    url(r'^patient_appointments/', consulting_views.patient_appointments,
        name='consulting_patient_appointments'),

    # PATIENT_MANAGEMENT
    url(r'^patient_management/$', consulting_views.patient_management,
        name='consulting_index_pm'),

    url(r'^patient_management/personal_data_pm/(?P<patient_id>\d+)$',
        consulting_views.personal_data_pm,
        name='consulting_personal_data_pm'),

    url(r'^searcher_patients_doctor/',
        consulting_views.searcher_patients_doctor,
        name='consulting_searcher_patients_doctor'),

    url(r'^patient_management/list_treatments_pm/$',
        consulting_views.list_treatments_pm,
        name='consulting_list_treatments_pm'),

    url(r'^patient_management/detail_treatment_pm/$',
        consulting_views.detail_treatment_pm,
        name='consulting_detail_treatment_pm'),

    url(r'^patient_management/newtreatment_pm/$',
        consulting_views.newtreatment_pm,
        name='consulting_newtreatment_pm'),

    url(r'^patient_management/newtreatment_pm/add_prescriptions_treatment_pm/(?P<treatment_id>\d+)$',
        consulting_views.add_prescriptions_treatment_pm,
        name='consulting_add_prescriptions_treatment_pm'),

    url(r'^patient_management/remove_prescription_pm/$',
        consulting_views.remove_prescription_pm,
        name='consulting_remove_prescription_pm'),

    url(r'^patient_management/remove_treatment_pm/$',
        consulting_views.remove_treatment_pm,
        name='consulting_remove_treatment_pm'),
)

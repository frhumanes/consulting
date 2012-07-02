# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from consulting import views as consulting_views

urlpatterns = patterns('',
    # MAIN
    url(r'^$', consulting_views.index, name='consulting_index'),
    # SEACHER: ROLE DOCTOR AND ADMINISTRATIVE
    url(r'^searcher/', consulting_views.searcher,
        name='consulting_searcher'),

    # APPOINTMENTS PATIENT: DOCTOR AND ADMINISTRATIVE ROLES
    # Look at index_administrative.html line 35
    url(r'^patient_appointments/(?P<patient_user_id>\d+)$',
        consulting_views.patient_appointments,
        name='consulting_patient_appointments'),

    # NEW PATIENT AND NEW APPOINTMENT: DOCTOR AND ADMINISTRATIVE ROLES
    url(r'^newpatient/$', consulting_views.newpatient,
        name='consulting_newpatient'),

    url(r'^newpatient/newappointment/(?P<newpatient_id>\d+)$',
        consulting_views.newappointment,
        name='consulting_newappointment'),

    url(r'^appointments_doctor/$', consulting_views.appointments_doctor,
        name='consulting_appointments_doctor'),


    # PATIENT_MANAGEMENT: DOCTOR ROLE
    url(r'^patient_management/$', consulting_views.patient_management,
        name='consulting_index_pm'),

    url(r'^patient_management/personal_data_pm/(?P<patient_user_id>\d+)$',
        consulting_views.personal_data_pm,
        name='consulting_personal_data_pm'),

    url(r'^patient_management/editpatient_pm/(?P<patient_user_id>\d+)$',
        consulting_views.editpatient_pm,
        name='consulting_editpatient_pm'),

    url(r'^patient_management/patient_identification_pm/(?P<patient_user_id>\d+)$',
        consulting_views.patient_identification_pm,
        name='consulting_patient_identification_pm'),

    url(r'^patient_management/list_treatments_pm/$',
        consulting_views.list_treatments_pm,
        name='consulting_list_treatments_pm'),

    url(r'^patient_management/detail_treatment_pm/$',
        consulting_views.detail_treatment_pm,
        name='consulting_detail_treatment_pm'),

    url(r'^searcher_component/', consulting_views.searcher_component,
        name='consulting_searcher_component'),

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

    # ADMINISTRATION: DOCTOR ROLE
    url(r'^administration/$', consulting_views.administration,
        name='consulting_index_administration'),

    url(r'^administration/newpatient/$', consulting_views.newpatient,
        name='consulting_newpatient_administration'),

    url(r'^administration/newpatient/newappointment/(?P<newpatient_id>\d+)$',
        consulting_views.newappointment,
        name='consulting_newappointment_administration'),

    # STATISTIC: DOCTOR ROLE
    url(r'^statistic/stratification$', consulting_views.stratification,
        name='consulting_stratification_statistic'),
)

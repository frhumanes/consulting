# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
# from django.views.generic.simple import direct_to_template
from consulting import views as consulting_views
# from cal import views as cal_views

urlpatterns = patterns(
    '',
    url(r'^$', consulting_views.index, name='consulting_index'),

    ############################## CONSULTATION ###############################
    url(r"^consultation/$", consulting_views.today, name='consulting_today'),

    url(r"^consultation/day/(\d+)/(\d+)/(\d+)/$", consulting_views.day,
        name='consulting_day'),

    url(r'^treatment/(?P<action>\w+)/medicine/$',
        consulting_views.add_medicine,
        name='consulting_add_medicine'),

    url(r'^treatment/list/(?P<filter_option>\w+)/(?P<id_patient>\d+)/$',
        consulting_views.get_medicines,
        name='consulting_get_medicines'),

    ##MONITORING
    url(r'^consultation/task/(\d+)/not_assess/(\d+)/$',
        consulting_views.not_assess_task,
        name='consulting_not_assess_task'),

    ########################## PATIENT SURVEYS ################################
    url(r'^surveys/$', consulting_views.list_surveys,
        name='consulting_list_surveys'),
    url(r'^surveys/block/(\d+)/$', consulting_views.self_administered_block,
        name='consulting_self_administered_block'),
    url(r'^surveys/block/(\d+)/extra/$',
        consulting_views.symptoms_worsening,
        name='consulting_symptoms_worsening'),
    url(r'^surveys/register/(\d+)/$', consulting_views.self_register,
        name='consulting_self_register'),

    ######################## ROLE ADMINISTRATIVE/DOCTOR #######################
    url(r'^newpatient/$', consulting_views.newpatient,
        name='consulting_newpatient'),

    url(r'^patient/searcher/', consulting_views.patient_searcher,
        name='consulting_patient_searcher'),

    url(r'^profession/searcher/', consulting_views.searcher_profession,
        name='consulting_searcher_profession'),

    ############################## ROLE DOCTOR ################################
    # PATIENT_MANAGEMENT: DOCTOR ROLE
    url(r'^patient/management/$', consulting_views.patient_management,
        name='consulting_index_pm'),

    #See index_pm.html
    url(r'^patient/management/(?P<patient_user_id>\d+)/$',
        consulting_views.pre_personal_data_pm,
        name='consulting_pre_personal_data_pm'),

    url(r'^patient/(?P<patient_user_id>\d+)/$',
        consulting_views.personal_data_pm,
        name='consulting_personal_data_pm'),

    url(r'^patient/(?P<patient_user_id>\d+)/edit/$',
        consulting_views.editpatient_pm,
        name='consulting_editpatient_pm'),

    url(r'^patient/(?P<patient_user_id>\d+)/identification/$',
        consulting_views.patient_identification_pm,
        name='consulting_patient_identification_pm'),

    url(r'^patient/management/list_by_doctor/(?P<doctor_user_id>\d+)/$',
        consulting_views.patient_list,
        name='consulting_patient_list'),

    # MEDICINES
    url(r'^component/searcher/', consulting_views.searcher_component,
        name='consulting_searcher_component'),

    url(r'^patient/(\d+)/medicines/$',
        consulting_views.list_medicines,
        name='consulting_list_medicines'),

    url(r'^patient/(?P<patient_user_id>\d+)/diagnostics/$',
        consulting_views.get_cie_tree,
        name='consulting_list_illnesses'),

    url(r'^patient/(?P<patient_user_id>\d+)/recommendations/$',
        consulting_views.list_recommendations,
        name='consulting_list_recommendations'),

    url(r'^patient/(?P<patient_user_id>\d+)/reports/$',
        consulting_views.list_reports,
        name='consulting_list_reports'),

    url(r'^patient/(?P<patient_user_id>\d+)/messages/$',
        consulting_views.list_messages,
        name='consulting_list_messages'),

    url(r'^report/(\d+)/$',
        consulting_views.view_report,
        name='consulting_view_report'),

    url(r'^task/(\d+)/$',
        consulting_views.show_task,
        name='consulting_view_task'),

    url(r'^patient/(?P<patient_user_id>\d+)/parameters/(?P<block_code>\d+)/$',
        consulting_views.user_evolution,
        name='consulting_user_evolution'),

    url(r'^patient/(?P<patient_user_id>\d+)/appointments/$',
        consulting_views.list_appointments,
        name='consulting_list_appointments'),

    url(r'^patient/(?P<patient_user_id>\d+)/(?P<filter_option>virtual|face2face|all)_appointments/$',
        consulting_views.get_appointments,
        name='consulting_get_appointments'),


    # ADMINISTRATION: DOCTOR ROLE
    url(r'^administration/$', consulting_views.administration,
        name='consulting_index_administration'),

    url(r'^administration/newpatient/$', consulting_views.newpatient,
        name='consulting_newpatient_administration'),


    #NEW URL'S
    url(r'^consultation/notes/save$',
        consulting_views.save_notes,
        name='consulting_save_notes'),

    url(r'^consultation/task/(?P<id_task>\d+)/variables/$',
        consulting_views.config_task_variables,
        name='consulting_config_variables'),

    url(r"^consultation/(?P<id_appointment>\d+)/$",
        consulting_views.select_illness, name='consulting_start'),

    url(r"^consultation/(?P<id_appointment>\d+)/(?P<code_illness>\w+)/$",
        consulting_views.monitoring, name='consulting_main'),

    url(r"^consultation/(?P<id_appointment>\d+)/(?P<code_illness>\w+)/tasks/incomplete/$",
        consulting_views.list_incomplete_tasks,
        name='consulting_list_incomplete_tasks'),

    url(r"^consultation/(?P<id_appointment>\d+)/(?P<code_illness>\w+)/tasks/self_administered/$",
        consulting_views.list_incomplete_tasks, {'self_administered': True},
        name='consulting_list_self_administered_tasks'),

    url(r"^consultation/(?P<id_appointment>\d+)/(?P<code_illness>\w+)/tasks/successive/$",
        consulting_views.select_successive_survey,
        name='consulting_select_successive_survey'),

    url(r"^consultation/(?P<id_appointment>\d+)/(?P<code_illness>\w+)/tasks/treatment/$",
        consulting_views.prev_treatment_block,
        name='consulting_prev_treatment_block'),

    url(r"^consultation/(?P<id_appointment>\d+)/(?P<code_illness>\w+)/task/(?P<id_task>\d+)/block/(?P<code_block>\d+)/$",
        consulting_views.show_block,
        name='consulting_show_task_block'),

    url(r"^consultation/(?P<id_appointment>\d+)/(?P<code_illness>\w+)/task/(?P<id_task>\d+)/finished/$",
        consulting_views.resume_task,
        name='consulting_finished_task'),

    url(r"^consultation/(?P<id_appointment>\d+)/(?P<code_illness>\w+)/tasks/reports/$",
        consulting_views.list_provisional_reports,
        name='consulting_list_provisional_reports'),

    url(r"^consultation/(?P<id_appointment>\d+)/(?P<code_illness>\w+)/treatment/$",
        consulting_views.list_medicines,
        name='consulting_show_prescription'),

    url(r"^consultation/(?P<action>\w+)_medicine/(?P<id_appointment>\d+)/$",
        consulting_views.add_medicine,
        name='consulting_add_medicine'),

    url(r"^consultation/(?P<id_appointment>\d+)/(?P<code_illness>\w+)/next_self_survey/$",
        consulting_views.select_self_administered_survey_monitoring,
        name='consulting_next_self_administered_survey'),

    url(r"^consultation/(?P<id_appointment>\d+)/(?P<code_illness>\w+)/conclusions/$",
        consulting_views.conclusion_monitoring,
        name='consulting_set_conclusion'),

    url(r"^consultation/(?P<id_appointment>\d+)/(?P<code_illness>\w+)/new_app/$",
        consulting_views.new_app,
        name='consulting_new_app'),

    url(r"^consultation/(?P<id_appointment>\d+)/(?P<code_illness>\w+)/payment/$",
        consulting_views.register_payment,
        name='consulting_register_payment'),

    ##########################################
    url(r"^alert/dismiss/$",
        consulting_views.dismiss_alert,
        name='consulting_dismiss_alert'),

    url(r"^survey/kinds/$",
        consulting_views.survey_kinds,
        name='consulting_survey_kinds'),

    url(r"^keep_alive/(\d+)/$",
        consulting_views.keep_alive,
        name='consulting_keep_alive'),

    url(r"^user_guide/$",
        consulting_views.get_user_guide,
        name='consulting_user_guide'),

)

# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
# from django.views.generic.simple import direct_to_template
from consulting import views as consulting_views
# from cal import views as cal_views

urlpatterns = patterns('',
    # MAIN
    url(r'^$', consulting_views.index, name='consulting_index'),

    ############################## CONSULTATION ###############################
    url(r"^consultation/$", consulting_views.today, name='consulting_today'),

    url(r"^consultation/day/(\d+)/(\d+)/(\d+)/$", consulting_views.day,
        name='consulting_day'),

    url(r"^consultation/month/(\d+)/(\d+)/(prev|next)/$",
        consulting_views.month, name='consulting_month'),

    url(r"^consultation/select_illness/(\d+)/$",
        consulting_views.select_illness, name='consulting_select_illness'),

    url(r"^consultation/select_action/(\d+)/$",
        consulting_views.select_action, name='consulting_select_action'),

    url(r"^consultation/conclusion/(\d+)/(\d+)/$",
        consulting_views.conclusion, name='consulting_conclusion'),
    url(r"^consultation/conclusion/(\d+)/$",
        consulting_views.conclusion, name='consulting_conclusion'),
    url(r"^consultation/conclusion/medicine/new_medicine/(\d+)/$",
        consulting_views.new_medicine_conclusion,
        name='consulting_new_medicine_conclusion'),
    url(r'^consultation/conclusion/medicine/list_medicines_before/(\d+)/$',
        consulting_views.list_medicines_before_conclusion,
        name='consulting_list_medicines_before_conclusion'),
    url(r'^consultation/conclusion/medicine/list_medicines_after/(\d+)/$',
        consulting_views.list_medicines_after_conclusion,
        name='consulting_list_medicines_after_conclusion'),
    url(r'^consultation/conclusion/medicine/detail_medicine/$',
        consulting_views.detail_medicine_conclusion,
        name='consulting_detail_medicine_conclusion'),
    url(r'^consultation/conclusion/medicine/remove_medicine/$',
        consulting_views.remove_medicine_conclusion,
        name='consulting_remove_medicine_conclusion'),

    url(r'^consultation/add_illness/(\d+)/$',
        consulting_views.add_illness,
        name='consulting_add_illness'),
    url(r'^consultation/check_conclusion/(\d+)/$',
        consulting_views.check_conclusion,
        name='consulting_check_conclusion'),

    url(r'^consultation/select_self_administered_survey/(\d+)/$',
        consulting_views.select_self_administered_survey,
        name='consulting_select_self_administered_survey'),
    url(r'^consultation/select_self_administered_survey/(\d+)/(\d+)/$',
        consulting_views.select_self_administered_survey,
        name='consulting_select_self_administered_survey'),
    url(r'^consultation/select_other_survey/(\d+)/(\d+)/$',
        consulting_views.select_other_survey,
        name='consulting_select_other_survey'),
    ##APPOINTMENT
    url(r'^consultation/new_app/select_year_month/(\d+)/(\d+)/(\d+)/$',
        consulting_views.select_year_month,
        name='consulting_select_year_month'),
    url(r'^consultation/new_app/select_year_month/(\d+)/(\d+)/$',
        consulting_views.select_year_month,
        name='consulting_select_year_month'),
    url(r"^consultation/new_app/month/(\d+)/(\d+)/(prev|next)/(\d+)/(\d+)/$",
        consulting_views.month_new_app, name='consulting_month_new_app'),
    url(r"^consultation/new_app/month/(\d+)/(\d+)/(prev|next)/(\d+)/$",
        consulting_views.month_new_app, name='consulting_month_new_app'),

    url(r"^consultation/new_app/day/(\d+)/(\d+)/(\d+)/(\d+)/(\d+)/$",
        consulting_views.day_new_app,
        name='consulting_day_new_app'),
    url(r"^consultation/new_app/day/(\d+)/(\d+)/(\d+)/(\d+)/$",
        consulting_views.day_new_app,
        name='consulting_day_new_app'),
    url(r'^consultation/new_app/app_add/(\d+)/(\d+)/(\d+)/(\d+)/(\d+)/$',
        consulting_views.app_add,
        name='consulting_app_add'),
    url(r'^consultation/new_app/app_add/(\d+)/(\d+)/(\d+)/(\d+)/$',
        consulting_views.app_add,
        name='consulting_app_add'),

    ##SURVEY
    url(r'^consultation/survey/block/(\d+)/(\d+)/$', consulting_views.block,
        name='consulting_block'),
    url(r'^consultation/survey/other_block/(\d+)/(\d+)/$',
        consulting_views.other_block, name='consulting_other_block'),
    url(r'^consultation/survey/select_block/(\d+)/$',
        consulting_views.select_block,
        name='consulting_select_block'),
    url(r'^consultation/survey/administrative_data/(\d+)/(\d+)/$',
        consulting_views.administrative_data,
        name='consulting_administrative_data'),
    url(r"^consultation/survey/medicine/new_medicine/(\d+)/$",
        consulting_views.new_medicine_survey,
        name='consulting_new_medicine_survey'),
    url(r'^consultation/survey/medicine/list_medicines_before/(\d+)/$',
        consulting_views.list_medicines_before_survey,
        name='consulting_list_medicines_before_survey'),
    url(r'^consultation/survey/medicine/detail_medicine/$',
        consulting_views.detail_medicine_survey,
        name='consulting_detail_medicine_survey'),
    url(r'^consultation/survey/medicine/remove_medicine/$',
        consulting_views.remove_medicine_survey,
        name='consulting_remove_medicine_survey'),

    ##MONITORING
    url(r'^consultation/monitoring/(\d+)/$', consulting_views.monitoring,
        name='consulting_monitoring'),

    url(r'^consultation/monitoring/incomplete_surveys/list/(\d+)/$',
        consulting_views.list_incomplete_surveys,
        name='consulting_list_incomplete_surveys'),

    url(r'^consultation/monitoring/incomplete_surveys/not_assess_task/(\d+)/(\d+)/$',
        consulting_views.not_assess_task,
        name='consulting_not_assess_task'),

    url(r'^consultation/monitoring/incomplete_surveys/survey/(\d+)/(\d+)/$',
        consulting_views.incomplete_block,
        name='consulting_incomplete_block'),

    url(r'^consultation/monitoring/incomplete_surveys/variables_mark/(\d+)/(\d+)/$',
        consulting_views.variables_mark,
        name='consulting_variables_mark'),

    url(r'^consultation/monitoring/complete_self_administered_survey/(\d+)/$',
        consulting_views.complete_self_administered_survey,
        name='consulting_complete_self_administered_survey'),

    url(r'^consultation/monitoring/complete_self_administered_survey/select_not_assessed_variables/(\d+)/(\d+)/$',
        consulting_views.select_not_assessed_variables,
        name='consulting_select_not_assessed_variables'),

    url(r'^consultation/monitoring/complete_self_administered_survey/survey/(\d+)/(\d+)/$',
        consulting_views.complete_self_administered_block,
        name='consulting_complete_self_administered_block'),

    url(r'^consultation/monitoring/successive_survey/select/(\d+)/$',
        consulting_views.select_successive_survey,
        name='consulting_select_successive_survey'),

    url(r'^consultation/monitoring/successive_survey/survey/(\d+)/(\d+)/$',
        consulting_views.successive_block,
        name='consulting_successive_survey'),

    url(r'^consultation/monitoring/treatment_survey/prev/(\d+)/$',
        consulting_views.prev_treatment_block,
        name='consulting_prev_treatment_survey'),

    url(r'^consultation/monitoring/treatment_survey/survey/(\d+)/(\d+)$',
        consulting_views.treatment_block,
        name='consulting_treatment_survey'),

    url(r'^consultation/monitoring/behavior_survey/select/(\d+)/$',
        consulting_views.select_behavior_survey,
        name='consulting_select_behavior_survey'),

    url(r'^consultation/monitoring/behavior_survey/survey/(\d+)/(\d+)/$',
        consulting_views.behavior_block,
        name='consulting_behavior_survey'),

    url(r'^consultation/monitoring/finish/conclusion/(\d+)/$',
        consulting_views.conclusion_monitoring,
        name='consulting_conclusion_monitoring'),

    url(r'^consultation/monitoring/finish/new_medicine/(\d+)/$',
        consulting_views.new_medicine_monitoring,
        name='consulting_new_medicine_monitoring'),

    url(r'^consultation/monitoring/finish/list_medicines_before/(\d+)/$',
        consulting_views.list_medicines_before_monitoring,
        name='consulting_list_medicines_before_monitoring'),

    url(r'^consultation/monitoring/finish/list_medicines_after/(\d+)/$',
        consulting_views.list_medicines_after_monitoring,
        name='consulting_list_medicines_after_monitoring'),

    url(r'^consultation/monitoring/finish/detail_medicine/$',
        consulting_views.detail_medicine_monitoring,
        name='consulting_detail_medicine_monitoring'),

    url(r'^consultation/monitoring/finish/remove_medicine/$',
        consulting_views.remove_medicine_monitoring,
        name='consulting_remove_medicine_monitoring'),

    url(r'^consultation/monitoring/finish/add_illness/(\d+)/$',
        consulting_views.add_illness_monitoring,
        name='consulting_add_illness_monitoring'),

    url(r'^consultation/monitoring/finish/select_year_month/(\d+)/(\d+)/(\d+)/$',
        consulting_views.select_year_month_monitoring,
        name='consulting_select_year_month_monitoring'),

    url(r"^consultation/monitoring/finish/day/(\d+)/(\d+)/(\d+)/(\d+)/(\d+)/$",
        consulting_views.day_monitoring,
        name='consulting_day_monitoring'),

    url(r'^consultation/monitoring/finish/app_add/(\d+)/(\d+)/(\d+)/(\d+)/(\d+)/$',
        consulting_views.app_add_monitoring,
        name='consulting_app_add_monitoring'),

    url(r"^consultation/monitoring/finish/month/(\d+)/(\d+)/(prev|next)/(\d+)/(\d+)/$",
        consulting_views.month_monitoring, name='consulting_month_monitoring'),

    url(r'^consultation/monitoring/finish/select_self_administered_survey/(\d+)/$',
        consulting_views.select_self_administered_survey_monitoring,
        name='consulting_select_self_administered_survey_monitoring'),

    ################################ SURVEYS ##################################
    url(r'^surveys/$', consulting_views.list_surveys,
        name='consulting_list_surveys'),
    url(r'^surveys/block/(\d+)/$', consulting_views.self_administered_block,
        name='consulting_self_administered_block'),
    url(r'^surveys/block/symptoms_worsening/(\d+)/$',
        consulting_views.symptoms_worsening,
        name='consulting_symptoms_worsening'),

    ######################### ROLE ADMINISTRATIVE/DOCTOR#######################
    url(r'^newpatient/$', consulting_views.newpatient,
        name='consulting_newpatient'),

    url(r'^patient_searcher/', consulting_views.patient_searcher,
        name='consulting_patient_searcher'),

    ############################## ROLE DOCTOR ###############################
    # PATIENT_MANAGEMENT: DOCTOR ROLE
    url(r'^patient_management/$', consulting_views.patient_management,
        name='consulting_index_pm'),

    #See index_pm.html
    url(r'^patient_management/pre_personal_data_pm/(?P<patient_user_id>\d+)$',
        consulting_views.pre_personal_data_pm,
        name='consulting_pre_personal_data_pm'),

    url(r'^patient_management/personal_data_pm/$',
        consulting_views.personal_data_pm,
        name='consulting_personal_data_pm'),

    url(r'^editpatient_pm/(?P<patient_user_id>\d+)$',
        consulting_views.editpatient_pm,
        name='consulting_editpatient_pm'),

    url(r'^patient_management/patient_identification_pm/\
            (?P<patient_user_id>\d+)$',
        consulting_views.patient_identification_pm,
        name='consulting_patient_identification_pm'),

    # MEDICINES
    url(r'^searcher_component/', consulting_views.searcher_component,
        name='consulting_searcher_component'),

    url(r'^patient_management/medicines/$',
        consulting_views.list_medicines,
        name='consulting_list_medicines'),

    url(r'^patient_management/medicines/new_medicine_pm/$',
        consulting_views.new_medicine_pm,
        name='consulting_new_medicine_pm'),

    url(r'^patient_management/recommendations/$',
        consulting_views.list_recommendations,
        name='consulting_list_recommendations'),

    url(r'^patient_management/reports/$',
        consulting_views.list_reports,
        name='consulting_list_reports'),

    url(r'^patient_management/messages/$',
        consulting_views.list_messages,
        name='consulting_list_messages'),

    url(r'^patient_management/report/(\d+)$',
        consulting_views.view_report,
        name='consulting_view_report'),

    url(r'^patient_management/parameters/$',
        consulting_views.user_evolution,
        name='consulting_user_evolution'),

    url(r'^patient_management/appointments/$',
        consulting_views.list_appointments,
        name='consulting_list_appointments'),

    url(r'^patient_management/medicines/list_medicines_before_pm/$',
        consulting_views.list_medicines_before_pm,
        name='consulting_list_medicines_before_pm'),

    url(r'^patient_management/medicines/list_medicines_after_pm/$',
        consulting_views.list_medicines_after_pm,
        name='consulting_list_medicines_after_pm'),

    url(r'^patient_management/medicines/detail_medicine_pm/$',
        consulting_views.detail_medicine_pm,
        name='consulting_detail_medicine_pm'),

    url(r'^patient_management/medicines/remove_medicine_pm/$',
        consulting_views.remove_medicine_pm,
        name='consulting_remove_medicine_pm'),

    # ADMINISTRATION: DOCTOR ROLE
    url(r'^administration/$', consulting_views.administration,
        name='consulting_index_administration'),

    url(r'^administration/newpatient/$', consulting_views.newpatient,
        name='consulting_newpatient_administration'),

    # STATISTIC: DOCTOR ROLE
    url(r'^statistic/stratification$', consulting_views.stratification,
        name='consulting_stratification_statistic'),

    url(r'^statistic/explotation$', consulting_views.explotation,
        name='consulting_explotation_statistic'),

    #NEW URL'S
    url(r'^consultation/task/(\d+)/report$',
        consulting_views.view_report,
        name='consulting_task_report'),
)

try:
    from django.conf.urls import *
except ImportError:  # django < 1.4
    from django.conf.urls.defaults import *
from cronos import views as cronos_views

# place app url patterns here
urlpatterns = patterns(
    '',
    url(r'^$', cronos_views.start_point, name='cronos_start_point'),
    url(r'^(?P<portal>medico|paciente|enfermero)/$', cronos_views.start_point, name='cronos_start_point'),
    url(r'login/$', cronos_views.cronos_login, name="cronos_login"),
    url(r'logout/$', cronos_views.cronos_logout, name="cronos_logout"),
    url(r'^tasks/$',
        cronos_views.list_tasks, name='cronos_tasks'),
    url(r'^videos/$',
        cronos_views.videoconferences, name='cronos_videoconferences'),
    url(r'^recommendations/$',
        cronos_views.recommendations, name='cronos_recommendations'),
    url(r'^recommendations/edit/$',
        cronos_views.edit_recommendation, name='cronos_new_recommendation'),
    url(r'^recommendations/(?P<id_conclusion>(\d+))/edit/$',
        cronos_views.edit_recommendation, name='cronos_edit_recommendation'),
    url(r'^tasks/for/(?P<code_illness>([#]{0,1}\w+))/home/(?P<id_appointment>(\w+))/$',
        'consulting.views.select_self_administered_survey_monitoring', name='cronos_home_tasks'),
    url(r'^api/cuestionarios/pendientes/$',
        cronos_views.pending_survey, name='cronos_pending_survey'),
    url(r'^api/report/(\d+)/$',
        cronos_views.view_report, name='cronos_view_report'),
    url(r'utilUserController.at4$', cronos_views.fake_auth, name="cronos_fake_auth"),
)
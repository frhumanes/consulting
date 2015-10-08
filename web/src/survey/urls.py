# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from survey import views as survey_views



urlpatterns = patterns(
    '',
    url(r'^$', survey_views.index, name='survey_index'),
    url(r'^(?P<id_survey>\d+)/$', survey_views.view, name='survey_view'),
)

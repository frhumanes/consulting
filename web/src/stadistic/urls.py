# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import *

from stadistic import views 


urlpatterns = patterns('',
# STATISTIC: DOCTOR ROLE
    url(r'^stratification/$', views.stratification,
        name='stratification_statistic'),

    url(r'^stratification/list_(\w+)/(-?\d+)/$', views.stratification_list,
        name='stratification_list'),

    url(r'^explotation/$', views.explotation,
        name='explotation_statistic'),

    url(r'^rebuild_data/$', views.regenerate_data,
        name='rebuild_data'),
)
# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import *
import views


urlpatterns = patterns('',
    url(r'^login/$', views.login_consulting, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
)

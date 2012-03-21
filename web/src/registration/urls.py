# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import *
from registration.views import login_consulting30, logout


urlpatterns = patterns('',
    url(r'^login/$', login_consulting30, name='login'),
    url(r'^logout/$', logout, name='logout'),
)

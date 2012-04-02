# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import *
from registration.views import login_consulting, logout


urlpatterns = patterns('',
    url(r'^login/$', login_consulting, name='login'),
    url(r'^logout/$', logout, name='logout'),
)

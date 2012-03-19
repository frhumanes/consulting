# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import *
from registration.views import *


urlpatterns = patterns('',
    url(r'^register/$', register, name='register'),
    url(r'^logout/$', logout, name='logout'),
)

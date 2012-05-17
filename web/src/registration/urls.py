# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from registration import views as registration_views


urlpatterns = patterns('',
    # url(r'^login/$', views.login_consulting, name='login'),
    url(r'^logout/$', registration_views.logout,
        name='registration_logout'),
)

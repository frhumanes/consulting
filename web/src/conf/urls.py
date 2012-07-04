# -*- encoding: utf-8 -*-

from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from conf import views


urlpatterns = patterns('',
    url(r'^$', views.user_preferences),
)

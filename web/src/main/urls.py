# -*- encoding: utf-8 -*-

from django.conf.urls.defaults import *
import views

urlpatterns = patterns('',
    url(r'^$', views.index, name="main_index"),
)

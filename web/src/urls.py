# -*- encoding: utf-8 -*-
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.defaults import *
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^account/', include('registration.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^', include('consulting.urls')),

    (r'^messages/', include('private_messages.urls')),
)

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
urlpatterns += staticfiles_urlpatterns()

# -*- encoding: utf-8 -*-

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', include('main.urls')),
    (r'^login/', include('registration.urls')),
    (r'^admin/', include(admin.site.urls)),
)


urlpatterns += staticfiles_urlpatterns()

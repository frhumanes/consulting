# -*- encoding: utf-8 -*-
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'^', include('consulting.urls')),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', name='login'),
    # url(r'^accounts/logout/$', 'django.contrib.auth.views.logout',
    #     name='logout'),
    (r'^accounts/', include('registration.urls')),
    (r'^statistic/', include('stadistic.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^messages/', include('private_messages.urls')),
    (r'^calendar/', include('cal.urls')),
    (r'^configuration/', include('conf.urls')),
    (r'^cache/', include('django_memcached.urls')),
)
urlpatterns += staticfiles_urlpatterns()

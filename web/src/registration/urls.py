# -*- encoding: utf-8 -*-
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from registration import views as registration_views
from registration.forms import ValidatingPasswordChangeForm
from django.contrib.auth.views import *
from decorators import update_password_date


urlpatterns = patterns(
    '',
    url(r'^logout/$', registration_views.logout, name='registration_logout'),
    url(r'^password/change/$', password_change,
        {'template_name': 'registration/password_change.html',
         'password_change_form': ValidatingPasswordChangeForm,
         'post_change_redirect': 'done/'},
        name='password_change'),
    url(r'^password/change/done/$',
        update_password_date(password_change_done),
        {'template_name': 'registration/password_done.html'},
        name='password_done'),
    url(r'^password/reset/$', 'django.contrib.auth.views.password_reset',
        {'template_name': 'registration/password_change.html'},
        name="password_reset"),
    url(r'^password/reset/confirm/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        'django.contrib.auth.views.password_reset_confirm',
        {'template_name': 'registration/password_change.html'}),
    url(r'^password/reset/complete/$',
        'django.contrib.auth.views.password_reset_complete',
        {'template_name': 'registration/password_done.html'}),
    url(r'^password/reset/done/$',
        'django.contrib.auth.views.password_reset_done',
        {'template_name': 'registration/password_resend.html'}),
)

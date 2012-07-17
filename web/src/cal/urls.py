# -*- encoding: utf-8 -*-

from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from cal import views


urlpatterns = patterns('',
    url(r'^(\d+)/$', views.main),
    url(r'^$', views.main),

    url(r"^month/(\d+)/(\d+)/(prev|next)/$", views.month),
    url(r"^month/(\d+)/(\d+)/$", views.month),
    url(r"^month$", views.month),

    url(r"^day/(\d+)/(\d+)/(\d+)/$", views.day),

    # ---------
    # Slot Type
    # ---------
    url(r'^slot/type/list/',
        views.list_slot_type,
        name='cal.list_slot_type'),
    url(r'^slot/type/add/',
        views.add_slot_type,
        name='cal.add_slot_type'),
    url(r'^slot/type/edit/(?P<pk>\d+)',
        views.edit_slot_type,
        name='cal.edit_entry_type'),

    url(r'^slot/type/delete/$', views.delete_slot_type,
        name='cal.delete_slot_type'),

    # ----
    # Slot
    # ----
    url(r"^slot/list/(\d+)/(\d+)/$",
        views.list_slot,
        name='cal.list_slot'),
    url(r"^slot/add/(\d+)/(\d+)/$",
        views.add_slot,
        name='cal.add_slot'),
    url(r"^slot/edit/(?P<pk>\d+)/$",
        views.edit_slot,
        name='cal.edit_slot'),
    url(r"^slot/delete/(?P<pk>\d+)/$",
        views.delete_slot,
        name='cal.delete_slot'),

    # -----------
    # Appointment
    # -----------
    url(r'^app/add/(\d+)/(\d+)/(\d+)/(\d+)/$', views.app_add, name='cal.add'),
    url(r'^app/add/(\d+)/(\d+)/(\d+)/$', views.app_add, name='cal.add'),

    url(r'^app/edit/(\d+)/(\d+)/$', views.app_edit, name='cal.edit'),
    url(r'^app/edit/(\d+)/$', views.app_edit, name='cal.edit'),

    url(r'^app/delete/(\d+)/(\d+)/(\d+)/(\d+)/(\d+)/$',
        views.app_delete, name='cal.delete'),
    url(r'^app/delete/$', views.app_delete, name='cal.delete'),

    # ------------
    # Doctor Views
    # ------------
    url(r"^doctor/select/(\d+)/(\d+)/$", views.doctor_calendar),

    url(r"^doctor/(\d+)/(\d+)/(\d+)/(prev|next)/$", views.doctor_month),
    url(r"^doctor/(\d+)/(\d+)/(\d+)/$", views.doctor_month),
    url(r"^doctor/(\d+)/(\d+)/$", views.doctor_month),
    url(r"^doctor/(\d+)/$", views.doctor_month),

    url(r"^doctor/day/(\d+)/(\d+)/(\d+)/(\d+)/$", views.doctor_day),

    # --------
    # vacation
    # --------
    url(r"^vacation/list/$",
        views.list_vacation,
        name='cal.list_vacation'),
    url(r"^vacation/add/$",
        views.add_vacation,
        name='cal.add_vacation'),
    url(r"^vacation/edit/(?P<pk>\d+)/$",
        views.edit_vacation,
        name='cal.edit_vacation'),
    url(r"^vacation/delete/$",
        views.delete_vacation,
        name='cal.delete_vacation'),

    # -----
    # event
    # -----
    url(r"^event/list/$",
        views.list_event,
        name='cal.list_event'),
    url(r"^event/add/$",
        views.add_event,
        name='cal.add_event'),
    url(r"^event/edit/(?P<pk>\d+)/$",
        views.edit_event,
        name='cal.edit_event'),
    url(r"^event/delete/$",
        views.delete_event,
        name='cal.delete_event'),
)
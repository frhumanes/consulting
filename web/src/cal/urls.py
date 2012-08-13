# -*- encoding: utf-8 -*-

from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url

from django.views.generic.simple import direct_to_template

from cal import views


urlpatterns = patterns('',
    url(r'^cal_management/$', views.index, name='cal.index'),

    url(r'^lookfor_patient/(\d+)/(\d+)/(\d+)/$', views.lookfor_patient,
        name='cal.lookfor_patient'),
    url(r'^lookfor_patient_app_list/$', direct_to_template,
        {'template': 'cal/patient/patient_searcher.html'},
        name='cal.lookfor_patient_app_list'),

    url(r'^patient_searcher/$', views.patient_searcher,
        name='cal.patient_searcher'),

    url(r'^check_patient/(\d+)/(\d+)/(\d+)/(\d+)/$', views.check_patient,
        name='cal.check_patient'),

    url(r'^select_doctor/(\d+)/(\d+)/(\d+)/(\d+)/$', views.select_doctor,
        name='cal.select_doctor'),

    url(r'^(\d+)/$', views.main),
    url(r'^$', views.main),

    url(r'^select_month_year/(\d+)/$', views.select_month_year,
        name='cal.select_month_year'),
    url(r'^select_month_year/$', views.select_month_year,
        name='cal.select_month_year'),
    url(r'^select_month_year_new_patient/(\d+)/(\d+)/$',
        views.select_month_year_new_patient,
        name='cal.select_month_year_new_patient'),
    url(r'^select_month_year_new_patient/(\d+)/$',
        views.select_month_year_new_patient,
        name='cal.select_month_year_new_patient'),

    url(r"^month/(\d+)/(\d+)/(prev|next)/$", views.month),
    url(r"^month/(\d+)/(\d+)/$", views.month),
    url(r"^month$", views.month),

    url(r"^day/(\d+)/(\d+)/(\d+)/$", views.day, name='cal.day'),
    url(r"^day/consultation/(\d+)/(\d+)/(\d+)/$", views.day_consultation,
        name='cal.day_consultation'),
    url(r"^day_new_app_admin/(\d+)/(\d+)/(\d+)/(\d+)/(\d+)/$",
        views.day_new_app_admin, name='cal.day_new_app_admin'),


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
    url(r'^app/add_new_app_admin/(\d+)/(\d+)/(\d+)/(\d+)/(\d+)/$',
        views.app_add_new_app_admin, name='cal.app_add_new_app_admin'),

    url(r'^app/add/(\d+)/(\d+)/(\d+)/(\d+)/(\d+)/$', views.app_add,
        name='cal.add'),
    url(r'^app/add/(\d+)/(\d+)/(\d+)/(\d+)/$', views.app_add, name='cal.add'),

    url(r'^app/edit/(\d+)/(\d+)/(\d+)/$', views.app_edit, name='cal.edit'),
    url(r'^app/edit/(\d+)/(\d+)/$', views.app_edit, name='cal.edit'),
    url(r'^app/edit/(\d+)/$', views.app_edit, name='cal.edit'),

    url(r'^app/delete/(\d+)/(\d+)/(\d+)/(\d+)/(\d+)/$',
        views.app_delete, name='cal.delete'),
    url(r'^app/delete/$', views.app_delete, name='cal.delete'),

    url(r'^app/list/patient/(\d+)/$', views.app_list_patient,
        name='cal.app_list_patient'),

    # ------------
    # Doctor Views
    # ------------
    url(r"^doctor/select/(\d+)/(\d+)/$", views.doctor_calendar),

    url(r"^doctor_new_app_admin/(\d+)/(\d+)/(\d+)/(\d+)/(prev|next)/$",
        views.doctor_month_new_app_admin,
        name='cal.doctor_month_new_app_admin'),

    url(r"^doctor/(\d+)/(\d+)/(\d+)/(prev|next)/$", views.doctor_month),
    url(r"^doctor/(\d+)/(\d+)/(\d+)/$", views.doctor_month),
    url(r"^doctor/(\d+)/(\d+)/$", views.doctor_month),
    url(r"^doctor/(\d+)/$", views.doctor_month),

    url(r"^doctor/day/(\d+)/(\d+)/(\d+)/(\d+)/$", views.doctor_day),
    url(r"^doctor/day_new_app_admin/(\d+)/(\d+)/(\d+)/(\d+)/(\d+)/$",
        views.doctor_day_new_app_admin, name='cal.doctor_day_new_app_admin'),

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

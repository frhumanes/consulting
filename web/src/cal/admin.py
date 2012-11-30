# -*- encoding: utf-8 -*-

from django.contrib import admin
from django.utils.translation import ugettext as _

from cal.models import Appointment
from cal.models import SlotType
from cal.models import Vacation
from cal.models import Event
from cal.models import Slot

from django.contrib.auth.models import User

def user_unicode(self):
    try:
        return  u'%s' % (self.get_profile().get_full_name())
    except:
        return  u'%s' % (self.username)

User.__unicode__ = user_unicode

admin.site.unregister(User)
admin.site.register(User)


class SlotTypeAdmin(admin.ModelAdmin):
    list_display = ["doctor", "title", "duration"]
    list_filter = ["doctor__profiles__role", "doctor", "duration"]
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('title',)
    fieldsets = (
        (None, {
            'fields': ('doctor', ('title', 'duration'))
        }),
        (_(u'Registro'), {
            'classes': ('collapse',),
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


class SlotAdmin(admin.ModelAdmin):
    list_display = ["creator", "slot_type", "weekday", "month", "year", "start_time",
        "end_time", "description"]
    list_filter = ["creator", "slot_type", "weekday", "month", "year"]
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('slot_type__title', 'description')
    fieldsets = (
        (None, {
            'fields': ('creator', 'slot_type')
        }),
        (_(u'Configuración'), {
            'fields': (("start_time", "end_time"),("weekday", "month", "year"))
            }),
        (_(u'Registro'), {
            'classes': ('collapse',),
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )



class AppointmentAdmin(admin.ModelAdmin):
    list_display = ["doctor", "patient", "app_type", "notify", "created_by"]
    list_filter = ["doctor", "patient", "app_type", "notify", "created_by"]
    readonly_fields = ('duration', 'created_at', 'updated_at')
    search_fields = ('app_type__title', 'description')
    fieldsets = (
        (None, {
            'fields': ('doctor', 'patient')
        }),
        (_(u'Configuración'), {
            'fields': ('app_type', 'notify', 'duration' , "description", "date", ("start_time", "end_time"))
            }),
        (_(u'Registro'), {
            'classes': ('collapse',),
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


class VacationAdmin(admin.ModelAdmin):
    list_display = ["doctor", "date", "description"]
    list_filter = ["doctor", "date"]
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('description',)
    fieldsets = (
        (None, {
            'fields': ('doctor', 'description', 'date')
        }),
        (_(u'Registro'), {
            'classes': ('collapse',),
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


class EventAdmin(admin.ModelAdmin):
    list_display = ["doctor", "date", "start_time", "end_time", "description"]
    list_filter = ["doctor", "date"]
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('description',)
    fieldsets = (
        (None, {
            'fields': ('doctor',)
        }),
        (_(u'Configuración'), {
            'fields': ("description", "date", ("start_time", "end_time"))
            }),
        (_(u'Registro'), {
            'classes': ('collapse',),
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


admin.site.register(SlotType, SlotTypeAdmin)
admin.site.register(Slot, SlotAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Vacation, VacationAdmin)
admin.site.register(Event, EventAdmin)

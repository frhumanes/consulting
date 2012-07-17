# -*- encoding: utf-8 -*-

from django.contrib import admin

from cal.models import Appointment
from cal.models import SlotType
from cal.models import Vacation
from cal.models import Event
from cal.models import Slot


class SlotTypeAdmin(admin.ModelAdmin):
    list_display = ["doctor", "title", "duration"]
    list_filter = ["doctor", "duration"]
    readonly_fields = ('created_at', 'updated_at')


class SlotAdmin(admin.ModelAdmin):
    list_display = ["creator", "slot_type", "weekday", "start_time",
        "end_time", "date", "description"]
    list_filter = ["creator", "slot_type", "weekday"]
    readonly_fields = ('created_at', 'updated_at')


class AppointmentAdmin(admin.ModelAdmin):
    list_display = ["created_by", "doctor", "patient", "app_type"]
    list_filter = ["created_by", "doctor", "patient", "app_type"]
    readonly_fields = ('created_at', 'updated_at')


class VacationAdmin(admin.ModelAdmin):
    list_display = ["doctor", "date", "description"]
    list_filter = ["doctor", "date"]
    readonly_fields = ('created_at', 'updated_at')


class EventAdmin(admin.ModelAdmin):
    list_display = ["doctor", "date", "description"]
    list_filter = ["doctor", "date"]
    readonly_fields = ('created_at', 'updated_at')


admin.site.register(SlotType, SlotTypeAdmin)
admin.site.register(Slot, SlotAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Vacation, VacationAdmin)
admin.site.register(Event, EventAdmin)

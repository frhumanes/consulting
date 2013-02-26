# -*- encoding: utf-8 -*-

from django.contrib import admin
from django import forms
from django.db import models
from django.utils.translation import ugettext as _

from consulting.models import *

from django.contrib.auth.models import User
"""
def user_unicode(self):
    try:
        return  u'%s' % (self.get_profile().get_full_name())
    except:
        return  u'%s' % (self.username)

User.__unicode__ = user_unicode

admin.site.unregister(User)
admin.site.register(User)
"""
class AnswerAdmin(admin.StackedInline):
    #fieldsets = [('Medicines', {'fields': ['patient', 'survey', 'task']})]
    model = Answer
    ordering = ('question',)
    fieldsets = ((None, {
            'fields': ('question', 'option', 'value')
        }),)

#admin.site.register(Result, ResultAdmin)

class TaskAdmin(admin.ModelAdmin):
    list_filter = ['survey', 'patient',  'self_administered', 'assess', 'completed', 'end_date']
    list_display = ('patient', 'survey', 'self_administered', 'assess',
                    'completed', 'creation_date', 'end_date')
    search_fields = ('observations',)
    fieldsets = (
        (None, {
            'fields': ('patient', 'observations')
        }),
        (_(u'Configuración'), {
            'fields': ('survey', 'kind', 'self_administered', 'previous_days', 'questions')
        }),
        (_(u'Estado'), {
            'fields': ('assess', 'completed', 'end_date')
        }),
        (_(u'Registro'), {
            'classes': ('collapse',),
            'fields': ('created_by', )
        }),
    )
    formfield_overrides = {
        models.ManyToManyField: {'widget': forms.CheckboxSelectMultiple},
    }


admin.site.register(Task, TaskAdmin)


class MedicineAdmin(admin.ModelAdmin):
    list_filter = ['patient', 'is_previous', 'after_symptoms', 'date']
    list_display = ('patient', 'component',
                    'is_previous', 'after_symptoms',
                    'posology', 'dosification')
    search_fields = ('component__name', 'posology','dosification')
    ordering = ('patient', 'created_at')
    fieldsets = (
        (None, {
            'fields': ('patient', 'component')
        }),
        (_(u'Prescipción'), {
            'fields': ('is_previous',
                    'after_symptoms',
                    'months', 'posology', 'dosification')
        }),
        (_(u'Registro'), {
            'classes': ('collapse',),
            'fields': ('created_by',)
        }),
    )

admin.site.register(Medicine, MedicineAdmin)


class ResultAdmin(admin.ModelAdmin):
    list_display = ('patient', 'survey', 'created_at', 'updated_at')
    search_fields = ('survey__title',)
    ordering = ('updated_at', 'patient',)
    list_filter=('patient', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('patient', 'survey')
        }),
        (_(u'Configuración'), {
            'fields': ('task',)
        }),
        (_(u'Registro'), {
            'classes': ('collapse',),
            'fields': ('created_by',)
        }),
    )
    inlines = [
        AnswerAdmin,
    ]

admin.site.register(Result, ResultAdmin)


class ConclusionAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['appointment', 'observation', 'recommendation', 'extra']}),
        (_(u'Registro'), {
            'classes': ('collapse',),
            'fields': ('created_by',)
        }),]
    list_filter = ('appointment__patient', 
                   'appointment__patient__profiles__doctor',
                   'date')
    list_display = ('appointment', 'date')
    search_fields = ('observation',
                    'recommendation',
                    'extra')
    ordering = ('appointment',)

admin.site.register(Conclusion, ConclusionAdmin)

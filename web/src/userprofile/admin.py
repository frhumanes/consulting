# -*- encoding: utf-8 -*-

from django.contrib import admin
from django.utils.translation import ugettext as _
from userprofile.models import Profile
from django import forms
from django.db import models


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'sex', 'email', 'doctor', 'role')
    search_fields = ('name', 'first_surname', 'medical_number'
                    'second_surname', 'address', 'town', 'postcode',
                    'dob', 'phone1', 'phone2', 'email', 'profession',
                    )
    readonly_fields = ('updated_password_at',)
    list_filter = ('role', 'sex', 'doctor', 'status')
    ordering = ('first_surname', 'second_surname', 'name', 'role')
    fieldsets =((None, {
                    'fields': ('user', )
                }),
                (_(u'Datos personales'), {
                    'fields': ('name', 'first_surname', 
                               'second_surname', 'nif', 'sex',
                               'dob', 'status')
                    }),
                (_(u'Otros datos personales'), {
                    'fields': ('address', 'town', 'postcode', 
                                'phone1', 'phone2', 'emergency_phone', 'email',
                                'education', 'profession', 'source')
                    }),
                (_(u'Consulta'), {
                    'fields': ('medical_number', 'doctor', 'role')
                    }),
                (_(u'Diagnóstico'), {
                    'classes': ('collapse',),
                    'fields': ('illnesses',)
                    }),
                (_(u'Registro'), {
                        'classes': ('collapse',),
                        'fields': ('created_by', 'updated_password_at')
                    }),
                )
    formfield_overrides = {
        models.ManyToManyField: {'widget': forms.CheckboxSelectMultiple},
    }

admin.site.register(Profile, ProfileAdmin)

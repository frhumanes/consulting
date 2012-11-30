# -*- encoding: utf-8 -*-

from django.contrib import admin
from django import forms
from django.db import models
from django.utils.translation import ugettext as _
from survey.models import *


class SurveyAdmin(admin.ModelAdmin):
    fieldsets = [
                (None, {
                    'fields': ['name', 'code']
                }),
                ('Ajustes', {
                    'fields':('multitype','blocks')
                    })
                ]
    list_display = ('name', 'code', 'multitype')
    search_fields = ('code', 'name')
    list_filter = ['multitype']
    ordering = ('code', 'name', 'multitype')
    formfield_overrides = {
        models.ManyToManyField: {'widget': forms.CheckboxSelectMultiple},
    }

admin.site.register(Survey, SurveyAdmin)


class CategoryAdmin(admin.ModelAdmin):
    fieldsets = [(None, {
                    'fields': ['name', 'code', 'kind']
                    }),
                 ('Preguntas', {
                    'classes':['collapse'], 
                    'fields': ['questions']
                    }),
                 (u'Variables', {
                    'classes': ('collapse',),
                    'fields': ['variables']
                    })
                ]
    list_display = ('name', 'code', 'kind')
    list_filter = ['kind']
    search_fields = ('code', 'name')
    ordering = ('code', 'name', 'kind')
    formfield_overrides = {
        models.ManyToManyField: {'widget': forms.CheckboxSelectMultiple},
    }

admin.site.register(Category, CategoryAdmin)


class BlockAdmin(admin.ModelAdmin):
    fieldsets = [
                (None, {
                    'fields': ['name', 'code']
                }),
                ('Ajustes', {
                    'fields':('kind',)
                }),
                ('Bloques', {
                    'classes': ('collapse',),
                    'fields': ['categories']
                    }),
                #(u'Fórmulas', {
                #    'classes': ('collapse',),
                #    'fields': ['formulas']
                #    })
                ]
    list_display = ('name', 'code', 'kind')
    list_filter = ['kind']
    search_fields = ('code', 'name')
    ordering = ('code', 'kind')
    formfield_overrides = {
        models.ManyToManyField: {'widget': forms.CheckboxSelectMultiple},
    }

admin.site.register(Block, BlockAdmin)


class OptionAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['text', 'code', 'weight',
                ]}),
                ('Pregunta', {
                    'fields': ['question']
                    }),]
    list_filter = ['question__code']
    list_display = ('code', 'text', 'weight', 'question')
    search_fields = ('code', 'text', 'weight')
    ordering = ('code',)

admin.site.register(Option, OptionAdmin)

class OptionInlineAdmin(admin.StackedInline):
    fieldsets = [(None, {'fields': ['text', 'code', 'weight']})]
    model = Option


class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['text', 'code']}),
                ('Ajustes', {
                    'fields': ['required', 'single','kind']
                    }),]
    list_display = ('code', 'text', 'required', 'single')
    list_filter = ['kind', 'required', 'single']
    search_fields = ('code', 'text')
    ordering = ('code',)
    inlines = [
        OptionInlineAdmin,
    ]

admin.site.register(Question, QuestionAdmin)

from django.contrib import admin
from django import forms
from django.db import models
from django.utils.translation import ugettext as _

from medicament.models import *


class GroupAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['name', 'adverse_reaction']})]
    list_display = ('name', 'adverse_reaction')
    search_fields = ('name', 'adverse_reaction')
    ordering = ('id',)

admin.site.register(Group, GroupAdmin)


class ComponentAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields':
                ['name', 'kind_component', 'groups']})]
    list_display = ('name', 'kind_component', )
    search_fields = ('name', 'kind_component',)
    list_filter = ['kind_component']
    ordering = ('kind_component', 'name',)
    formfield_overrides = {
        models.ManyToManyField: {'widget': forms.CheckboxSelectMultiple},
    }

admin.site.register(Component, ComponentAdmin)

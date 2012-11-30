from django.contrib import admin
from illness.models import *
from django.db import models
from django import forms


class IllnessAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['code', 'name', 'surveys']})]
    list_display = ('code', 'name')
    search_fields = ('code', 'name')
    ordering = ('code', )
    formfield_overrides = {
        models.ManyToManyField: {'widget': forms.CheckboxSelectMultiple},
    }

admin.site.register(Illness, IllnessAdmin)

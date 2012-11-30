from django.contrib import admin
from formula.models import *


class DimensionAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['name', 'polynomial', 'factor']})]
    list_filter = ['name']
    list_display = ('name', 'polynomial', 'factor')
    search_fields = ('name', 'polynomial', 'factor')
    ordering = ('name',)

admin.site.register(Dimension, DimensionAdmin)


class VariableAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['dimension', 'name', 'code']})]
    list_filter = ["dimension"]
    list_display = ('code', 'name', 'dimension')
    search_fields = ('code', 'name', 'dimension')
    ordering = ('dimension', 'code')

admin.site.register(Variable, VariableAdmin)


class FormulaAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['variable', 'polynomial',
                'factor', 'sibling']})]
    list_filter = ["variable", "kind"]
    list_display = ('variable', 'kind')
    search_fields = ('variable__name', 'polynomial', 'factor')
    ordering = ('variable', )

admin.site.register(Formula, FormulaAdmin)

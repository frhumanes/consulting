from django.contrib import admin
from formula.models import *


class DimensionAdmin(admin.ModelAdmin):
    fieldsets = [('Dimensions', {'fields': ['name', 'polynomial', 'factor']})]
    list_display = ('name', 'polynomial', 'factor')
    search_fields = ('name', 'polynomial', 'factor')
    ordering = ('name',)

admin.site.register(Dimension, DimensionAdmin)


class VariableAdmin(admin.ModelAdmin):
    fieldsets = [('Variables', {'fields': ['dimension', 'name', 'code']})]
    list_display = ('code', 'name', 'dimension')
    search_fields = ('code', 'name', 'dimension')
    ordering = ('dimension', 'code')

admin.site.register(Variable, VariableAdmin)


class FormulaAdmin(admin.ModelAdmin):
    fieldsets = [('Formulas', {'fields': ['variable', 'polynomial',
                'factor', 'sibling']})]
    list_display = ('variable', 'kind', 'polynomial', 'factor')
    search_fields = ('variable', 'polynomial', 'factor')
    ordering = ('variable', )

admin.site.register(Formula, FormulaAdmin)

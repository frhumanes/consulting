from django.contrib import admin
from formula.models import *


class DimensionAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['name', 'polynomial', 'factor']})]
    list_filter = ['name']
    list_display = ('name', 'polynomial', 'factor')
    search_fields = ('name', 'polynomial', 'factor')
    ordering = ('name',)

admin.site.register(Dimension, DimensionAdmin)

class ConditionInlineAdmin(admin.StackedInline):
    #fieldsets = [('Medicines', {'fields': ['patient', 'survey', 'task']})]
    model = Condition

class VariableAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['dimension', 'name', 'code']}),
                 (u'Rango', {'fields': ['vmin', 'vmax']})]
    list_filter = ["dimension"]
    list_display = ('code', 'name', 'dimension')
    search_fields = ('code', 'name')
    ordering = ('dimension', 'code')
    inlines = [
        ConditionInlineAdmin,
    ]

admin.site.register(Variable, VariableAdmin)


class FormulaAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['variable', 'polynomial',
                'factor', 'kind', 'sibling']})]
    list_filter = ["variable", "kind"]
    list_display = ('variable', 'kind')
    search_fields = ('variable__name', 'polynomial', 'factor')
    ordering = ('variable', )

admin.site.register(Formula, FormulaAdmin)

class LevelInlineAdmin(admin.StackedInline):
    fieldsets = [(None, {'fields': ['score', 'name',  'css', 'color']})]
    model = Level

class ScaleAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['name', 'polynomial',
                'factor', 'kind', 'inverted', 'key', 'action']})]
    list_filter = ["name"]
    list_display = ('name', 'key', 'polynomial')
    search_fields = ('name', 'polynomial')
    ordering = ('name', )
    inlines = [
        LevelInlineAdmin,
    ]

admin.site.register(Scale, ScaleAdmin)

admin.site.register(Risk)
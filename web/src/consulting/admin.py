from django.contrib import admin
from consulting.models import *


class TaskAdmin(admin.ModelAdmin):
    fieldsets = [('Tasks', {'fields': ['patient', 'survey',
                    'self_administered', 'assess', 'completed']})]
    list_display = ('patient', 'survey', 'self_administered', 'assess',
                    'completed')
    search_fields = ('patient', 'survey', 'self_administered', 'assess',
                    'completed')
    ordering = ('patient', )

admin.site.register(Task, TaskAdmin)


class MedicineAdmin(admin.ModelAdmin):
    fieldsets = [('Medicines', {'fields': ['patient', 'component',
                    'conclusion', 'result', 'before_after_first_appointment',
                    'before_after_symptom',
                    'months', 'posology']})]
    list_display = ('patient', 'component',
                    'before_after_first_appointment', 'before_after_symptom',
                    'months', 'posology')
    search_fields = ('patient', 'component',
                    'before_after_first_appointment', 'before_after_symptom',
                    'months', 'posology')
    ordering = ('patient', )

admin.site.register(Medicine, MedicineAdmin)


class ResultAdmin(admin.ModelAdmin):
    fieldsets = [('Medicines', {'fields': ['patient', 'survey',
                'task']})]
    list_display = ('patient', 'survey', 'task')
    search_fields = ('patient', 'survey', 'task')
    ordering = ('patient',)

admin.site.register(Result, ResultAdmin)


class ReportAdmin(admin.ModelAdmin):
    fieldsets = [('Reports', {'fields': ['patient', 'illness',
                'survey', 'result']})]
    list_display = ('patient', 'illness',
                'survey', 'result')
    search_fields = ('patient', 'illness',
                'survey', 'result')
    ordering = ('patient',)

admin.site.register(Report, ReportAdmin)


class ConclusionAdmin(admin.ModelAdmin):
    fieldsets = [('Conclusions', {'fields': ['patient', 'result',
                'appointment', 'observation', 'recommendation']})]
    list_display = ('patient', 'result', 'appointment', 'observation',
                    'recommendation', 'date')
    search_fields = ('patient', 'result', 'appointment', 'observation',
                    'recommendation', 'date')
    ordering = ('patient',)

admin.site.register(Conclusion, ConclusionAdmin)

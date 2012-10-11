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
                    'is_previous',
                    'after_symptoms',
                    'months', 'posology']})]
    list_display = ('patient', 'component',
                    'is_previous', 'after_symptoms',
                    'months', 'posology')
    search_fields = ('patient', 'component',
                    'is_previous', 'after_symptoms',
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




class ConclusionAdmin(admin.ModelAdmin):
    fieldsets = [('Conclusions', {'fields': ['patient',
                'appointment', 'observation', 'recommendation']})]
    list_display = ('patient', 'appointment', 'observation',
                    'recommendation', 'date')
    search_fields = ('patient', 'appointment', 'observation',
                    'recommendation', 'date')
    ordering = ('patient',)

admin.site.register(Conclusion, ConclusionAdmin)

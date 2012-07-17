from django.contrib import admin
from consulting.models import *


class TaskAdmin(admin.ModelAdmin):
    fieldsets = [('Tasks', {'fields': ['patient', 'survey', 
                    'self_administered', 'value',
                    'completed']})]
    list_display = ('patient', 'survey',
                    'self_administered', 'value',
                    'completed')
    search_fields = ('patient', 'survey',
                    'self_administered', 'value',
                    'completed')
    ordering = ('patient', )

admin.site.register(Task, TaskAdmin)


class RecommendationAdmin(admin.ModelAdmin):
    fieldsets = [('Recommendations', {'fields': ['patient',
                'content']})]
    list_display = ('patient', 'content')
    search_fields = ('patient', 'content')
    ordering = ('patient', )

admin.site.register(Recommendation, RecommendationAdmin)


class MedicineAdmin(admin.ModelAdmin):
    fieldsets = [('Medicines', {'fields': ['patient', 'component',
                    'before_after_first_appointment', 'before_after_symptom',
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
    fieldsets = [('Medicines', {'fields': ['patient', 'survey', 'answers',
                'task']})]
    list_display = ('patient', 'survey', 'task')
    search_fields = ('patient', 'survey', 'task')
    ordering = ('patient',)

admin.site.register(Result, ResultAdmin)


class AnswerAdmin(admin.ModelAdmin):
    fieldsets = [('Answers', {'fields': ['option', 'text']})]
    list_display = ('option', 'text')
    search_fields = ('option', 'text')
    ordering = ('option',)

admin.site.register(Answer, AnswerAdmin)


class ReportAdmin(admin.ModelAdmin):
    fieldsets = [('Reports', {'fields': ['patient', 'illness',
                'survey', 'result']})]
    list_display = ('patient', 'illness',
                'survey', 'result')
    search_fields = ('patient', 'illness',
                'survey', 'result')
    ordering = ('patient',)

admin.site.register(Report, ReportAdmin)

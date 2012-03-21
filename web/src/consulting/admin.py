from django.contrib import admin
from consulting.models import *


class ReportAdmin(admin.ModelAdmin):
    fieldsets = [('Reports', {'fields': ['name', 'patient', 'visit', 'kind',
                'observations', 'date']})]
    list_display = ('name', 'patient', 'visit', 'kind', 'observations', 'date')
    search_fields = ('name', 'patient', 'visit', 'kind', 'observations',
                    'date')
    ordering = ('name', 'patient', 'date')

admin.site.register(Report, ReportAdmin)


class VisitAdmin(admin.ModelAdmin):
    fieldsets = [('Visits', {'fields': ['patient', 'doctor', 'questionnaire',
                'answers', 'treatment', 'date']})]
    list_display = ('patient', 'doctor', 'questionnaire', 'treatment', 'date')
    search_fields = ('patient', 'doctor', 'questionnaire', 'treatment', 'date')
    ordering = ('patient', 'date')


admin.site.register(Visit, VisitAdmin)


class QuestionnaireAdmin(admin.ModelAdmin):
    fieldsets = [('Questionnaires', {'fields': ['survey', 'self_administered',
                'rate', 'creation_date', 'start_date', 'end_date', 'from_date',
                'to_date', 'completed']})]
    list_display = ('survey', 'creation_date', 'start_date', 'end_date',
                    'from_date', 'to_date', 'completed')
    search_fields = ('survey', 'creation_date', 'start_date', 'end_date',
                    'from_date', 'to_date', 'completed')
    ordering = ('survey', 'creation_date')

admin.site.register(Questionnaire, QuestionnaireAdmin)


class AnswerAdmin(admin.ModelAdmin):
    fieldsets = [('Answers', {'fields': ['option', 'text']})]
    list_display = ('option', 'text')
    search_fields = ('option', 'text')
    ordering = ('option',)

admin.site.register(Answer, AnswerAdmin)


#-----------------------------------------------------------------------------#
#--------------------------------- Treatment ---------------------------------#
#-----------------------------------------------------------------------------#
class TreatmentAdmin(admin.ModelAdmin):
    fieldsets = [('Treatments', {'fields': ['patient', 'medications',
                'date']})]
    list_display = ('patient', 'date')
    search_fields = ('patient', 'date')
    ordering = ('patient',)

admin.site.register(Treatment, TreatmentAdmin)


class MedicationAdmin(admin.ModelAdmin):
    fieldsets = [('Medications', {'fields': ['medicine', 'posology', 'time',
                'before_after']})]
    list_display = ('medicine', 'posology', 'time', 'before_after')
    search_fields = ('medicine', 'posology', 'time', 'before_after')
    ordering = ('medicine',)

admin.site.register(Medication, MedicationAdmin)

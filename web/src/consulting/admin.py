from django.contrib import admin
from consulting.models import *


class ReportAdmin(admin.ModelAdmin):
    fieldsets = [('Reports', {'fields': ['name', 'patient', 'appointment',
                'kind', 'observations', 'date']})]
    list_display = ('name', 'patient', 'appointment', 'kind', 'observations',
                    'date')
    search_fields = ('name', 'patient', 'appointment', 'kind', 'observations',
                    'date')
    ordering = ('name', 'patient', 'date')

admin.site.register(Report, ReportAdmin)


class AppointmentAdmin(admin.ModelAdmin):
    fieldsets = [('Appointments', {'fields': ['patient', 'doctor',
                'questionnaire', 'answers', 'treatment', 'date', 'hour']})]
    list_display = ('patient', 'doctor', 'questionnaire', 'treatment', 'date',
                    'hour')
    search_fields = ('patient', 'doctor', 'questionnaire', 'treatment', 'date',
                    'hour')
    ordering = ('patient', 'date')


admin.site.register(Appointment, AppointmentAdmin)


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
    fieldsets = [('Treatments', {'fields': ['patient', 'date']})]
    list_display = ('patient', 'date')
    search_fields = ('patient', 'date')
    ordering = ('patient',)

admin.site.register(Treatment, TreatmentAdmin)


class PrescriptionAdmin(admin.ModelAdmin):
    fieldsets = [('Prescriptions', {'fields': ['treatment', 'component',
                    'before_after', 'months', 'posology']})]
    list_display = ('treatment', 'before_after', 'months', 'posology')
    search_fields = ('treatment', 'before_after', 'months', 'posology')
    ordering = ('component',)

admin.site.register(Prescription, PrescriptionAdmin)

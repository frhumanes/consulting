# -*- encoding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.conf import settings

from log.models import TraceableModel
from survey.models import Survey, Block, Question, Option
from medicament.models import Component
from illness.models import Illness
from cal.models import Appointment


class Task(TraceableModel):
    patient = models.ForeignKey(User, related_name='patient_tasks')

    survey = models.ForeignKey(Survey, related_name="survey_tasks")

    questions = models.ManyToManyField(Question,
                                        related_name="questions_tasks",
                                        blank=True, null=True)

    treated_blocks = models.ManyToManyField(Block, related_name='blocks_tasks')

    appointment = models.ForeignKey(Appointment,
                                    related_name="appointment_tasks")

    self_administered = models.NullBooleanField(_(u'¿Tarea autoadministrada?'))

    creation_date = models.DateTimeField(_(u'Fecha de creación de la tarea'),
                                        auto_now_add=True)

    start_date = models.DateTimeField(_(u'Fecha de comienzo de la encuesta'),
                                        blank=True, null=True)

    end_date = models.DateTimeField(_(u'Fecha de finalización de la encuesta'),
                                    blank=True, null=True)

    from_date = models.DateField(
                    _(u'Fecha a partir de la cual puede realizar la encuesta'),
                    blank=True, null=True)

    to_date = models.DateField(
                    _(u'Fecha hasta la que puede realizar la encuesta'),
                    blank=True, null=True)

    value = models.BooleanField(_(u'¿Seguir valorando la encuesta?'),
                                default=True)

    completed = models.BooleanField(
                    _(u'¿Ha contestado todas las preguntas de la encuesta?'),
                    default=False)

    def __unicode__(self):
        return u'id: %s task: %s %s %s' \
            % (self.id, self.patient, self.survey, self.creation_date)


class Medicine(TraceableModel):
    BEFORE_AFTER_CHOICES = (
        (settings.BEFORE, _(u'Anterior')),
        (settings.AFTER, _(u'Posterior')),
    )
    patient = models.ForeignKey(User, related_name='patient_medicines')

    component = models.ForeignKey(Component,
                                related_name='component_medicines',
                                blank=True, null=True)
    conclusion = models.ForeignKey('Conclusion',
                                related_name='conclusion_medicines',
                                blank=True, null=True)
    result = models.ForeignKey('Result', related_name='result_medicines',
                              blank=True, null=True)

    before_after_first_appointment = models.IntegerField(
                                        _(u'Anterior/Posterior\
                                        Primera Cita'),
                                        choices=BEFORE_AFTER_CHOICES,
                                        blank=True, null=True)
    before_after_symptom = models.IntegerField(_(u'Anterior/Posterior\
                                    síntomas psiquiátricos'),
                                    choices=BEFORE_AFTER_CHOICES,
                                    blank=True, null=True)
    months = models.IntegerField(_(u'Número de meses de toma del fármaco'),
                                    blank=True, null=True)
    posology = models.CharField(_(u'Posología (mg/día)'), max_length=255,
                                    blank=True)
    date = models.DateTimeField(_(u'Fecha'), auto_now_add=True)

    def __unicode__(self):
        return u'id: %s medicine: %s' % (self.id, self.component)

    def get_before_after_symptom(self):
        if self.before_after_symptom == settings.BEFORE:
            before_after_symptom = _(u'Anterior')
        else:
            before_after_symptom = _(u'Posterior')

        return before_after_symptom

    def get_before_after_first_appointment(self):
        if self.before_after_first_appointment == settings.BEFORE:
            before_after_first_appointment = _(u'Anterior')
        else:
            before_after_first_appointment = _(u'Posterior')

        return before_after_first_appointment


class Result(TraceableModel):
    patient = models.ForeignKey(User, related_name='patient_results')

    survey = models.ForeignKey(Survey, related_name="survey_results")

    options = models.ManyToManyField(Option, related_name="options_results")

    task = models.ForeignKey(Task, related_name="task_results")

    date = models.DateTimeField(_(u'Fecha'), auto_now_add=True)

    symptoms_worsening = models.CharField(max_length=5000, blank=True,
                                            null=True)

    def __unicode__(self):
        return u'id: %s result: %s %s' % (self.id, self.patient, self.survey)


class Report(TraceableModel):
    patient = models.ForeignKey(User, related_name='patient_reports')

    illness = models.ForeignKey(Illness, related_name='illness_reports')

    survey = models.ForeignKey(Survey, related_name="survey_reports")

    result = models.ForeignKey(Result, related_name='result_reports')

    date = models.DateTimeField(_(u'Fecha del Informe'), auto_now_add=True)

    def __unicode__(self):
        return u'id: %s report: %s %s' % (self.id, self.patient, self.illness)


class Conclusion(TraceableModel):
    patient = models.ForeignKey(User, related_name='patient_conclusions')

    result = models.ForeignKey(Result, unique=True,
                                related_name='result_conclusion',
                                blank=True, null=True)

    appointment = models.ForeignKey(Appointment,
                                    related_name="appointment_conclusions")

    observation = models.CharField(max_length=5000, blank=True, null=True)

    recommendation = models.CharField(max_length=5000, blank=True, null=True)

    date = models.DateTimeField(_(u'Fecha'), auto_now_add=True)

    def __unicode__(self):
        return u'id: %s conclusion: %s %s' \
                                % (self.id, self.patient, self.appointment)

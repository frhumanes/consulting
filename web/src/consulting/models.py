# -*- encoding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.conf import settings
from survey.models import Option, Survey
from medicament.models import Component
from illness.models import Illness


class Task(models.Model):
    patient = models.ForeignKey(User, related_name='patient_tasks')

    survey = models.ForeignKey(Survey, related_name="survey_tasks")

    self_administered = models.NullBooleanField(_(u'¿Tarea autoadministrada?'))

    creation_date = models.DateTimeField(_(u'Fecha de creación de la tarea'),
                                        auto_now_add=True)

    start_date = models.DateTimeField(_(u'Fecha de comienzo de la encuesta'),
                                        blank=True, null=True)

    end_date = models.DateTimeField(_(u'Fecha de finalización de la encuesta'),
                                    blank=True, null=True)

    from_date = models.DateTimeField(
                    _(u'Fecha a partir de la cual puede realizar la encuesta'),
                    blank=True, null=True)

    to_date = models.DateTimeField(
                    _(u'Fecha hasta la que puede realizar la encuesta'),
                    blank=True, null=True)

    value = models.BooleanField(_(u'¿Seguir valorando la encuesta?'),
                                default=True)

    completed = models.BooleanField(
                    _(u'¿Ha contestado todas las preguntas de la encuesta?'),
                    default=False)

    def __unicode__(self):
        return u'%s %s %s' % (self.patient, self.survey, self.creation_date)


class Recommendation(models.Model):
    patient = models.ForeignKey(User, related_name='patient_recommendations')

    date = models.DateTimeField(_(u'Fecha'), auto_now_add=True)

    content = models.CharField(_(u'Recomendación/nes'), max_length=255,
                                blank=True)


class Medicine(models.Model):
    BEFORE_AFTER_CHOICES = (
        (settings.BEFORE, _(u'Anterior')),
        (settings.AFTER, _(u'Posterior')),
    )
    patient = models.ForeignKey(User, related_name='patient_medicines')

    component = models.ForeignKey(Component,
                              related_name='component_medicines')

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
        return u'%s' % (self.component)

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


class Result(models.Model):
    patient = models.ForeignKey(User, related_name='patient_results')

    survey = models.ForeignKey(Survey, related_name="survey_results")

    answers = models.ManyToManyField('Answer',
                                    related_name="answers_results")

    task = models.ForeignKey(Task, related_name="task_results")

    date = models.DateTimeField(_(u'Fecha'), auto_now_add=True)

    def __unicode__(self):
        return u'%s %s' % (self.patient, self.date)


class Answer(models.Model):
    option = models.ForeignKey(Option, related_name="option_answers")

    text = models.CharField(_(u'Texto'), max_length=255, blank=True)

    def __unicode__(self):
        return u'%s' % self.option


class Report(models.Model):
    patient = models.ForeignKey(User, related_name='patient_reports')

    illness = models.ForeignKey(Illness, related_name='illness_reports')

    survey = models.ForeignKey(Survey, related_name="survey_reports")

    result = models.ForeignKey(Result, related_name='result_reports')

    date = models.DateTimeField(_(u'Fecha del Informe'), auto_now_add=True)

    def __unicode__(self):
        return u'%s %s' % (self.patient, self.survey, self.date)

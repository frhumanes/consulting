#!/usr/bin/python
# -*- encoding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from survey.models import Option, Survey
from medicament.models import Medicine
from django.conf import settings


class Report(models.Model):
    KIND = (
        (1, _(u'Por fedecto')),
        (2, _(u'Sucesivo')),
    )

    patient = models.ForeignKey(User, related_name='userreports')
    appointment = models.ForeignKey('Appointment',
                                    related_name='appointmentreports')

    kind = models.IntegerField(_(u'Tipo de Informe'), choices=KIND)
    name = models.CharField(max_length=255)
    observations = models.TextField(_(u'Observaciones'), blank=True)
    recommendations_treatment = models.TextField(
                                _(u'Recomendaciones/Tratamiento'), blank=True)
    date = models.DateTimeField()


class Appointment(models.Model):
    patient = models.ForeignKey(User, related_name="patientappointments")
    doctor = models.ForeignKey(User, related_name="doctorappointments")
    questionnaire = models.ForeignKey('Questionnaire',
                    related_name='questionnaireappointments', blank=True,
                    null=True)
    answers = models.ManyToManyField('Answer',
                                    related_name="answerappointments",
                                    blank=True, null=True)
    treatment = models.ForeignKey('Treatment',
                                    related_name="treatmentappointments",
                                    blank=True, null=True)

    date = models.DateField(_(u'Fecha de la Cita'))
    hour = models.TimeField(_(u'Hora de la Cita'))

    def __unicode__(self):
        return u'%s - %s' % (self.patient, self.questionnaire)


class Questionnaire(models.Model):
    survey = models.ForeignKey(Survey, related_name="questionnaires")

    self_administered = models.BooleanField()
    creation_date = models.DateTimeField()
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    from_date = models.DateTimeField(blank=True, null=True)
    to_date = models.DateTimeField(blank=True, null=True)
    rate = models.BooleanField(default=True)

    completed = models.BooleanField()

    def __unicode__(self):
        return u'%s' % self.survey


class Answer(models.Model):
    option = models.ForeignKey(Option, related_name="answers")

    text = models.CharField(_(u'Texto'), max_length=255, blank=True)

    def __unicode__(self):
        return u'%s' % self.option


#-----------------------------------------------------------------------------#
#--------------------------------- Treatment ---------------------------------#
#-----------------------------------------------------------------------------#
class Treatment(models.Model):
    patient = models.ForeignKey(User, related_name='patienttreatments')
    medications = models.ManyToManyField('Medication',
                related_name='medicationstreatments')

    from_appointment = models.BooleanField()
    date = models.DateTimeField(_(u'Fecha'))

    def __unicode__(self):
        return u'%s' % self.date


class Medication(models.Model):
    BEFORE_AFTER_CHOICES = (
        (settings.BEFORE, _(u'Anterior')),
        (settings.AFTER, _(u'Posterior')),
    )

    medicine = models.ForeignKey(Medicine, related_name='medications')
    before_after = models.IntegerField(_(u'Anterior/Posterior\
                                    síntomas psiquiátricos'),
                                    choices=BEFORE_AFTER_CHOICES)
    date = models.DateField(_(u'Fecha comienzo medicamento'),
                                blank=True, null=True)
    posology = models.CharField(_(u'Posología (mg/día)'), max_length=255)

    def __unicode__(self):
            return u'%s' % self.medicine

    def get_before_after(self):
        if self.before_after == settings.BEFORE:
            before_after = _(u'Anterior')
        else:
            before_after = _(u'Posterior')

        return before_after

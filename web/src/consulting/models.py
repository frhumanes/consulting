#!/usr/bin/python
# -*- encoding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from survey.models import Option, Survey
from medicament.models import Component
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
    #observations debe ir en appointment
    observations = models.TextField(_(u'Observaciones'), blank=True)
    #recommendations_treatment se debe dividir en recommendations de tipo
    #TextField y en components de tipo ManyToManyField(Component).Ambos
    #campos deben ir en appointment
    #La fecha de las recomendaciones es la fecha de la cita
    recommendations_treatment = models.TextField(
                                _(u'Recomendaciones/Tratamiento'), blank=True)
    date = models.DateTimeField()


class Appointment(models.Model):

    STATUS = (
        (settings.UNRESOLVED, _(u'Pendiente')),
        (settings.DONE, _(u'Realizada')),
        (settings.NOT_DONE, _(u'No Realizada')),
        (settings.MODIFIED, _(u'Modificada')),
        (settings.MODIFIED_DONE, _(u'Modificada/Realizada')),
        (settings.MODIFIED_NOT_DONE, _(u'No Realizada')),
        (settings.MODIFIED_DELETED, _(u'Modificada/Cancelada')),
        (settings.CANCELED, _(u'Cancelada'))
    )

    patient = models.ForeignKey(User, related_name="patientappointments")
    doctor = models.ForeignKey(User, related_name="doctorappointments")
    questionnaire = models.ForeignKey('Questionnaire',
                    related_name='questionnaireappointments', blank=True,
                    null=True)
    # answers debe estar en questionnaire
    answers = models.ManyToManyField('Answer',
                                    related_name="answerappointments",
                                    blank=True, null=True)
    treatment = models.ForeignKey('Treatment',
                                    related_name="treatmentappointments",
                                    blank=True, null=True)

    status = models.IntegerField(_(u'Estado'), choices=STATUS,
                                    blank=True, null=True)
    date = models.DateField(_(u'Fecha de la Cita'))
    hour = models.TimeField(_(u'Hora de la Cita'))
    # status = models.IntegerField(_(u'Estado'), choices=STATUS, blank=True,
    #                             null=True)
    # date_appointment = models.DateField(_(u'Fecha de la Cita'), blank=True,
    #                                     null=True)
    # hour_start = models.TimeField(_(u'Hora de Inicio de la Cita'),
    #                               blank=True,
    #                                 null=True)
    # hour_finish = models.TimeField(_(u'Hora de Fin de la Cita'), blank=True,
    #                                 null=True)
    # date_modified = models.DateTimeField(
    #           _(u'Fecha y hora de modificación de la Cita'), blank=True,
    #                 null=True)
    # date_cancel = models.DateTimeField(
    #                 _(u'Fecha y hora de cancelación de la Cita'), blank=True,
    #                 null=True)

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
    from_appointment = models.BooleanField()
    date = models.DateTimeField(_(u'Fecha'))

    def __unicode__(self):
        return u'%s' % self.date


class Prescription(models.Model):
    BEFORE_AFTER_CHOICES = (
        (settings.BEFORE, _(u'Anterior')),
        (settings.AFTER, _(u'Posterior')),
    )

    treatment = models.ForeignKey(Treatment,
                                    related_name='treatmentprescriptions')
    component = models.ForeignKey(Component,
                              related_name='componentprescriptions')
    before_after = models.IntegerField(_(u'Anterior/Posterior\
                                    síntomas psiquiátricos'),
                                    choices=BEFORE_AFTER_CHOICES)
    months = models.IntegerField(_(u'Número de meses de toma del fármaco'))
    posology = models.CharField(_(u'Posología (mg/día)'), max_length=255)

    def __unicode__(self):
            return u'%s' % self.treatment

    def get_before_after(self):
        if self.before_after == settings.BEFORE:
            before_after = _(u'Anterior')
        else:
            before_after = _(u'Posterior')

        return before_after

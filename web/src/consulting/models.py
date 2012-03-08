#!/usr/bin/python
# -*- encoding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from survey.models import Option, Survey
from medicament.models import Medicine


class Report(models.Model):
    KIND = (
        (1, _(u'Default')),
        (2, _(u'Successive')),
    )

    patient = models.ForeignKey(User, related_name='userreports')
    visit = models.ForeignKey('Visit', related_name='visitreports')

    kind = models.IntegerField(_(u'Kind of report'), choices=KIND)
    name = models.CharField(max_length=255)
    observations = models.TextField(_(u'Observations'), blank=True)
    date = models.DateTimeField()


class Visit(models.Model):
    patient = models.ForeignKey(User, related_name="patientvisits")
    doctor = models.ForeignKey(User, related_name="doctorvisits")
    questionnaire = models.ForeignKey('Questionnaire',
                    related_name='questionnairevisits', blank=True, null=True)
    answers = models.ManyToManyField('Answer', related_name="answervisits",
                blank=True, null=True)
    treatment = models.ForeignKey('Treatment', related_name="treatmentvisits",
                blank=True, null=True)

    date = models.DateTimeField()

    def __unicode__(self):
        return u'%s - %s' % (self.patient, self.questionnaire)


class Questionnaire(models.Model):
    survey = models.ForeignKey(Survey, related_name="questionnaires")

    self_administered = models.BooleanField()
    creation_date = models.DateTimeField()
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    deadline = models.DateTimeField()
    rate = models.BooleanField(default=True)

    completed = models.BooleanField()

    def __unicode__(self):
        return u'%s' % self.survey


class Answer(models.Model):
    option = models.ForeignKey(Option, related_name="answers")

    text = models.CharField(_(u'Text'), max_length=255, blank=True)

    def __unicode__(self):
        return u'%s' % self.option


#-----------------------------------------------------------------------------#
#--------------------------------- Treatment ---------------------------------#
#-----------------------------------------------------------------------------#
class Treatment(models.Model):
    patient = models.ForeignKey(User, related_name='patienttreatments')
    medications = models.ManyToManyField('Medication',
                    related_name='medicationstreatments')

    from_visit = models.BooleanField()
    date = models.DateTimeField(_(u'Date'))

    def __unicode__(self):
        return u'%s - %s' % (self.patient, self.date)


class Medication(models.Model):
    BEFORE_AFTER_CHOICES = (
        ('B', _(u'Before')),
        ('A', _(u'After')),
    )

    medicine = models.ForeignKey(Medicine, unique=True,
                related_name='medications')

    posology = models.CharField(_(u'Posology (mg/day)'), max_length=255)
    time = models.IntegerField(_(u'Treatment time before or after begining of \
            symptoms (months)'))
    before_after = models.CharField(_(u'Treatment BEFORE or AFTER begining of \
                    apsychiatric symptoms'),
                    max_length=9, choices=BEFORE_AFTER_CHOICES)

    def __unicode__(self):
            return u'%s' % self.medicine

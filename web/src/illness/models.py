# -*- encoding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from survey.models import Survey


class Illness(models.Model):
    surveys = models.ManyToManyField(Survey, related_name="surveys_illnesses")

    name = models.CharField(_(u'Nombre de la enfermedad'), max_length=255,
                                blank=True)

    code = models.CharField(_(u'Código'), max_length=100)

    def __unicode__(self):
        return u'%s' % self.name

# -*- encoding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _

from log.models import TraceableModel
from survey.models import Survey


class Illness(TraceableModel):
    surveys = models.ManyToManyField(Survey, related_name="surveys_illnesses")

    name = models.CharField(_(u'Nombre de la enfermedad'), max_length=255,
                                blank=True)

    code = models.IntegerField(_(u'Código'), blank=True, null=True)

    def __unicode__(self):
        return u'%s' % (self.name)

    class Meta:
        verbose_name = u"Diágnostico"
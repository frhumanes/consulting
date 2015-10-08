# -*- encoding: utf-8 -*-
from django.db import models
from formula.models import Level, Risk
from consulting.models import Task

from django.utils.translation import ugettext_lazy as _

# Create your models here.
class Recommendation(models.Model):

    level = models.OneToOneField(Level)

    tests = models.TextField(_(u'Pruebas complementarias'), blank=True)
    surveys = models.TextField(_(u'Cuestionarios específicos'), blank=True)
    tracking = models.TextField(_(u'Tipo de seguimiento y cronograma'), blank=True)
    recommendation = models.TextField(_(u'Medidas recomendadas'), blank=True)


    def __unicode__(self):
        return unicode(self.level)
    


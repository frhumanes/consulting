#!/usr/bin/python
# -*- encoding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _


class Group(models.Model):
    name = models.CharField(_(u'Nombre del grupo'), max_length=40, blank=True)
    adverse_reaction = models.CharField(_(u'Reacciones Adversas'),
                        max_length=255)

    def __unicode__(self):
        return u'%s' % (self.name)


class Medicine(models.Model):
    group = models.ForeignKey(Group, related_name='medicines')

    name = models.CharField(_(u'Nombre del medicamento'), max_length=40)
    active_ingredient = models.CharField(_(u'Principio Activo'),
                        max_length=255)

    def __unicode__(self):
                return u'%s - %s - %s' % (self.group, self.name,
                self.active_ingredient)

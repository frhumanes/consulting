# -*- encoding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


class Group(models.Model):
    name = models.CharField(_(u'Nombre del grupo'), max_length=40, blank=True)

    adverse_reaction = models.CharField(_(u'Reacciones Adversas'),
                        max_length=255)

    def __unicode__(self):
        return u'%s' % (self.name)

    class Meta:
        verbose_name = "Grupo"


class Component(models.Model):
    KIND = (
        (settings.ACTIVE_INGREDIENT, _(u'Principio Activo')),
        (settings.MEDICINE, _(u'Fármaco (nombre comercial)')),
    )

    groups = models.ManyToManyField(Group, related_name='groups_components')

    kind_component = models.IntegerField(_(u'Tipo de componente'),
                                        choices=KIND)

    name = models.CharField(_(u'Nombre'), max_length=255,
                            blank=True)

    def __unicode__(self):
        return u'%s' % (self.name)

    class Meta:
        verbose_name = u"Fármaco"

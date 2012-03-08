#!/usr/bin/python
# -*- encoding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _


class Group(models.Model):
    name = models.CharField(_(u'Name of group'), max_length=40, blank=True)
    adverse_reaction = models.CharField(_(u'Adverse_Reaction'),
                        max_length=255)

    def __unicode__(self):
        return u'%s' % (self.name)


class Medicine(models.Model):
    group = models.ForeignKey(Group, related_name='medicines')

    name = models.CharField(_(u'Name of medicine'), max_length=40)
    active_ingredient = models.CharField(_(u'Active Ingredient'),
                        max_length=255)

    def __unicode__(self):
                return u'%s - %s - %s' % (self.group, self.name,
                self.active_ingredient)

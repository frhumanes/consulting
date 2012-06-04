#!/usr/bin/python
# -*- encoding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
# from survey.models import Block


class Dimension(models.Model):
    name = models.CharField(_(u'Nombre'), max_length=40, blank=True)
    polynomial = models.TextField(_(u'Polinomio'))
    factor = models.DecimalField(u'Factor', max_digits=10, decimal_places=8)

    def __unicode__(self):
        return u'%s' % self.name


class Variable(models.Model):
    dimension = models.ForeignKey('Dimension', related_name='variables')

    name = models.CharField(_(u'Nombre'), max_length=40, blank=True)
    code = models.CharField(_(u'Código'), max_length=40, blank=True)

    def __unicode__(self):
        return u'%s' % self.name


class Formula(models.Model):
    # block = models.ForeignKey(Block, related_name='blockformulas')
    variable = models.ForeignKey('Variable', related_name='variableformulas')
    sibling = models.ForeignKey('self', blank=True, null=True,
                related_name='siblingformulas')

    polynomial = models.CharField(_(u'Polinomio'), max_length=250)
    factor = models.DecimalField(u'Factor', max_digits=12, decimal_places=10)

    def __unicode__(self):
        return u'%s' % self.variable

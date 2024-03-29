# -*- encoding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


class Dimension(models.Model):
    name = models.CharField(_(u'Nombre'), max_length=40, blank=True)

    polynomial = models.TextField(_(u'Polinomio'))

    factor = models.DecimalField(u'Factor', max_digits=10, decimal_places=8)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = u"Dimensión"
        verbose_name_plural = "Dimensiones"


class Variable(models.Model):
    dimension = models.ForeignKey('Dimension', on_delete=models.SET_NULL,
                                    related_name='dimension_variables', 
                                    null=True, blank=True)

    name = models.CharField(_(u'Nombre'), max_length=40, blank=True)

    code = models.CharField(_(u'Código'), max_length=40, blank=True)

    vmin = models.IntegerField(_(u'Valor mínimo'), default=0)
    vmax = models.IntegerField(_(u'Valor máximo'))

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = "Variable"


class Formula(models.Model):
    KIND = (
        (settings.GENERAL, _(u'General')),
        (settings.EXTENSO, _(u'Extenso')),
        (settings.ABREVIADO, _(u'Abreviado')),
    )
    variable = models.ForeignKey('Variable', related_name='variable_formulas')

    sibling = models.ForeignKey('self', blank=True, null=True,
                related_name='sibling_formulas')

    kind = models.IntegerField(_(u'Tipo'), choices=KIND)

    polynomial = models.CharField(_(u'Polinomio'), max_length=250)

    factor = models.DecimalField(u'Factor', 
                                max_digits=12, 
                                decimal_places=10, 
                                default=1)

    def __unicode__(self):
        return u'%s [%s]' % (self.variable, self.get_kind())

    def get_kind(self):
        if self.kind == settings.GENERAL:
            return 'General'
        elif self.kind == settings.EXTENSO:
            return 'Extenso'
        else:
            return 'Abreviado'

    class Meta:
        verbose_name = u"Fórmula"

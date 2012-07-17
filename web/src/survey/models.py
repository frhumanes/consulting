# -*- encoding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from formula.models import Formula


class Survey(models.Model):
    blocks = models.ManyToManyField('Block', related_name='blocks_surveys')

    name = models.CharField(_(u'Nombre'), max_length=100)

    code = models.CharField(_(u'Código'), max_length=100)

    def __unicode__(self):
        return u'%s - %s' % (self.code, self.name)


class Category(models.Model):
    name = models.CharField(_(u'Nombre'), max_length=100)

    code = models.CharField(_(u'Código'), max_length=15)

    def __unicode__(self):
        return u'%s - %s' % (self.code, self.name)


class Block(models.Model):
    KIND = (
        (0, _(u'General')),
        (1, _(u'Extenso')),
        (2, _(u'Abreviado')),
    )

    categories = models.ManyToManyField('Category',
                                        related_name='categories_blocks')
    formulas = models.ManyToManyField(Formula, related_name='formulas_blocks')

    kind = models.IntegerField(_(u'Tipo'), choices=KIND)

    name = models.CharField(_(u'Nombre'), max_length=100)

    code = models.CharField(_(u'Código'), max_length=100)

    def __unicode__(self):
        return u'%s - %d - %s' % (self.code, self.kind, self.name)


class Question(models.Model):
    #Es ManyToMany, ejemplo Pregunta B5 esta en la categoria Culpa-Abreviada y
    #en Culpa-Extensa
    categories = models.ManyToManyField('Category',
                                        related_name='categories_questions')

    text = models.CharField(_(u'Text'), max_length=500)

    code = models.CharField(_(u'Código'), max_length=10)

    def __unicode__(self):
        return u'%s - %s' % (self.code, self.text)


class Option(models.Model):
    KIND = (
        (0, _(u'Obligatorio')),
        (1, _(u'Libre')),
    )

    question = models.ForeignKey('Question', related_name="question_options")
    #REPASAR RELACION: creo que es OneToMany
    #Un hijo solo puede pertenecer a un padre. Ejemplo F9.1 su padre es solo F9
    father = models.ForeignKey('self', blank=True, null=True,
                related_name='father_options')

    kind = models.IntegerField(_(u'Tipo'), choices=KIND)

    code = models.CharField(_(u'Código'), max_length=10)

    weight = models.DecimalField(_(u'Peso'), max_digits=5, decimal_places=2,
        blank=True, null=True)

    text = models.CharField(_(u'Texto'), max_length=255)

    def __unicode__(self):
        return u'%s - %s' % (self.code, self.text)

# -*- encoding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _

from log.models import TraceableModel
from formula.models import Formula

from django.conf import settings


class Survey(TraceableModel):
    KIND = (
        (settings.GENERAL, _(u'General')),
        (settings.EXTENSO, _(u'Extenso')),
        (settings.ABREVIADO, _(u'Abreviado')),
    )
    blocks = models.ManyToManyField('Block', related_name='blocks_surveys')

    name = models.CharField(_(u'Nombre'), max_length=100)

    code = models.IntegerField(_(u'Código'), blank=True, null=True)

    kind = models.IntegerField(_(u'Tipo'), choices=KIND)

    def __unicode__(self):
        return u'id: %s survey: %s kind: %s' % (self.id, self.name, self.kind)

    def get_kind(self):
        if self.kind == settings.GENERAL:
            return 'General'
        elif self.kind == settings.EXTENSO:
            return 'Extenso'
        else:
            return 'Abreviado'


class Category(TraceableModel):
    KIND = (
        (settings.GENERAL, _(u'General')),
        (settings.EXTENSO, _(u'Extenso')),
        (settings.ABREVIADO, _(u'Abreviado')),
    )
    name = models.CharField(_(u'Nombre'), max_length=100)

    code = models.IntegerField(_(u'Código'), blank=True, null=True)

    kind = models.IntegerField(_(u'Tipo'), choices=KIND)

    def __unicode__(self):
        return u'id: %s category: %s kind: %s' % (self.id, self.name, self.kind)


class Block(TraceableModel):
    KIND = (
        (settings.GENERAL, _(u'General')),
        (settings.EXTENSO, _(u'Extenso')),
        (settings.ABREVIADO, _(u'Abreviado')),
    )

    categories = models.ManyToManyField('Category',
                                        related_name='categories_blocks')
    formulas = models.ManyToManyField(Formula, related_name='formulas_blocks')

    kind = models.IntegerField(_(u'Tipo'), choices=KIND)

    name = models.CharField(_(u'Nombre'), max_length=100)

    code = models.IntegerField(_(u'Código'), blank=True, null=True)

    def __unicode__(self):
        return u'id: %s block: %s kind: %s' % (self.id, self.name, self.kind)


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
    # father = models.ForeignKey('self', blank=True, null=True,
    #             related_name='father_options')

    kind = models.IntegerField(_(u'Tipo'), choices=KIND)

    code = models.CharField(_(u'Código'), max_length=10)

    weight = models.DecimalField(_(u'Peso'), max_digits=5, decimal_places=2,
        blank=True, null=True)

    text = models.CharField(_(u'Texto'), max_length=255)

    def __unicode__(self):
        return u'%s - %s' % (self.code, self.text)

#!/usr/bin/python
# -*- encoding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _


class Survey(models.Model):
    blocks = models.ManyToManyField('Block', related_name='surveys')

    name = models.CharField(_(u'Name'), max_length=100)
    code = models.CharField(_(u'Code'), max_length=100)

    def __unicode__(self):
        return u'%s - %s' % (self.code, self.name)


class Category(models.Model):
    name = models.CharField(_(u'Name'), max_length=100)
    code = models.CharField(_(u'Code'), max_length=15)

    def __unicode__(self):
        return u'%s - %s' % (self.code, self.name)


class Block(models.Model):
    KIND = (
        (0, _(u'General')),
        (1, _(u'Extensive')),
        (2, _(u'Abbreviated')),
    )

    categories = models.ManyToManyField('Category', related_name='blocks')

    kind = models.IntegerField(_(u'Kind'), choices=KIND)
    name = models.CharField(_(u'Name'), max_length=100)
    code = models.CharField(_(u'Code'), max_length=100)

    def __unicode__(self):
        return u'%s - %d - %s' % (self.code, self.kind, self.name)


class Question(models.Model):
    categories = models.ManyToManyField('Category', related_name='questions')

    text = models.CharField(_(u'Text'), max_length=255)
    code = models.CharField(_(u'Code'), max_length=10)

    def __unicode__(self):
        return u'%s - %s' % (self.code, self.text)


class Option(models.Model):
    KIND = (
        (1, _(u'Bounded')),
        (2, _(u'Free')),
    )

    question = models.ForeignKey('Question', related_name="options")
    children = models.ManyToManyField('self', blank=True, null=True,
                related_name='childrenoptions')

    kind = models.IntegerField(_(u'Kind'), choices=KIND)
    code = models.CharField(_(u'Code'), max_length=10)
    weight = models.DecimalField(_(u'Weight'), max_digits=5, decimal_places=2,
        blank=True, null=True)
    text = models.CharField(_(u'Text'), max_length=255)

    def __unicode__(self):
        return u'%s - %s' % (self.code, self.text)

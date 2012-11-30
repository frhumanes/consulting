# -*- encoding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.text import truncate_words

from log.models import TraceableModel
from formula.models import Variable

from django.conf import settings


class Survey(TraceableModel):
    
    blocks = models.ManyToManyField('Block', related_name='blocks_surveys', verbose_name=_(u'Bloque'))

    multitype = models.BooleanField(_(u'Encuesta configurable'), default=False, help_text=u"Necesario para seleccionar bloques Extenso o Abreviado")

    name = models.CharField(_(u'Nombre'), max_length=100)

    code = models.IntegerField(_(u'Código'), blank=True, null=True, db_index=True)


    def __unicode__(self):
        return u'%s' % (self.name)

    def num_blocks(self):
        return self.blocks.values('code').distinct().count()

    class Meta:
        verbose_name = "Cuestionario"


class Category(TraceableModel):
    KIND = (
        (settings.GENERAL, _(u'General')),
        (settings.EXTENSO, _(u'Extenso')),
        (settings.ABREVIADO, _(u'Abreviado')),
    )
    
    questions = models.ManyToManyField('Question',
                                        related_name='questions_categories', verbose_name=_(u'Preguntas'))
    name = models.CharField(_(u'Nombre'), max_length=100)

    code = models.IntegerField(_(u'Código'), blank=True, null=True, db_index=True)

    variables = models.ManyToManyField(Variable, related_name='variables_categories', verbose_name=_(u'Variables asociadas'))

    kind = models.IntegerField(_(u'Tipo'), choices=KIND)

    def __unicode__(self):
        return u'%s [%s]' % (self.name, self.get_kind())

    def get_kind(self):
        if self.kind == settings.GENERAL:
            return 'General'
        elif self.kind == settings.EXTENSO:
            return 'Extenso'
        else:
            return 'Abreviado'

    class Meta:
        verbose_name = u"Categoría"

class Block(TraceableModel):
    KIND = (
        (settings.GENERAL, _(u'General')),
        (settings.EXTENSO, _(u'Extenso')),
        (settings.ABREVIADO, _(u'Abreviado')),
    )

    categories = models.ManyToManyField('Category',
                                        related_name='categories_blocks', verbose_name=_(u'Categorías'))

    kind = models.IntegerField(_(u'Tipo'), choices=KIND)

    name = models.CharField(_(u'Nombre'), max_length=100)

    code = models.IntegerField(_(u'Código'), db_index=True)

    def __unicode__(self):
        return u'%s [%s]' % (self.name, self.get_kind())

    def get_kind(self):
        if self.kind == settings.GENERAL:
            return 'General'
        elif self.kind == settings.EXTENSO:
            return 'Extenso'
        else:
            return 'Abreviado'

    class Meta:
        verbose_name = "Bloque"

class Question(models.Model):
    KIND = (
        (settings.UNISEX, _(u'Ambos sexos')),
        (settings.MAN, _(u'Hombre')),
        (settings.WOMAN, _(u'Mujer')),
    )

    text = models.TextField(_(u'Text'), max_length=500)

    code = models.CharField(_(u'Código'), max_length=10, db_index=True, unique=True)

    single = models.BooleanField(_(u'Respuesta única'), default=False)

    kind = models.IntegerField(_(u'Sexo'), choices=KIND, default=settings.UNISEX, help_text="Pregunta disponible sólo para el sexo seleccionado")
    
    required = models.BooleanField(_(u'Respuesta requerida'), default=False)

    def __unicode__(self):
        return u'%s - %s' % (self.code, truncate_words(self.text, 20))

    def get_kind(self):
        if self.kind == settings.MAN:
            return 'Hombre'
        elif self.kind == settings.WOMAN:
            return 'Mujer'
        else:
            return 'Ambos'

    def get_af_illness(self):
        return self.text[self.text.find('padecido')+9:self.text.find(' alguno')]

    class Meta:
        ordering = ['id','code']
        verbose_name = "Pregunta"


class Option(models.Model):

    question = models.ForeignKey('Question', related_name="question_options", verbose_name=_(u'Pregunta'))

    code = models.CharField(_(u'Código'), max_length=10, db_index=True, unique=True)

    weight = models.DecimalField(_(u'Peso'), max_digits=5, decimal_places=2,
        blank=True, null=True)

    text = models.CharField(_(u'Texto'), max_length=255)

    def __unicode__(self):
        return u'%s - %s' % (self.code, self.text)

    class Meta:
        verbose_name = u"Opción"
        verbose_name_plural = "Opciones"



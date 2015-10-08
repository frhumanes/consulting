# -*- encoding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from django.core.cache import cache


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

    def get_active_condition(self, value):
        conds = self.condition_set.filter(score__gte=value).order_by('score')
        if conds.exists():
            return conds[:1].get()


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

class Scale(models.Model):

    KIND = (
        (settings.EXTENSO, _(u'Polinomio completo')),
        (settings.ABREVIADO, _(u'Polinomio abreviado')),
    )


    name = models.CharField(_(u'Nombre'), max_length=40, blank=True)

    key = models.CharField(_(u'Clave'), max_length=40, blank=True)

    kind = models.IntegerField(_(u'Tipo'), choices=KIND, default=settings.EXTENSO)

    polynomial = models.CharField(_(u'Polinomio'), max_length=250, blank=True)

    factor = models.DecimalField(u'Factor', 
                                max_digits=12, 
                                decimal_places=10, 
                                default=1)

    inverted = models.BooleanField(_(u'Escala inversa'), default=True, help_text=_(u"Menor puntuación es mejor"))

    action = models.CharField(_(u'Acción'), max_length=250, null=True, blank=True)

    class Meta:
        verbose_name = u"Escala"

    def get_level(self, score):
        try:
            return self.scale_levels.filter(score__gte=score).order_by('score')[:1].get()
        except:
            l = Level()
            l.scale = self
            return l

    def levels(self):
        if self.inverted:
            return self.scale_levels.all().order_by('-score')
        else:
            return self.scale_levels.all()

    def __unicode__(self):
        return "[%s] %s" % (self.key, self.name)

class Level(models.Model):

    scale = models.ForeignKey('Scale', blank=False, null=False,
                related_name='scale_levels')

    name = models.CharField(_(u'Nombre'), max_length=80, blank=True)

    css = models.CharField(_(u'Clase CSS'), max_length=40, blank=True, default="default")

    score = models.DecimalField(u'Punto de corte', 
                                max_digits=7, 
                                decimal_places=3)

    color = models.CharField(_(u'Color (hexadecimal o nombre)'), max_length=16, blank=True, null=True)


    class Meta:
        verbose_name = "Nivel"
        verbose_name_plural = "Niveles"
        ordering = ['scale', 'score']

    def __unicode__(self):
        return "[%s] %s" % (self.scale.name, self.name)

    def index(self):
        _index = cache.get('level_index_' + str(self.id))
        if _index:
            return _index
        try:
            if self.scale.inverted:
                _index = list(Level.objects.filter(scale=self.scale).order_by('score')).index(self)
            else:
                _index = list(Level.objects.filter(scale=self.scale).order_by('-score')).index(self)
            cache.set('level_index_' + str(self.id), _index)
        except:
            _index = 0
        return _index


class Risk(models.Model):
    name = models.CharField(_(u'Nombre'), max_length=64)
    color = models.CharField(_(u'Código color'), max_length=16, blank=True)
    criticity = models.IntegerField(_('Criticidad'), default=0)
    message = models.TextField(_(u'Mensaje'), blank=True)
    trigger = models.ManyToManyField(Variable, through='Condition')
    coincidences = models.IntegerField(_(u'Numero de mínimo de condiciones'), default=2)


    class Meta:
        ordering = ['criticity', 'id']
        verbose_name = _(u'Riesgo')
        verbose_name_plural = _(u'Riesgos')

    def __unicode__(self):
        return self.name


class Condition(models.Model):
    risk = models.ForeignKey(Risk)
    variable = models.ForeignKey(Variable)
    score = models.DecimalField(_(u'Valor'), max_digits=5, decimal_places=2, null=False)

    class Meta:
        verbose_name = _(u'Condición')
        verbose_name_plural = _(u'Condiciones')
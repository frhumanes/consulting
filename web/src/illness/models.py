# -*- encoding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _

from log.models import TraceableModel
from survey.models import Survey


class Illness(TraceableModel):
    surveys = models.ManyToManyField(Survey, related_name="surveys_illnesses")

    name = models.CharField(_(u'Nombre de la enfermedad'), max_length=255,
                                blank=True)

    code = models.CharField(_(u'Código'), max_length=10, unique=True)

    parent = models.ForeignKey('self', related_name="cie_code", null=True)

    def __unicode__(self):
        if self.parent:
            if self.code.startswith('|'):
                children = list(self.cie_code.values('code').order_by('code'))
                if len(children) >= 2:
                    return u'(%s-%s) %s' % (children[0]['code'],
                                            children[-1]['code'],
                                            self.name)
                elif len(children) == 1:
                    return u'(%s) %s' % (children[0]['code'], self.name)
                else:
                    return u'%s' % (self.name)
            else:
                return u'(%s) %s' % (self.code, self.name)
        else:
            return u'%s %s - %s' % (_(u'CAPÍTULO'), self.code, self.name)

    def serialize(self, include=[]):
        children, css = [], ''
        if self in include:
            children = [i.serialize(include) for i in self.cie_code.all().order_by('code')]
            if not self.cie_code.all().count():
                css = "jstree-checked" 
        return dict(data=self.__unicode__(), 
                    children= children,
                    state="closed" if self.cie_code.all().count() else 'leaf',
                    attr={
                           'code': self.code, 
                           'id': 'node_'+self.code,
                           'class': css,
                        'rel': "folder" if self.cie_code.all().count() else 'illness'
                    })



    class Meta:
        verbose_name = u"Diagnóstico"
        #ordering = ("code",)

# -*- encoding: utf-8 -*-
from django import forms
from django.conf import settings
from userprofile.models import Profile
from formula.models import Variable, Dimension
from survey.models import Option
from consulting.models import Medicine
from django.utils.translation import ugettext_lazy as _
from django.utils.html import strip_tags

class MultipleValueField(forms.MultiValueField):

    def draw(self):
        attrs = self.widget.attrs
        attrs['id'] = 'id_' + self.label.replace(' ','_').lower()
        return self.widget.render(self.label.replace(' ','-'), [], attrs)

class RangeWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        widgets = (forms.HiddenInput(attrs=attrs), forms.HiddenInput(attrs=attrs))
        super(RangeWidget, self).__init__(widgets, attrs)
  
    def decompress(self, value):
        if value:
            return [value.start, value.stop]
        return [None, None]
  
    def format_output(self, rendered_widgets):
        return '<div class="range">%s</div>' % u' '.join(rendered_widgets)

class DateWidget(forms.MultiWidget):
    def __init__(self, attrs=None, format=None):
        widgets = (forms.DateInput(attrs=attrs, format=format), forms.DateInput(attrs=attrs, format=format))
        super(DateWidget, self).__init__(widgets, attrs)
  
    def decompress(self, value):
        if value:
            return [value.start, value.stop]
        return [None, None]
  
    def format_output(self, rendered_widgets):
        return u' - '.join(rendered_widgets)

class FiltersForm(forms.Form):
    options = forms.MultipleChoiceField(
                    label=_(u'Opciones'),
                    choices=[('filter', u'Mostrar sólo mis pacientes'),
                             ('group', u'Agrupar pacientes repetidos*')],
                    widget=forms.CheckboxSelectMultiple(),
                    help_text=_(u'* Calcula la media de los parámetros disponibles'))

    sex = forms.MultipleChoiceField(
                    label=_(u'Sexo'),
                    choices=Profile.SEX[1:],
                    widget=forms.CheckboxSelectMultiple())

    profession = forms.MultipleChoiceField(
                    label=_(u'Profesión'),
                    choices=[(p['profession'], p['profession']) for p in Profile.objects.distinct().values('profession')],
                    widget=forms.CheckboxSelectMultiple())

    age = forms.MultiValueField(
    				label=_(u'Edad'),
    				widget=RangeWidget(attrs={'class':'span3','min':'0', 'max':'100'}))
    variables = []
    for v in Variable.objects.all():
    	#vars()['group_'+v.code] = forms.MultiValueField(
    	#			label=_(v.name),
    	#			widget=RangeWidget(attrs={'class':'span3','min':'0', 'max':'5'}))
        variables.append(MultipleValueField(
                    label='variables.'+v.name,
                    widget=RangeWidget(attrs={'class':'span3',
                                              'min':'0', 
                                              'max':'5'})))

    dimensions = []
    for d in Dimension.objects.all():
        dimensions.append(MultipleValueField(
                    label='dimensions.'+d.name,
                    widget=RangeWidget(attrs={'class':'span3','min':'0', 'max':'10'})))

    treatment = [MultipleValueField(
                    label='variables.Adherencia',
                    widget=RangeWidget(attrs={'class':'span3',
                                              'min':'0', 
                                              'max':'4'}))]
    for c in  Medicine.objects.values('component__name').order_by('component__name').distinct('component'):
        treatment.append(MultipleValueField(
                    label='treatment.'+c['component__name'],
                    widget=RangeWidget(attrs={'class':'span3',
                                              'min':'0', 
                                              'max':'1000'})))

    anxiety = forms.MultipleChoiceField(
                    label=_(u'Nivel de Ansiedad'),
                    choices=[(c, strip_tags(settings.HAMILTON[v][0])) for c, v in enumerate(sorted(settings.HAMILTON))],
                    widget=forms.CheckboxSelectMultiple())

    depression = forms.MultipleChoiceField(
                    label=_(u'Nivel de Depresión'),
                    choices=[(c, strip_tags(settings.BECK[v][0])) for c, v in enumerate(sorted(settings.BECK))],
                    widget=forms.CheckboxSelectMultiple())

    aves = forms.MultipleChoiceField(
                    label=_(u'Acontecimientos Vitales Estresantes'),
                    choices=[(op.id, op.text) for op in Option.objects.filter(code__startswith='AVE')],
                    widget=forms.CheckboxSelectMultiple())

    date = forms.MultiValueField(
                    label=_(u'Fechas'),
                    widget=DateWidget(attrs={'class':'span5'},
                                           format=settings.DATE_FORMAT))

    


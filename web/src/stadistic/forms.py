# -*- encoding: utf-8 -*-
from django import forms
from django.conf import settings
from userprofile.models import Profile
from formula.models import Variable, Dimension
from survey.models import Option
from django.utils.translation import ugettext_lazy as _

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

    anxiety = forms.MultipleChoiceField(
                    label=_(u'Nivel de Ansiedad'),
                    choices=[(c, settings.HAMILTON[v][0]) for c, v in enumerate(sorted(settings.HAMILTON))],
                    widget=forms.CheckboxSelectMultiple())

    depression = forms.MultipleChoiceField(
                    label=_(u'Nivel de Depresión'),
                    choices=[(c, settings.BECK[v][0]) for c, v in enumerate(sorted(settings.BECK))],
                    widget=forms.CheckboxSelectMultiple())

    ave = forms.MultipleChoiceField(
                    label=_(u'Acontecimientos Vitales Estresantes'),
                    choices=[(op.id, op.text) for op in Option.objects.filter(code__startswith='AVE')],
                    widget=forms.CheckboxSelectMultiple())

    date = forms.MultiValueField(
                    label=_(u'Fechas'),
                    #input_formats=(settings.DATE_FORMAT,),
                    widget=DateWidget(attrs={'class':'span5'},
                                           format=settings.DATE_FORMAT))
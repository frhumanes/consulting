# -*- encoding: utf-8 -*-
from django import forms
from django.conf import settings
from userprofile.models import Profile
from formula.models import Variable, Dimension
from survey.models import Option
from consulting.models import Medicine
from illness.models import Illness
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
                             ('ungroup', u'Separar por episodios*')],
                    widget=forms.CheckboxSelectMultiple(),
                    help_text=_(u'* Segrega distintos episodios de un mismo paciente'))

    sex = forms.MultipleChoiceField(
                    label=_(u'Sexo'),
                    choices=Profile.SEX,
                    widget=forms.CheckboxSelectMultiple())

    marital = forms.MultipleChoiceField(
                    label=_(u'Estado civil'),
                    choices=Profile.STATUS,
                    widget=forms.CheckboxSelectMultiple())

    education = forms.MultipleChoiceField(
                    label=_(u'Nivel de estudios'),
                    choices=Profile.EDUCATION,
                    widget=forms.CheckboxSelectMultiple())

    profession = forms.MultipleChoiceField(
                    label=_(u'Profesión'),
                    choices=[(p['profession'], p['profession']) for p in Profile.objects.exclude(profession='').values('profession').order_by('profession').distinct()],
                    widget=forms.CheckboxSelectMultiple())

    age = forms.MultiValueField(
    				label=_(u'Edad'),
    				widget=RangeWidget(attrs={'class':'span3','min':'0', 'max':'100'}))

    illnesses =forms.MultipleChoiceField(
                    label='Diagnóstico',
                    choices=[(i['code'], '('+i['code']+') '+i['name']) for i in Illness.objects.filter(illnesses_profiles__isnull=False).values('code', 'name').order_by('code').distinct('illnesses')],
                    widget=forms.CheckboxSelectMultiple())

    date = forms.MultiValueField(
                    label=_(u'Fechas'),
                    widget=DateWidget(attrs={'class':'span5'},
                                           format=settings.DATE_INPUT_FORMAT))

    anxiety = forms.MultipleChoiceField(
                    label=_(u'Nivel de Ansiedad'),
                    choices=[(c, strip_tags(settings.HAMILTON[v][0])) for c, v in enumerate(sorted(settings.HAMILTON))],
                    widget=forms.CheckboxSelectMultiple())

    depression = forms.MultipleChoiceField(
                    label=_(u'Nivel de Depresión'),
                    choices=[(c, strip_tags(settings.BECK[v][0])) for c, v in enumerate(sorted(settings.BECK))],
                    widget=forms.CheckboxSelectMultiple())

    unhope = forms.MultipleChoiceField(
                    label=_(u'Nivel de Desesperanza'),
                    choices=[(c, strip_tags(settings.UNHOPE[v][0])) for c, v in enumerate(sorted(settings.UNHOPE))],
                    widget=forms.CheckboxSelectMultiple())
    
    suicide = forms.MultipleChoiceField(
                    label=_(u'Nivel de Riesgo'),
                    choices=[(c, strip_tags(settings.SUICIDE[v][0])) for c, v in enumerate(sorted(settings.SUICIDE))],
                    widget=forms.CheckboxSelectMultiple())

    ybocs = forms.MultipleChoiceField(
                    label=_(u'Nivel de Obsesión-compulsión'),
                    choices=[(c, strip_tags(settings.Y_BOCS[v][0])) for c, v in enumerate(sorted(settings.Y_BOCS))],
                    widget=forms.CheckboxSelectMultiple())

    aves = forms.MultipleChoiceField(
                    label=_(u'Acontecimientos Vitales Estresantes'),
                    choices=[(op.id, op.text) for op in Option.objects.filter(code__startswith='AVE', option_answers__isnull=False).distinct().order_by('text')],
                    widget=forms.CheckboxSelectMultiple())

    treatment =forms.MultipleChoiceField(
                    label='Tratamiento',
                    choices=[(m['component__name'], m['component__name']) for m in Medicine.objects.filter(is_previous=False).values('component__name').order_by('component__name').distinct('component')],
                    widget=forms.CheckboxSelectMultiple())

    def __init__(self, *args, **kwargs):
        block = None
        if 'block' in kwargs:
            block = kwargs.pop('block')
        super(forms.Form, self).__init__(*args, **kwargs)
        if block:
            self.variables = []
            for v in Variable.objects.filter(variables_categories__categories_blocks=block).distinct():
                #vars()['group_'+v.code] = forms.MultiValueField(
                #           label=_(v.name),
                #           widget=RangeWidget(attrs={'class':'span3','min':'0', 'max':'5'}))
                self.variables.append(MultipleValueField(
                            label='variables.'+v.name,
                            widget=RangeWidget(attrs={'class':'span3',
                                                      'min':v.vmin, 
                                                      'max':v.vmax})))

            self.dimensions = []
            for d in Dimension.objects.exclude(name=''):
                self.dimensions.append(MultipleValueField(
                            label='dimensions.'+d.name,
                            widget=RangeWidget(attrs={'class':'span3','min':'0', 'max':'10'})))


    


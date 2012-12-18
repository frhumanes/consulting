# -*- encoding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.utils.safestring import mark_safe
from django.forms.widgets import RadioFieldRenderer
from django.forms.util import flatatt
from django.utils.encoding import force_unicode
from django.shortcuts import get_object_or_404

from consulting.validators import validate_choice

from consulting.models import Medicine, Conclusion
from medicament.models import Component
from survey.models import Question
import copy


class AdminRadioFieldRenderer(RadioFieldRenderer):
    def render(self):
        """Outputs a <ul> for this set of radio fields."""
        return mark_safe(u'<ul%s>\n%s\n</ul>' % (
            flatatt(self.attrs),
            u'\n'.join([u'<li class="radio_js" >%s</li>' \
            % force_unicode(w) for w in self]))
        )

class TreatmentForm(forms.ModelForm):
    KIND = (
        (settings.ACTIVE_INGREDIENT, _(u'Principio Activo')),
        (settings.MEDICINE, _(u'Fármaco(nombre comercial)')),
    )

    kind_component = forms.ChoiceField(label=_(u'Tipo de componente'),
        choices=KIND,
        widget=forms.RadioSelect(renderer=AdminRadioFieldRenderer))
    searcher_component = forms.CharField(label=_(u'Componente'),
                                        max_length=150)
    component = forms.ModelChoiceField(
                                    queryset=Component.objects.all(),
                                    widget=forms.HiddenInput, initial='-1')
    posology = forms.IntegerField(label=_(u'Posología (mg/día)'))

    dosification = forms.CharField(label=_(u'Modo de administración'),
                                    max_length=255, required=False)

    class Meta:
        model = Medicine
        exclude = ('patient', 'date', 'created_at', 'updated_at', 'months', 'after_symptoms')

class MedicineForm(forms.ModelForm):
    KIND = (
        (settings.ACTIVE_INGREDIENT, _(u'Principio Activo')),
        (settings.MEDICINE, _(u'Fármaco(nombre comercial)')),
    )
    BEFORE_AFTER_CHOICES = (
        ('', _(u'Seleccionar')),
        (0, _(u'Anterior')),
        (1, _(u'Posterior')),
    )

    kind_component = forms.ChoiceField(label=_(u'Tipo de componente'),
        choices=KIND,
        widget=forms.RadioSelect(renderer=AdminRadioFieldRenderer))
    searcher_component = forms.CharField(label=_(u'Componente'),
                                        max_length=150)
    component = forms.ModelChoiceField(
                                    queryset=Component.objects.all(),
                                    widget=forms.HiddenInput, initial='-1')
    after_symptoms = forms.ChoiceField(
                                    label=_(u'Anterior/Posterior\
                                    a los síntomas'),
                                    choices=BEFORE_AFTER_CHOICES,
                                    validators=[validate_choice])
    months = forms.DecimalField(label=_(u'Número de meses de toma del\
                                         fármaco'))
    posology = forms.IntegerField(label=_(u'Posología (mg/día)'))

    class Meta:
        model = Medicine
        exclude = ('patient', 'appointment', 'is_previous', 'date', 'created_at', 'updated_at', 'dosification')


class ConclusionForm(forms.ModelForm):
    observation = forms.CharField(label=_(u'Observaciones'),
                                    widget=forms.Textarea(attrs={'cols': 60,
                                                'rows': 4, 'class': 'span12'}), required=False)
    recommendation = forms.CharField(label=_(u'Recomendaciones'),
                                    widget=forms.Textarea(attrs={'cols': 60,
                                                'rows': 4, 'class': 'span12'}),
                                    required=False)

    class Meta:
        model = Conclusion
        exclude = ('created_at', 'updated_at', 'patient', 'result',
                    'appointment', 'date', 'appointment', 'created_by')

    def clean(self):
        cleaned_data = self.cleaned_data
        observation = cleaned_data.get("observation")
        recommendation = cleaned_data.get("recommendation")

        if not observation and not recommendation:
            msg = _(u"Debe rellenar al menos uno de los dos campos")
            self._errors['__all__'] = self.error_class([msg])
        return cleaned_data


class ActionSelectionForm(forms.Form):
    ACTION = (
        ('', _(u'--------')),
        (settings.PREVIOUS_STUDY, _(u'Estudio Previo')),
    )

    survey = forms.ChoiceField(label=_(u'Realizar'), choices=ACTION,
        widget=forms.Select(
                        attrs={'class': 'input-medium search-query span12'}))

    def __init__(self, *args, **kwargs):
        if 'variables' in kwargs:
            variables = kwargs.pop('variables')
        super(ActionSelectionForm, self).__init__(*args, **kwargs)


class SelectOtherTaskForm(forms.Form):
    survey = forms.ChoiceField(label=_(u'Encuesta'),
            widget=forms.Select(
                        attrs={'class': 'input-medium search-query span12'}))
    NEXT_SURVEY = [('', _(u'--------'))]

    def __init__(self, *args, **kwargs):
        choices = copy.copy(self.NEXT_SURVEY)
        if 'variables' in kwargs:
            variables = kwargs.pop('variables')
            super(SelectOtherTaskForm, self).__init__(*args, **kwargs)

            choices.append(
                    (settings.ANXIETY_DEPRESSION_SURVEY,
                    _(u'Valoración de la depresión y la ansiedad'))
                    )
            self.fields['variables'] = forms.MultipleChoiceField(
                    label=_(u'Variables'),
                    widget=forms.CheckboxSelectMultiple(),
                    choices=variables,
                    initial=[x[0] for x in variables],
                    required=False)
            if variables:
                choices.append(
                    (settings.CUSTOM, _(u'Variables más puntuadas')))
        else:
            super(SelectOtherTaskForm, self).__init__(*args, **kwargs)
            choices.append(
                    (settings.INITIAL_ASSESSMENT, 
                    _(u'Valoración Inicial'))
                    )
        self.fields['survey'].choices = choices
        self.fields['kind'] = forms.ChoiceField(
                    label=_(u'Tipo'),
                    widget=forms.Select(),
                    choices=((settings.ABREVIADO, u'Abreviado'),
                             (settings.EXTENSO, u'Extendido')),
                    required=True)

    def clean(self):
        cleaned_data = self.cleaned_data
        survey = cleaned_data.get("survey")
        

        if survey == str(settings.CUSTOM):
            if not cleaned_data.get("variables"):
                msg = _(u"Este campo es obligatorio")
                self._errors['variables'] = self.error_class([msg])

        return cleaned_data

class SelectTaskForm(SelectOtherTaskForm):
    previous_days = forms.CharField(
            label=_(u'Visible'),
            widget=forms.TextInput(),
            required=True)

class SelectVirtualTaskForm(SelectTaskForm):
    def __init__(self, *args, **kwargs):
        super(SelectTaskForm, self).__init__(*args, **kwargs)
        self.fields['survey'].choices = ((settings.VIRTUAL_SURVEY, _(u'Seguimiento virtual')),)
        del self.fields['kind']


class SelectNotAssessedVariablesForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'variables' in kwargs:
            variables = kwargs.pop('variables')
            super(SelectNotAssessedVariablesForm, self)\
                                                    .__init__(*args, **kwargs)

            self.fields['variables'] = forms.MultipleChoiceField(
                    label=_(u'Variables'),
                    widget=forms.CheckboxSelectMultiple(attrs={'class':'span4'}),
                    choices=variables,
                    required=True)
        else:
            super(SelectNotAssessedVariablesForm, self)\
                                                    .__init__(*args, **kwargs)


class SymptomsWorseningForm(forms.Form):

    symptoms_worsening = forms.CharField(widget=forms.Textarea(
                                attrs={'cols': 60, 'rows': 4, 'class': 'span12'}))

    def __init__(self, *args, **kwargs):
        OPTION = (
                (0, _(u'No')),
                (1, _(u'Sí')),
            )

        super(SymptomsWorseningForm, self).__init__(*args, **kwargs)
        self.fields['question'] = forms.ChoiceField(choices=OPTION,
                                                    widget=forms.Select(
                                                    attrs={'class': 'input-medium search-query span3', 'id':'question'}))
        question = Question.objects.get(code=settings.CODE_SYMPTOMS_WORSENING)
        if question:
            self.fields['symptoms_worsening'].label = question.text

class ParametersFilterForm(forms.Form):

    from_date = forms.DateField(input_formats=(settings.DATE_FORMAT,),
        widget=forms.DateInput(attrs={'class':'span6'},format=settings.DATE_FORMAT),required=False)

    to_date = forms.DateField(input_formats=(settings.DATE_FORMAT,),
        widget=forms.DateInput(attrs={'class':'span6'},format=settings.DATE_FORMAT),required=False)
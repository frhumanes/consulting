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
from survey.models import Question, Survey
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
    posology = forms.DecimalField(label=_(u'Posología (mg/día)'))

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
    posology = forms.DecimalField(label=_(u'Posología (mg/día)'))

    class Meta:
        model = Medicine
        exclude = ('patient', 'appointment', 'is_previous', 'date', 'created_at', 'updated_at', 'dosification')

class SelfRegisterForm(forms.Form):
    table = forms.CharField(label=_(u'registro'), widget=forms.HiddenInput(),
        help_text=_(u'Rellene los campos de la tabla. La primera fila se considerará la cabecera de la misma y no podrá ser editada por el paciente.'))

class ConclusionForm(forms.ModelForm):
    observation = forms.CharField(label=_(u'Observaciones'),
                                    widget=forms.Textarea(attrs={'cols': 60,
                                                'rows': 4, 'class': 'span12'}), required=False)
    recommendation = forms.CharField(label=_(u'Recomendaciones y consejos para el paciente'),
                                    widget=forms.Textarea(attrs={'cols': 60,
                                                'rows': 4, 'class': 'span12'}),
                                    required=False)

    extra = forms.FileField(label=_(u'Adjuntar archivo para paciente'),
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


class SelectSurveyForm(forms.Form):
    survey = forms.ChoiceField(label=_(u'Realizar cuestionario'), choices=[],
            widget=forms.Select(attrs={'class': 'input-medium search-query span12'}))
    table = forms.CharField(label=_(u'Plantilla'), widget=forms.HiddenInput(),
        help_text=_(u'Rellene los campos de la tabla o cargue una plantilla ya existente. La primera fila se considerará la cabecera de la misma y no podrá ser editada por el paciente.'), required=False)

    def __init__(self, *args, **kwargs):
        survey_choices = []
        self.variables = None
        if 'variables' in kwargs:
            self.variables = kwargs.pop('variables')
        if 'illness' in kwargs:
            illness = kwargs.pop('illness')
            survey_choices = list(Survey.objects.filter(surveys_illnesses=illness, enabled=True).values_list('id','name'))
        super(SelectSurveyForm, self).__init__(*args, **kwargs)

        if self.variables:
            self.fields['variables'] = forms.MultipleChoiceField(
                    label=_(u'Variables'),
                    widget=forms.CheckboxSelectMultiple(),
                    choices=self.variables,
                    initial=[x[0] for x in self.variables],
                    required=False)
            survey_choices.append(
                    (settings.CUSTOM, _(u'Variables más puntuadas')))

        self.fields['survey'].choices = survey_choices
        self.fields['kind'] = forms.ChoiceField(
                    label=_(u'Tipo'),
                    widget=forms.Select(),
                    choices=((settings.GENERAL, "-------"),
                             (settings.ABREVIADO,  _(u'Abreviado')),
                             (settings.EXTENSO,  _(u'Extendido'))),
                    required=True)

    def clean(self):
        cleaned_data = super(SelectSurveyForm, self).clean()
        survey = cleaned_data.get("survey")
        kind = cleaned_data.get("kind")

        if survey == str(settings.CUSTOM):
            if not cleaned_data.get("variables"):
                msg = _(u"Este campo es obligatorio")
                self._errors['variables'] = self.error_class([msg])

        if survey == str(settings.CUSTOM):
            survey = settings.ANXIETY_DEPRESSION_SURVEY
        selected_survey = get_object_or_404(Survey, code=str(survey))
        kinds = selected_survey.get_available_kinds()
        if len(kinds) == 1:
            cleaned_data['kind'] = kinds[0]
        elif not long(kind) in kinds:
            msg = _(u"Este campo es obligatorio")
            self._errors['kind'] = self.error_class([msg])



        return cleaned_data


class SelectSurveyTaskForm(SelectSurveyForm):
    previous_days = forms.IntegerField(
            label=_(u'Visible'),
            widget=forms.TextInput(attrs={'class': 'span3'}),
            required=False, min_value=0, max_value=365)

    from_date = forms.DateField(label = _(u'Desde'), input_formats=(settings.DATE_INPUT_FORMAT,),
        widget=forms.DateInput(attrs={'class':'span6'},format=settings.DATE_INPUT_FORMAT),required=False)

    to_date = forms.DateField(input_formats=(settings.DATE_INPUT_FORMAT,),
        label = _(u'hasta'),
        widget=forms.DateInput(attrs={'class':'span6'},format=settings.DATE_INPUT_FORMAT),required=False)  

    repeat = forms.IntegerField(
            label=_(u'Repetir cada'),
            widget=forms.TextInput(attrs={'class': 'span3'}),
            required=False, min_value=0, max_value=56)

    def __init__(self, *args, **kwargs):
        survey_choices = []
        if 'illness' in kwargs:
            illness = kwargs.pop('illness')
            survey_choices = list(Survey.objects.filter(surveys_illnesses=illness, multitype=True, enabled=True).values_list('id','name'))
        else:
            survey_choices = list(Survey.objects.filter(multitype=True, enabled=True).values_list('id','name'))
        super(SelectSurveyTaskForm, self).__init__(*args, **kwargs)
        if self.variables:
            survey_choices.append((settings.CUSTOM, _(u'Variables más puntuadas')))
        self.fields['survey'].choices = survey_choices
        self.fields['survey'].label = _(u'Asignar cuestionario')

    def clean(self):
        cleaned_data = super(SelectSurveyForm, self).clean()
        pd = cleaned_data.get("previous_days")
        from_date = cleaned_data.get("from_date")
        to_date = cleaned_data.get("to_date")
        
        if pd is None and from_date is None:
             raise forms.ValidationError(_(u"Algun tipo de programación es requerida."))
        else:
            if from_date and to_date and to_date < from_date:
                 raise forms.ValidationError(_(u"La fecha de cierre no puede ser anterior a la de apertura"))       


        return cleaned_data


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

    from_date = forms.DateField(input_formats=(settings.DATE_INPUT_FORMAT,),
        widget=forms.DateInput(attrs={'class':'span6'},format=settings.DATE_INPUT_FORMAT),required=False)

    to_date = forms.DateField(input_formats=(settings.DATE_INPUT_FORMAT,),
        widget=forms.DateInput(attrs={'class':'span6'},format=settings.DATE_INPUT_FORMAT),required=False)
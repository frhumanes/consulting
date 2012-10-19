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



# class RecipientChoiceField(forms.ModelChoiceField):
#     def label_from_instance(self, obj):
#         return "%s %s" % (obj.first_name, obj.last_name)


# class AppointmentForm(forms.ModelForm):
#     format = _(u'%d/%m/%Y')
#     input_formats = [format]

#     date = forms.DateField(label=_(u'Fecha'), widget=DateInput(
#             attrs={'class': 'span2', 'size': '16'}))
#     hour = forms.TimeField(label=_(u'Hora'),
#                                 widget=forms.TextInput(
#                                 attrs={'class': 'input-mini'}))
#     # date_appointment = forms.DateField(label=_(u'Fecha'),
#     #                                 input_formats=('%d/%m/%Y',),
#     #                                 widget=DateInput(
#     #                                 attrs={'class': 'span2', 'size': '16'},
#     #                                 format='%d/%m/%Y'))
#     # hour_start = forms.TimeField(label=_(u'Hora de Inicio de la cita'),
#     #                             widget=forms.TextInput(
#     #                             attrs={'class': 'input-mini'}))
#     # hour_finish = forms.TimeField(label=_(u'Hora de Fin de la Cita'),
#     #                             widget=forms.TextInput(
#     #                             attrs={'class': 'input-mini'}))

#     def __init__(self, *args, **kwargs):
#         if 'readonly_doctor' in kwargs and 'doctor_user' in kwargs:
#             readonly_doctor = kwargs.pop('readonly_doctor')
#             doctor_user = kwargs.pop('doctor_user')
#             super(AppointmentForm, self).__init__(*args, **kwargs)

#             profiles_doctor = Profile.objects.filter(role=settings.DOCTOR)
#             ids_doctor = [profile.user.id for profile in profiles_doctor]
#             queryset = User.objects.filter(pk__in=ids_doctor)

#             self.fields['doctor'] = RecipientChoiceField(
#                                                 label=_(u"Médico"),
#                                                 queryset=queryset,
#                                                 validators=[validate_choice])
#             if readonly_doctor and not doctor_user is None:
#                 self.fields.pop('doctor')

#         else:
#             super(AppointmentForm, self).__init__(*args, **kwargs)

#     doctor = RecipientChoiceField(label=_(u'Médico'),
#                                     queryset=User.objects.none(),
#                                     validators=[validate_choice])

#     class Meta:
#         model = Appointment
#         exclude = ('patient', 'questionnaire', 'answers', 'medicine')
#         # exclude = ('patient', 'questionnaire', 'answers', 'medicine',
#         #             'status', 'date_modified', 'date_cancel')


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
    months = forms.IntegerField(label=_(u'Número de meses de toma del\
                                         fármaco'))
    posology = forms.IntegerField(label=_(u'Posología (mg/día)'))

    class Meta:
        model = Medicine
        exclude = ('patient', 'appointment', 'is_previous', 'date', 'created_at', 'updated_at')


class ConclusionForm(forms.ModelForm):
    observation = forms.CharField(label=_(u'Observaciones'),
                                    widget=forms.Textarea(attrs={'cols': 60,
                                                'rows': 4, 'class': 'span12'}))
    recommendation = forms.CharField(label=_(u'Recomendaciones'),
                                    widget=forms.Textarea(attrs={'cols': 60,
                                                'rows': 4, 'class': 'span12'}),
                                    required=False)

    class Meta:
        model = Conclusion
        exclude = ('created_at', 'updated_at', 'patient', 'result',
                    'appointment', 'date', 'appointment')


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

    def __init__(self, *args, **kwargs):
        if 'variables' in kwargs:
            variables = kwargs.pop('variables')
            super(SelectOtherTaskForm, self).__init__(*args, **kwargs)

            self.fields['variables'] = forms.MultipleChoiceField(
                    label=_(u'Variables'),
                    widget=forms.CheckboxSelectMultiple(),
                    choices=variables,
                    initial=[x[0] for x in variables],
                    required=False)
            NEXT_SURVEY = (
                ('', _(u'--------')),
                (settings.INITIAL_ASSESSMENT,
                    _(u'Valoración Inicial')),
                (settings.ANXIETY_DEPRESSION_SURVEY,
                    _(u'Valoración de la depresión y la ansiedad')),
                (settings.CUSTOM, _(u'Variables más puntuadas')),
            )

            
            if not variables:
                NEXT_SURVEY = NEXT_SURVEY[:-1]
            self.fields['survey'].choices = NEXT_SURVEY
        else:
            super(SelectOtherTaskForm, self).__init__(*args, **kwargs)
        self.fields['kind'] = forms.ChoiceField(
                    label=_(u'Tipo'),
                    widget=forms.Select(),
                    choices=((settings.ABREVIADO, u'Abreviado'),
                             (settings.EXTENSO, u'Extendido')),
                    required=True)

    def clean(self):
        cleaned_data = self.cleaned_data
        survey = cleaned_data.get("survey")
        variables = cleaned_data.get("variables")

        if survey == str(settings.CUSTOM) and not variables:
            msg = _(u"Este campo es obligatorio")
            self._errors['variables'] = self.error_class([msg])

        return cleaned_data

class SelectTaskForm(SelectOtherTaskForm):
    previous_days = forms.CharField(
            label=_(u'Visible'),
            widget=forms.TextInput(),
            required=True)
    NEXT_SURVEY = (
                ('', _(u'--------')),
                (settings.ANXIETY_DEPRESSION_SURVEY,
                    _(u'Valoración de la depresión y la ansiedad')),
                (settings.CUSTOM, _(u'Variables más puntuadas')),
            )

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
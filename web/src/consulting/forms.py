# -*- encoding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.utils.safestring import mark_safe
from django.forms.widgets import RadioFieldRenderer
from django.forms.util import flatatt
from django.utils.encoding import force_unicode

from consulting.validators import validate_choice

from consulting.models import Medicine, Conclusion, Task
from medicament.models import Component
from survey.models import Survey


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


class MedicineForm(forms.ModelForm):
    KIND = (
        (settings.ACTIVE_INGREDIENT, _(u'Principio Activo')),
        (settings.MEDICINE, _(u'Fármaco(nombre comercial)')),
    )
    BEFORE_AFTER_CHOICES = (
        (-1, _(u'Seleccionar')),
        (settings.BEFORE, _(u'Anterior')),
        (settings.AFTER, _(u'Posterior')),
    )

    kind_component = forms.ChoiceField(label=_(u'Tipo de componente'),
        choices=KIND,
        widget=forms.RadioSelect(renderer=AdminRadioFieldRenderer))
    searcher_component = forms.CharField(label=_(u'Componente'),
                                        max_length=150)
    component = forms.ModelChoiceField(
                                    queryset=Component.objects.all(),
                                    widget=forms.HiddenInput, initial='-1')
    before_after_first_appointment = forms.ChoiceField(
                                    label=_(u'Anterior/Posterior\
                                    Primera Cita'),
                                    choices=BEFORE_AFTER_CHOICES,
                                    validators=[validate_choice])
    before_after_symptom = forms.ChoiceField(
                                    label=_(u'Anterior/Posterior\
                                    síntomas psiquiátricos'),
                                    choices=BEFORE_AFTER_CHOICES,
                                    validators=[validate_choice])
    months = forms.IntegerField(label=_(u'Número de meses de toma del\
                                         fármaco'))
    posology = forms.IntegerField(label=_(u'Posología (mg/día)'))

    class Meta:
        model = Medicine
        exclude = ('patient', 'result', 'date', 'created_at', 'updated_at')


class ConclusionForm(forms.ModelForm):
    observation = forms.CharField(label=_(u'Observaciones'),
                                    widget=forms.Textarea(attrs={'cols': 60,
                                                'rows': 4, 'class': 'span5'}))
    recommendation = forms.CharField(label=_(u'Recomendaciones'),
                                    widget=forms.Textarea(attrs={'cols': 60,
                                                'rows': 4, 'class': 'span5'}),
                                    required=False)

    class Meta:
        model = Conclusion
        exclude = ('created_at', 'updated_at', 'patient', 'result',
                    'appointment', 'date')


class ActionSelectionForm(forms.Form):
    ACTION = (
        ('', _(u'--------')),
        (settings.CONCLUSION, _(u'Resumen')),
        (settings.PREVIOUS_STUDY, _(u'Estudio Previo')),
    )

    action = forms.ChoiceField(label=_(u'Realizar'), choices=ACTION,
        widget=forms.Select(
                        attrs={'class': 'input-medium search-query span4'}))


class SelectTaskForm(forms.ModelForm):
    survey = forms.ModelChoiceField(label=_(u"Encuesta"),
                        queryset=Survey.objects.filter(
                        code__in=[settings.ANXIETY_DEPRESSION_EXTENSIVE,
                        settings.ANXIETY_DEPRESSION_SHORT]),
                        widget=forms.Select(
                        attrs={'class': 'input-medium search-query span4'}))
    from_date = forms.DateField(
            label=_(u'Fecha a partir de la cual puede realizar la encuesta'),
            input_formats=(settings.DATE_FORMAT,),
            widget=forms.DateInput(format=settings.DATE_FORMAT,
                                    attrs={'class': 'span3', 'size': '16'}))
    to_date = forms.DateField(
            label=_(u'Fecha hasta la cual puede realizar la encuesta'),
            input_formats=(settings.DATE_FORMAT,),
            widget=forms.DateInput(format=settings.DATE_FORMAT,
                                    attrs={'class': 'span3', 'size': '16'}))

    class Meta:
        model = Task
        exclude = ('created_at', 'updated_at', 'patient', 'treated_blocks',
                    'appointment', 'self_administered', 'start_date',
                    'end_date', 'value', 'completed')

    def clean(self):
        cleaned_data = self.cleaned_data
        from_date = cleaned_data.get("from_date")
        to_date = cleaned_data.get("to_date")

        if from_date is None:
            msg = _(u"Este campo es obligatorio")
            self._errors["from_date"] = self.error_class([msg])

        if to_date is None:
            msg = _(u"Este campo es obligatorio")
            self._errors["to_date"] = self.error_class([msg])

        if from_date and to_date:
            if to_date < from_date:
                msg = _("La fecha hasta debe ser mayor que la fecha desde.")
                self._errors['to_date'] = self.error_class([msg])

        return cleaned_data

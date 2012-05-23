# -*- encoding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.forms.widgets import DateInput
from django.conf import settings
from userprofile.models import Profile
from consulting.validators import validate_choice
from consulting.models import Appointment, Medication
from medicament.models import Medicine


class RecipientChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s %s" % (obj.first_name, obj.last_name)


class AppointmentForm(forms.ModelForm):
    format = _(u'%d/%m/%Y')
    input_formats = [format]

    #PATIENT
    profiles_patient = Profile.objects.filter(role=settings.PATIENT)
    id_patient_users = [profile.user.id for profile in profiles_patient]
    queryset = User.objects.filter(pk__in=id_patient_users)
    patient = forms.ModelChoiceField(queryset=queryset,
                                    widget=forms.HiddenInput)

    #DOCTOR
    profiles_doctor = Profile.objects.filter(role=settings.DOCTOR)
    id_doctor_users = [profile.user.id for profile in profiles_doctor]
    queryset = User.objects.filter(pk__in=id_doctor_users)
    doctor = RecipientChoiceField(queryset=queryset,
                                    validators=[validate_choice])

    date = forms.DateField(widget=DateInput(
            attrs={'class': 'span2', 'size': '16'}))
    hour = forms.TimeField(widget=forms.TextInput(
                            attrs={'class': 'input-mini'}))

    class Meta:
        model = Appointment
        exclude = ('questionnaire', 'answers', 'treatment')


class MedicationForm(forms.ModelForm):
    BEFORE_AFTER_CHOICES = (
        (-1, _(u'Seleccionar')),
        (settings.BEFORE, _(u'Anterior')),
        (settings.AFTER, _(u'Posterior')),
    )
    searcher_medicine = forms.CharField(label=_(u'Fármaco'), max_length=150)
    medicine = forms.ModelChoiceField(queryset=Medicine.objects.all(),
                                    widget=forms.HiddenInput, initial='-1')
    before_after = forms.ChoiceField(label=_(u'Anterior/Posterior\
                                    síntomas psiquiátricos'),
                                    choices=BEFORE_AFTER_CHOICES,
                                    validators=[validate_choice])
    months = forms.IntegerField(label=_(u'Número de meses de toma del\
                                         fármaco'))
    posology = forms.IntegerField(label=_(u'Posología (mg/día)'))

    class Meta:
        model = Medication
        exclude = ('treatment')

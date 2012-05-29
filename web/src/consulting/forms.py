# -*- encoding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.forms.widgets import DateInput
from django.conf import settings
from django.utils.safestring import mark_safe
from django.forms.widgets import RadioFieldRenderer
from django.forms.util import flatatt
from django.utils.encoding import force_unicode
from userprofile.models import Profile
from consulting.validators import validate_choice
from consulting.models import Appointment, Prescription
from medicament.models import Component


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


class AdminRadioFieldRenderer(RadioFieldRenderer):
    def render(self):
        """Outputs a <ul> for this set of radio fields."""
        return mark_safe(u'<ul%s>\n%s\n</ul>' % (
            flatatt(self.attrs),
            u'\n'.join([u'<li class="radio_js" >%s</li>' \
            % force_unicode(w) for w in self]))
        )


class PrescriptionForm(forms.ModelForm):
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
    before_after = forms.ChoiceField(label=_(u'Anterior/Posterior\
                                    síntomas psiquiátricos'),
                                    choices=BEFORE_AFTER_CHOICES,
                                    validators=[validate_choice])
    months = forms.IntegerField(label=_(u'Número de meses de toma del\
                                         fármaco'))
    posology = forms.IntegerField(label=_(u'Posología (mg/día)'))

    class Meta:
        model = Prescription
        exclude = ('treatment')

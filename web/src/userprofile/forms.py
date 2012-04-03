# -*- encoding: utf-8 -*-
from django import forms
from django.contrib.localflavor.es.forms import ESIdentityCardNumberField
from django.contrib.localflavor.es.forms import ESPostalCodeField
from django.contrib.localflavor.es.forms import ESPhoneNumberField
from django.utils.translation import ugettext_lazy as _
from django.forms.widgets import DateInput
from models import Profile
from consulting.validators import validate_choice


class ProfileForm(forms.ModelForm):
    SEX = (
        (-1, _(u'Seleccione el sexo')),
        (1, _(u'Mujer')),
        (2, _(u'Hombre')),
    )
    STATUS = (
        (-1, _(u'Seleccione el estado civil')),
        (1, _(u'Casado')),
        (2, _(u'Pareja estable')),
        (3, _(u'Divorciado')),
        (4, _(u'Viudo')),
        (5, _(u'Soltero/a')),
        (6, _(u'Otros')),
    )

    ROLE = (
        (Profile.DOCTOR, _(u'Médico')),
        (Profile.ADMINISTRATIVE, _(u'Administrativo')),
        (Profile.PATIENT, _(u'Paciente')),
    )

    name = forms.CharField(max_length=150)
    first_surname = forms.CharField(max_length=150)
    second_surname = forms.CharField(max_length=150)
    nif = ESIdentityCardNumberField()
    sex = forms.ChoiceField(choices=SEX, validators=[validate_choice])
    address = forms.CharField(max_length=150)
    town = forms.CharField(max_length=150)
    postcode = ESPostalCodeField()
    dob = forms.DateField(widget=DateInput(
                            attrs={'class': 'span2', 'size': '16'}))
    status = forms.ChoiceField(choices=STATUS, validators=[validate_choice])
    phone1 = ESPhoneNumberField()
    phone2 = ESPhoneNumberField(required=False)
    email = forms.EmailField(required=False)
    profession = forms.CharField(max_length=150, required=False)

    class Meta:
        model = Profile
        exclude = ('user', 'role', 'doctor')

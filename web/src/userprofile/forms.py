# -*- encoding: utf-8 -*-
from django import forms
from django.contrib.localflavor.es.forms import ESIdentityCardNumberField
from django.contrib.localflavor.es.forms import ESPostalCodeField
from django.contrib.localflavor.es.forms import ESPhoneNumberField
from django.utils.translation import ugettext_lazy as _
from django.forms.widgets import DateInput
from django.conf import settings
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
        (1, _(u'Casado/a')),
        (2, _(u'Pareja estable')),
        (3, _(u'Divorciado/a')),
        (4, _(u'Viudo/a')),
        (5, _(u'Soltero/a')),
        (6, _(u'Otros')),
    )

    ROLE = (
        (settings.DOCTOR, _(u'Médico')),
        (settings.ADMINISTRATIVE, _(u'Administrativo')),
        (settings.PATIENT, _(u'Paciente')),
    )

    name = forms.CharField(label=_(u'Nombre'), max_length=150)
    first_surname = forms.CharField(label=_(u'Primer Apellido'),
                                    max_length=150)
    second_surname = forms.CharField(label=_(u'Segundo Apellido'),
                                        max_length=150)
    nif = ESIdentityCardNumberField(label=_(u'NIF'))
    sex = forms.ChoiceField(label=_(u'Sexo'), choices=SEX,
                            validators=[validate_choice])
    address = forms.CharField(label=_(u'Dirección'), max_length=150)
    town = forms.CharField(label=_(u'Municipio'), max_length=150)
    postcode = ESPostalCodeField(label=_(u'Código Postal'))
    dob = forms.DateField(label=_(u'Fecha de Nacimiento'), widget=DateInput(
                            attrs={'class': 'span2', 'size': '16'}))
    status = forms.ChoiceField(label=_(u'Estado Civil'), choices=STATUS,
                                validators=[validate_choice])
    phone1 = ESPhoneNumberField(label=_(u'Teléfono 1'))
    phone2 = ESPhoneNumberField(label=_(u'Teléfono 2'), required=False)
    email = forms.EmailField(label=_(u'Correo Electrónico'), required=False)
    profession = forms.CharField(label=_(u'Profesión'), max_length=150,
                                required=False)

    class Meta:
        model = Profile
        exclude = ('user', 'role', 'doctor', 'search_field')

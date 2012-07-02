# -*- encoding: utf-8 -*-
from datetime import date
from django import forms
from django.contrib.localflavor.es.forms import ESIdentityCardNumberField
from django.contrib.localflavor.es.forms import ESPostalCodeField
from django.contrib.localflavor.es.forms import ESPhoneNumberField
from django.utils.translation import ugettext_lazy as _
from django.forms.widgets import DateInput
from django.conf import settings
from models import Profile


class ProfileForm(forms.ModelForm):
    ADULT = 18
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
    nif = ESIdentityCardNumberField(label=_(u'NIF'), required=False,
                    error_messages={'unique': _(u'Este NIF ya existe')})
    sex = forms.ChoiceField(label=_(u'Sexo'), choices=Profile.SEX,
                        required=False)
    address = forms.CharField(label=_(u'Dirección'), max_length=150,
                            required=False)
    town = forms.CharField(label=_(u'Municipio'), max_length=150,
                            required=False)
    postcode = ESPostalCodeField(label=_(u'Código Postal'), required=False)
    dob = forms.DateField(label=_(u'Fecha de Nacimiento'),
                    input_formats=('%d/%m/%Y',),
                    widget=DateInput(attrs={'class': 'span2', 'size': '16'},
                                    format='%d/%m/%Y'),
                    required=False)
    status = forms.ChoiceField(label=_(u'Estado Civil'),
                                choices=Profile.STATUS, required=False)
    phone1 = ESPhoneNumberField(label=_(u'Teléfono 1'))
    phone2 = ESPhoneNumberField(label=_(u'Teléfono 2'), required=False)
    email = forms.EmailField(label=_(u'Correo Electrónico'))
    profession = forms.CharField(label=_(u'Profesión'), max_length=150,
                                required=False)

    def age(self, dob):
        today = date.today()
        years = today.year - dob.year
        if today.month < dob.month or\
            today.month == dob.month and today.day < dob.day:
            years -= 1
        return years

    def clean(self):
        cleaned_data = super(ProfileForm, self).clean()
        nif = cleaned_data.get("nif")
        dob = cleaned_data.get("dob")

        if not nif:
            if dob is None:
                msg = _(u"Este campo es obligatorio")
                self._errors["dob"] = self.error_class([msg])
            else:
                if dob > date.today():
                    msg = _(u"Fecha de Nacimiento debe ser menor que la fecha\
                         actual")
                    self._errors["dob"] = self.error_class([msg])
                else:
                    age = self.age(dob)
                    if age >= ProfileForm.ADULT:
                        msg = _(u"Este campo es obligatorio")
                        self._errors["nif"] = self.error_class([msg])
        else:
            if not dob is None and dob > date.today():
                msg = _(u"Fecha de Nacimiento debe ser menor que la fecha\
                         actual")
                self._errors["dob"] = self.error_class([msg])

        return cleaned_data

    class Meta:
        model = Profile
        exclude = ('user', 'role', 'doctor', 'search_field', 'patients')

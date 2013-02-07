# -*- encoding: utf-8 -*-
from datetime import date
from django import forms
from django.contrib.localflavor.es.forms import ESIdentityCardNumberField
from django.contrib.localflavor.es.forms import ESPostalCodeField
from django.contrib.localflavor.es.forms import ESPhoneNumberField

from django.forms.widgets import DateInput

from django.utils.translation import ugettext_lazy as _

from django.conf import settings

from consulting.validators import validate_choice

from models import Profile
from stadistic.forms import FiltersForm


class ProfileForm(forms.ModelForm):
    ADULT = 14
    ACTIVE = (
        (settings.ACTIVE, _(u'Activada')),
        (settings.DEACTIVATE, _(u'Desactivada')),
    )

    name = forms.CharField(label=_(u'Nombre'), max_length=150, required=True)
    first_surname = forms.CharField(label=_(u'Primer Apellido'),
                                    max_length=150, required=True)
    second_surname = forms.CharField(label=_(u'Segundo Apellido'),
                                        max_length=150, required=False)
    nif = ESIdentityCardNumberField(label=_(u'DNI/NIF'), required=False,
                    error_messages={'unique': _(u'Este documento ya existe')},
                    help_text=_(u"Requerido para pacientes mayores de %d años" % ADULT))
    postcode = ESPostalCodeField(label=_(u'Código Postal'), required=False)

    dob = forms.DateField(label=_(u'Fecha de Nacimiento'),
                    input_formats=(settings.DATE_INPUT_FORMAT,),
                    widget=DateInput(attrs={'class': 'span12', 
                                            'size': '16', 
                                            'data-date-format':'dd/mm/yyyy', 
                                            'data-date-weekstart': '1',
                                            'data-date-language': 'es'},
                                    format=settings.DATE_INPUT_FORMAT),
                    required=False)
    phone1 = ESPhoneNumberField(label=_(u'Teléfono 1'))
    phone2 = ESPhoneNumberField(label=_(u'Teléfono 2'), required=False)
    email = forms.EmailField(label=_(u'Correo Electrónico'), required=False)
    profession = forms.CharField(label=_(u'Profesión'), max_length=150,
                                required=False)
    active = forms.ChoiceField(label=_(u'Estado de la cuenta'), choices=ACTIVE, help_text=_(u"Permite el inicio de sesión en el sistema"))

    def age(self, dob):
        today = date.today()
        years = today.year - dob.year
        if today.month < dob.month or\
            today.month == dob.month and today.day < dob.day:
            years -= 1
        return years

    def clean_nif(self):
        data = self.cleaned_data.get('nif', '')
        if data.startswith('0'):
            data = data[1:]
        return data

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
                        msg = _(u"Documento no válido. Compruebe que no ha cometido ningún error y que el campo sigue el formato 01234567X")
                        self._errors["nif"] = self.error_class([msg])
        else:
            if not dob is None and dob > date.today():
                msg = _(u"Fecha de Nacimiento debe ser menor que la fecha\
                         actual")
                self._errors["dob"] = self.error_class([msg])

        return cleaned_data

    def __init__(self, *args, **kwargs):
        exclude_list = kwargs['exclude_list']
        del kwargs['exclude_list']

        super(ProfileForm, self).__init__(*args, **kwargs)

        for field in exclude_list:
            del self.fields[field]

    class Meta:
        model = Profile
        exclude = ('created_at', 'updated_at', 'medical_number')

ProfileSurveyForm = ProfileForm 

class ProfileFiltersForm(FiltersForm):
    def __init__(self, *args, **kwargs):
        super(FiltersForm, self).__init__(*args, **kwargs)
         
        exclude = ('options', 'variables', 'dimensions', 'treatment', 'adherence', 'aves', 'depression', 'anxiety')

        for field_name in exclude:
            if field_name in self.fields:
                del self.fields[field_name]

        self.fields['date'].label = _(u'Fecha de alta')
        

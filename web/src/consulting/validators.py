# -*- encoding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _


def validate_choice(value):
    if value == '-1':
        raise forms.ValidationError(_(u'Este campo es obligatorio'))

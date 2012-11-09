# -*- encoding: utf-8 -*-
from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.utils.translation import ugettext as _


class UserRegistrationForm(AuthenticationForm):

    username = forms.CharField(max_length=50, widget=forms.TextInput(
        attrs={'class': 'input-xlarge'}))

    password = forms.CharField(max_length=50, widget=forms.PasswordInput(
        attrs={'class': 'input-xlarge'}))

from django.contrib import auth

class ValidatingPasswordChangeForm(PasswordChangeForm):
    MIN_LENGTH = 8

    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')

        # At least MIN_LENGTH long
        if len(password1) < self.MIN_LENGTH:
            raise forms.ValidationError(_(u"La contraseña debe tener una longitud mínima de %d caracteres." % self.MIN_LENGTH))

        # At least one letter and one non-letter
        first_isalpha = password1[0].isalpha()
        if all(c.isalpha() == first_isalpha for c in password1):
            raise forms.ValidationError(_(u"La nueva contraseña debe contener al menos una letra y al menos un número o caracter especial."))

        return password1
from django import forms
from django.contrib.auth.forms import AuthenticationForm


class UserRegistrationForm(AuthenticationForm):

    username = forms.CharField(max_length=50, widget=forms.TextInput(
        attrs={'class': 'input-xlarge'}))

    password = forms.CharField(max_length=50, widget=forms.PasswordInput(
        attrs={'class': 'input-xlarge'}))

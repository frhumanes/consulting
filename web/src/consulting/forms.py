# -*- encoding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.forms.widgets import DateInput
from django.conf import settings
from userprofile.models import Profile
from consulting.models import Appointment
from consulting.validators import validate_choice


class RecipientChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s %s" % (obj.first_name, obj.last_name)


class AppointmentForm(forms.ModelForm):
    format = _(u'%d/%m/%Y')
    input_formats = [format]

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
        exclude = ('patient', 'questionnaire', 'answers', 'treatment')

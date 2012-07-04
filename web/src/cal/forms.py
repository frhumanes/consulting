# -*- encoding: utf-8 -*-

from django.utils.translation import ugettext as _
from django import forms

from cal.models import SlotType
from cal.models import Slot
from cal.models import Appointment
from django.contrib.auth.models import User
from django.conf import settings
import cal.settings as cal_settings
from cal.custom_fields import SlotTypeChoiceField


class SlotTypeForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={'cols': 60,
        'rows': 4, 'class': 'span5'}))

    duration = forms.IntegerField(widget=forms.TextInput(attrs={'cols': 60,
        'rows': 4, 'class': 'span5'}))

    class Meta:
        model = SlotType
        exclude = ('created_at', 'updated_at')

    def clean(self):
        cleaned_data = self.cleaned_data
        duration = cleaned_data.get("duration")

        if duration:
            if int(duration) * 60 > cal_settings.TOTAL_HOURS.seconds:
                msg = _("Duration must be lower than %s minutes."
                    % (cal_settings.TOTAL_HOURS.seconds / 60))
                self._errors['duration'] = self.error_class([msg])
                del cleaned_data["duration"]

        return cleaned_data


class SlotForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        if 'user' in kwargs:
            user = kwargs.pop('user')
            super(SlotForm, self).__init__(*args, **kwargs)

            if not user is None:
                if user.get_profile().is_doctor():
                    queryset = SlotType.objects.filter(doctor=user)
                else:
                    queryset = SlotType.objects.none()

                self.fields['slot_type'] = SlotTypeChoiceField(
                    label=_(u"Slot type"),
                    queryset=queryset,
                    widget=forms.Select(attrs={'class': 'span5'}))
        else:
            super(SlotForm, self).__init__(*args, **kwargs)

    slot_type = SlotTypeChoiceField(label=_(u"Slot type"),
        queryset=SlotType.objects.none(),
        widget=forms.Select(attrs={'class': 'span5'}))

    weekday = forms.CharField(widget=forms.Select(
        attrs={'class': 'span5'}, choices=Slot.WEEKDAYS))

    date = forms.DateField(input_formats=(settings.DATE_FORMAT,),
        widget=forms.DateInput(format=settings.DATE_FORMAT,
            attrs={'class': 'span5'}))

    start_time = forms.TimeField(widget=forms.TimeInput(
        attrs={'class': 'span5'}))

    end_time = forms.TimeField(widget=forms.TimeInput(
        attrs={'class': 'span5'}))

    note = forms.CharField(widget=forms.Textarea(attrs={'cols': 60, 'rows': 4,
        'class': 'span5'}), required=False)

    class Meta:
        model = Slot
        exclude = ('created_at', 'updated_at')

    def clean(self):
        cleaned_data = self.cleaned_data
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time:
            if end_time < start_time:
                msg = _("End time must be greater than start time.")
                self._errors['end_time'] = self.error_class([msg])
                del cleaned_data["end_time"]

        return cleaned_data


class DoctorSelectionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(DoctorSelectionForm, self).__init__(*args, **kwargs)
        queryset = User.objects.filter(profile__role=settings.DOCTOR)
        choices = [('', '--------')]
        choices.extend([(doc.id, unicode(doc)) for doc in queryset])
        self.fields['doctor'].choices = choices

    doctor = forms.ChoiceField(label=_(u"Doctor"),
        widget=forms.Select(
            attrs={'class': 'input-medium search-query span5'}))


class AppointmentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        if 'user' in kwargs:
            user = kwargs.pop('user')
            super(AppointmentForm, self).__init__(*args, **kwargs)

            if not user is None:
                if user.get_profile().is_doctor():
                    queryset = SlotType.objects.filter(doctor=user)
                else:
                    queryset = SlotType.objects.none()

                self.fields['app_type'] = SlotTypeChoiceField(
                    label=_(u"Appointment type"),
                    queryset=queryset,
                    widget=forms.Select(attrs={'class': 'span5'}))
        else:
            super(AppointmentForm, self).__init__(*args, **kwargs)

    app_type = SlotTypeChoiceField(label=_(u"Appointment type"),
        queryset=SlotType.objects.none(),
        widget=forms.Select(attrs={'class': 'span5'}))

    date = forms.DateField(input_formats=(settings.DATE_FORMAT,),
        widget=forms.DateInput(format=settings.DATE_FORMAT,
            attrs={'class': 'span5'}))

    start_time = forms.TimeField(widget=forms.TimeInput(
        attrs={'class': 'span5'}))

    end_time = forms.TimeField(widget=forms.TimeInput(
        attrs={'class': 'span5'}))

    note = forms.CharField(widget=forms.Textarea(attrs={'cols': 60, 'rows': 4,
        'class': 'span5'}), required=False)

    class Meta:
        model = Appointment
        exclude = ('created_at', 'updated_at')

    def clean(self):
        cleaned_data = self.cleaned_data
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time:
            if end_time <= start_time:
                msg = _("End time must be greater than start time.")
                self._errors['end_time'] = self.error_class([msg])
                del cleaned_data["end_time"]

        return cleaned_data

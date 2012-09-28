# -*- encoding: utf-8 -*-

from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.conf import settings
from django import forms

from cal.models import SlotType
from cal.models import Slot
from cal.models import Appointment
from cal.models import Vacation
from cal.models import Event

from cal.custom_fields import SlotTypeChoiceField

import cal.settings as cal_settings


class VacationForm(forms.ModelForm):
    date = forms.DateField(input_formats=(settings.DATE_FORMAT,),
        widget=forms.DateInput(format=settings.DATE_FORMAT,
            attrs={'class': 'span9'}))

    description = forms.CharField(widget=forms.Textarea(attrs={'cols': 60,
        'rows': 4, 'class': 'span9'}), required=False)

    class Meta:
        model = Vacation
        exclude = ('created_at', 'updated_at')


class EventForm(forms.ModelForm):
    date = forms.DateField(input_formats=(settings.DATE_FORMAT,),
        widget=forms.DateInput(format=settings.DATE_FORMAT,
            attrs={'class': 'span9'}))

    start_time = forms.TimeField(widget=forms.TimeInput(
        attrs={'class': 'span9'}))

    end_time = forms.TimeField(widget=forms.TimeInput(
        attrs={'class': 'span9'}))

    description = forms.CharField(widget=forms.Textarea(attrs={'cols': 60,
        'rows': 4, 'class': 'span9'}), required=False)

    class Meta:
        model = Event
        exclude = ('created_at', 'updated_at')

    def clean(self):
        cleaned_data = super(EventForm, self).clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if not start_time is None and not end_time is None:
            time_format = '%H:%M'

            if end_time <= start_time:
                msg = _("End time must be greater than start time.")
                self._errors['end_time'] = self.error_class([msg])
                del cleaned_data["end_time"]

            if start_time < cal_settings.START_TIME \
                or start_time > cal_settings.END_TIME:
                start_time_err = \
                    _("Start time must be in the interval %s to %s")\
                    % (cal_settings.START_TIME.strftime(time_format),
                        cal_settings.END_TIME.strftime(time_format))
                start_time_msg = _(start_time_err)
                self._errors['start_time'] = self.error_class([start_time_msg])
                if "start_time" in cleaned_data:
                    del cleaned_data["start_time"]

            if end_time < cal_settings.START_TIME \
                or end_time > cal_settings.END_TIME:
                end_time_err = _("End time must be in the interval %s to %s")\
                    % (cal_settings.START_TIME.strftime(time_format),
                        cal_settings.END_TIME.strftime(time_format))
                end_time_msg = _(end_time_err)
                self._errors['end_time'] = self.error_class([end_time_msg])
                if "end_time" in cleaned_data:
                    del cleaned_data["end_time"]

        return cleaned_data


class SlotTypeForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={'cols': 60,
        'rows': 4, 'class': 'span9'}))

    duration = forms.IntegerField(widget=forms.TextInput(attrs={'cols': 60,
        'rows': 4, 'class': 'span9'}))

    description = forms.CharField(widget=forms.Textarea(attrs={'cols': 60,
        'rows': 4, 'class': 'span9'}), required=False)

    vacation = forms.BooleanField(widget=forms.CheckboxInput(
        attrs={'class': 'span1'}), required=False)

    event = forms.BooleanField(widget=forms.CheckboxInput(
        attrs={'class': 'span1'}), required=False)

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
                    widget=forms.Select(attrs={'class': 'span9'}))
        else:
            super(SlotForm, self).__init__(*args, **kwargs)

    slot_type = SlotTypeChoiceField(label=_(u"Slot type"),
        queryset=SlotType.objects.none(),
        widget=forms.Select(attrs={'class': 'span9'}))

    weekday = forms.CharField(widget=forms.Select(
        attrs={'class': 'span9'}, choices=Slot.WEEKDAYS))

    date = forms.DateField(input_formats=(settings.DATE_FORMAT,),
        widget=forms.DateInput(format=settings.DATE_FORMAT,
            attrs={'class': 'span9'}))

    start_time = forms.TimeField(widget=forms.TimeInput(
        attrs={'class': 'span9'}))

    end_time = forms.TimeField(widget=forms.TimeInput(
        attrs={'class': 'span9'}))

    description = forms.CharField(widget=forms.Textarea(attrs={'cols': 60,
        'rows': 4, 'class': 'span9'}), required=False)

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
        queryset = User.objects.filter(profiles__role=settings.DOCTOR)
        choices = [('', '--------')]
        choices.extend([(doc.id, doc.get_profile().get_full_name()) for doc in queryset])
        self.fields['doctor'].choices = choices

    doctor = forms.ChoiceField(label=_(u"Doctor"),
        widget=forms.Select(
            attrs={'class': 'input-medium search-query span9'}))


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
                    widget=forms.Select(attrs={'class': 'span9'}),
                    required=False)
        else:
            super(AppointmentForm, self).__init__(*args, **kwargs)

    app_type = SlotTypeChoiceField(label=_(u"Appointment type"),
        queryset=SlotType.objects.none(),
        widget=forms.Select(attrs={'class': 'span9'}),
        required=False)

    date = forms.DateField(input_formats=(settings.DATE_FORMAT,),
        widget=forms.DateInput(format=settings.DATE_FORMAT,
            attrs={'class': 'span9'}))

    start_time = forms.TimeField(widget=forms.TimeInput(
        attrs={'class': 'span9'}))

    end_time = forms.TimeField(widget=forms.TimeInput(
        attrs={'class': 'span9'}))

    description = forms.CharField(widget=forms.Textarea(attrs={'cols': 60,
        'rows': 4, 'class': 'span9'}), required=False)

    class Meta:
        model = Appointment
        exclude = ('created_at', 'updated_at')

    def clean(self):
        cleaned_data = super(AppointmentForm, self).clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")
        app_type = self.cleaned_data.get("app_type", None)
        description = self.cleaned_data.get("description", None)

        if not start_time is None and not end_time is None:
            time_format = '%H:%M'

            if end_time <= start_time:
                msg = _("End time must be greater than start time.")
                self._errors['end_time'] = self.error_class([msg])
                del cleaned_data["end_time"]

            if start_time < cal_settings.START_TIME \
                or start_time > cal_settings.END_TIME:
                start_time_err = \
                    _("Start time must be in the interval %s to %s")\
                    % (cal_settings.START_TIME.strftime(time_format),
                        cal_settings.END_TIME.strftime(time_format))
                start_time_msg = _(start_time_err)
                self._errors['start_time'] = self.error_class([start_time_msg])
                if "start_time" in cleaned_data:
                    del cleaned_data["start_time"]

            if end_time < cal_settings.START_TIME \
                or end_time > cal_settings.END_TIME:
                end_time_err = _("End time must be in the interval %s to %s")\
                    % (cal_settings.START_TIME.strftime(time_format),
                        cal_settings.END_TIME.strftime(time_format))
                end_time_msg = _(end_time_err)
                self._errors['end_time'] = self.error_class([end_time_msg])
                if "end_time" in cleaned_data:
                    del cleaned_data["end_time"]

        if not app_type:
            if not description:
                msg = _("You must write a description if you"\
                        " do not choose an appointment type")
                self._errors['description'] = self.error_class([msg])
                if "description" in cleaned_data:
                    del cleaned_data["description"]

        return cleaned_data

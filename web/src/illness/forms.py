# -*- encoding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _

from cal.models import Appointment
from illness.models import Illness
from userprofile.models import Profile


class IllnessSelectionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'id_appointment' in kwargs:
            id_appointment = kwargs.pop('id_appointment')
            super(IllnessSelectionForm, self).__init__(*args, **kwargs)
            appointment = Appointment.objects.get(id=id_appointment)
            #illnesses = appointment.patient.get_profile().illnesses.all()\
            #            .order_by('code')
            illnesses = Illness.objects.all()
            choices = [('', '--------')]
            choices.extend(
                    [(illness.code, illness.name) for illness in illnesses])
            self.fields['illness'].choices = choices
        else:
            super(IllnessSelectionForm, self).__init__(*args, **kwargs)

    illness = forms.ChoiceField(label=_(u"Diagnóstico"),
                        widget=forms.Select(
                        attrs={'class': 'input-medium search-query span12'}))


class IllnessAddPatientForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(IllnessAddPatientForm, self).__init__(*args, **kwargs)
        illnesses = Illness.objects.all().order_by('code')
        choices = []
        choices.extend(
                [(illness.id, illness.name) for illness in illnesses])
        self.fields['illnesses'].choices = choices

    illnesses = forms.MultipleChoiceField(label=_(u"Enfermedades"),
                widget=forms.CheckboxSelectMultiple())

    class Meta:
        model = Profile
        fields = ('illnesses', 'created_by')

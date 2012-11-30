#!/usr/bin/python
# -*- encoding: utf-8 -*-

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from private_messages.models import Message
from django.db.models import Q


class RecipientChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        if obj.get_profile().is_doctor():
            return obj.get_profile().get_full_name(True)
        else:
            return "%s (%s)" % (obj.get_profile().get_full_name(), obj.username)


class MessageForm(forms.ModelForm):
    subject = forms.CharField(label=_("Asunto"),
        widget=forms.TextInput(attrs={'class': 'span12'}))
    parent = forms.ModelChoiceField(label=_(""),queryset=Message.objects.all(),
        widget=forms.HiddenInput(attrs={'class': 'span12'}),required=False)
    body = forms.CharField(label=_("Mensaje"),
        widget=forms.Textarea(
            attrs={'cols': 80, 'rows': 10, 'class': 'span12'}))

    def __init__(self, *args, **kwargs):
        if 'user' in kwargs:
            user = kwargs.pop('user')
            super(MessageForm, self).__init__(*args, **kwargs)

            if not user is None:
                profile = user.get_profile()
                queryset = None

                if not profile.is_patient():
                    queryset = User.objects.filter(Q(is_active=True), Q(profiles__doctor=user) | Q(profiles__role__in=[settings.DOCTOR, settings.ADMINISTRATIVE])).order_by('profiles__role').exclude(id=user.id)
                else:
                    queryset = User.objects.filter(profiles=profile.doctor.get_profile(), is_active=True)
                self.fields['recipient'] = RecipientChoiceField(
                        label=_(u"Destinatario"),
                        queryset=queryset,
                        widget=forms.Select(attrs={'class': 'span12'}))
        else:
            super(MessageForm, self).__init__(*args, **kwargs)

    recipient = forms.ModelChoiceField(label=_("Destinatario"),
        queryset=User.objects.none(),
        widget=forms.Select(attrs={'class': 'span5'}))

    class Meta:
        model = Message
        exclude = ('author', 'sent_at', 'unread')


class ReplyMessageForm(forms.ModelForm):
    body = forms.CharField(
        widget=forms.Textarea(
            attrs={'cols': 60, 'rows': 10, 'class': 'span12'}))

    class Meta:
        model = Message
        exclude = (
            'author',
            'sent_at',
            'unread',
            'recipient',
            'subject'
        )

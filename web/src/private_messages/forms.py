#!/usr/bin/python
# -*- encoding: utf-8 -*-

from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from private_messages.models import Message


class RecipientChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s %s (%s)" % (obj.first_name, obj.last_name, obj.username)


class MessageForm(forms.ModelForm):
    subject = forms.CharField(label=_("Asunto"),
        widget=forms.TextInput(attrs={'class': 'span6'}))
    body = forms.CharField(label=_("Mensaje"),
        widget=forms.Textarea(
            attrs={'cols': 60, 'rows': 10, 'class': 'span6'}))

    def __init__(self, *args, **kwargs):
        if 'user' in kwargs:
            user = kwargs.pop('user')
            super(MessageForm, self).__init__(*args, **kwargs)

            if not user is None:
                profile = user.get_profile()
                queryset = None

                if profile.is_doctor():
                    queryset = profile.patients
                else:
                    queryset = User.objects.filter(\
                        profile=profile.doctor.get_profile)

                self.fields['recipient'] = RecipientChoiceField(
                    label=_(u"Destinatario"),
                    queryset=queryset,
                    widget=forms.Select(attrs={'class': 'span6'}))
        else:
            super(MessageForm, self).__init__(*args, **kwargs)

    recipient = forms.ModelChoiceField(label=_("Destinatario"),
        queryset=User.objects.none(),
        widget=forms.Select(attrs={'class': 'span6'}))

    class Meta:
        model = Message
        exclude = ('author', 'sent_at', 'unread')


class ReplyMessageForm(forms.ModelForm):
    body = forms.CharField(
        widget=forms.Textarea(
            attrs={'cols': 60, 'rows': 10, 'class': 'span6'}))

    class Meta:
        model = Message
        exclude = (
            'author',
            'sent_at',
            'unread',
            'recipient',
            'subject'
        )

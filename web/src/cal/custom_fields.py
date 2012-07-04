# -*- encoding: utf-8 -*-

from django import forms


class SlotTypeChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s (%s min)" % (obj.title, obj.duration)

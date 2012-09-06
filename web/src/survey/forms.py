# -*- encoding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.conf import settings

from survey.models import Question


class SelectBlockForm(forms.Form):
    BLOCK = (
        ('', '-----------'),
        (settings.ANXIETY_DEPRESSION_EXTENSIVE,
        _(u'Extenso')),
        (settings.ANXIETY_DEPRESSION_SHORT,
        _(u'Abreviado'))
    )

    block = forms.ChoiceField(
                    label=_(u'Valoración de la depresión y la ansiedad:'),
                    choices=BLOCK,
                    widget=forms.Select(
                        attrs={'class': 'input-medium search-query span2'}))


class SelectBehaviorSurveyForm(forms.Form):
    SURVEY = (
        ('', '-----------'),
        (settings.BEHAVIOR_EXTENSIVE, _(u'Extenso')),
        (settings.BEHAVIOR_SHORT, _(u'Abreviado'))
    )

    survey = forms.ChoiceField(
                    label=_(u'Formato:'),
                    choices=SURVEY,
                    widget=forms.Select(
                        attrs={'class': 'input-medium search-query span2'}))


class QuestionsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'dic' in kwargs and 'selected_options' in kwargs:
            dic = kwargs.pop('dic')
            selected_options = kwargs.pop('selected_options')
            super(QuestionsForm, self).__init__(*args, **kwargs)

            for k, values in dic.items():
                question = get_object_or_404(Question, pk=int(k))
                initial_options = []
                for v in values:
                    id_option = v[0]
                    if selected_options:
                        if selected_options.filter(id=id_option):
                            initial_options.append(id_option)
                self.fields[question.code] = forms.MultipleChoiceField(
                        label=question.text,
                        widget=forms.CheckboxSelectMultiple(), choices=values,
                        required=False, initial=initial_options)
        else:
            super(QuestionsForm, self).__init__(*args, **kwargs)

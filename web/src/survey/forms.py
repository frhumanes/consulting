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
                        attrs={'class': 'input-medium search-query span12'}))


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
                        attrs={'class': 'input-medium search-query span12'}))


class QuestionsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'dic' in kwargs and 'selected_options' in kwargs:
            dic = kwargs.pop('dic')
            selected_options = kwargs.pop('selected_options')
            super(QuestionsForm, self).__init__(*args, **kwargs)
            pkeys = dic.keys()
            pkeys.sort()
            for k in pkeys:
                question = get_object_or_404(Question, pk=int(k))
                values = dic[k]
                if question.single:
                    initial_option = ''
                    for v in values:
                        id_option = v[0]
                        if selected_options:
                            if selected_options.filter(id=id_option):
                                initial_option = id_option
                    values.insert(0,('',''))
                    if question.code.startswith('DS'):
                        self.fields[question.code] = forms.ChoiceField(
                            label=question.text,
                            widget=forms.Select(attrs={'class': 'span6'}), choices=values,
                            required=False, initial=initial_option)
                        self.fields[question.code+'_value'] = forms.CharField(label="DS", widget=forms.TextInput(attrs={'class': 'span2'}))
                    else:
                        self.fields[question.code] = forms.ChoiceField(
                            label=question.text,
                            widget=forms.Select(), choices=values,
                            required=False, initial=initial_option)

                else:
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

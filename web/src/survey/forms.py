# -*- encoding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404

from survey.models import Survey, Question


class SelectSurveyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(SelectSurveyForm, self).__init__(*args, **kwargs)
        surveys = Survey.objects.filter(id__in=[1, 3, 4])

        choices = [('', '--------')]
        choices.extend(
        [(survey.id, survey.name + '-' + survey.get_kind())\
         for survey in surveys])
        self.fields['survey'].choices = choices

    survey = forms.ChoiceField(label=_(u"Encuesta"),
        widget=forms.Select(
            attrs={'class': 'input-medium search-query span4'}))


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
                    if selected_options.filter(id=id_option):
                        initial_options.append(id_option)
                self.fields[question.code] = forms.MultipleChoiceField(
                        label=question.text,
                        widget=forms.CheckboxSelectMultiple(), choices=values,
                        required=False, initial=initial_options)
        else:
            super(QuestionsForm, self).__init__(*args, **kwargs)

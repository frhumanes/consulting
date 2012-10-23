# -*- encoding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.forms.util import flatatt, StrAndUnicode
from itertools import chain
from django.template.defaultfilters import escape
from django.utils.html import conditional_escape, mark_safe

from survey.models import Question


class SelectBlockForm(forms.Form):
    BLOCK = (
        ('', '-----------'),
        (settings.EXTENSO,
        _(u'Extenso')),
        (settings.ABREVIADO,
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
        (settings.EXTENSO, _(u'Extenso')),
        (settings.ABREVIADO, _(u'Abreviado'))
    )

    survey = forms.ChoiceField(
                    label=_(u'Formato:'),
                    choices=SURVEY,
                    widget=forms.Select(
                        attrs={'class': 'input-medium search-query span12'}))
force_unicode = unicode

class SelectWidgetBootstrap(forms.Select):
    """
    http://twitter.github.com/bootstrap/components.html#buttonDropdowns
    Needs bootstrap and jquery
    """
    js = ("""
    <script type="text/javascript">
        function setBtnGroupVal(elem) {
            btngroup = $(elem).parents('.btn-group');
            selected_a = btngroup.find('a[selected]');
            if (selected_a.length > 0) {
                val = selected_a.attr('data-value');
                label = selected_a.html();
            } else {
                btngroup.find('a').first().attr('selected', 'selected');
                setBtnGroupVal(elem);
            }
            btngroup.find('input[type=hidden]').val(val);
            /*btngroup.find('.btn-group-label').html(label.substring(0, 20)+'...');*/
            btngroup.find('.btn-group-label').val(label);
        }
        $(document).ready(function() {
            $('.btn-group-form input').each(function() {
                setBtnGroupVal(this);
            });
            $('.btn-group-form li a').click(function() {
                $(this).parent().siblings().find('a').attr('selected', false);
                $(this).attr('selected', true);
                setBtnGroupVal(this);
            });
        })
    </script>
    """)
    def __init__(self, attrs={'class': 'btn-group pull-right btn-group-form'}, choices=()):
        self.noscript_widget = forms.Select(attrs={}, choices=choices)
        super(SelectWidgetBootstrap, self).__init__(attrs, choices)
    
    def __setattr__(self, k, value):
        super(SelectWidgetBootstrap, self).__setattr__(k, value)
        if k != 'attrs':
            self.noscript_widget.__setattr__(k, value)
    
    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = ''
        final_attrs = self.build_attrs(attrs, name=name)
        output = ["""<div%(attrs)s>"""
                  """    <input class="btn-group-label" type="text" readonly="readonly" value="%(label)s" />"""
                  """    <button class="btn btn-info dropdown-toggle" type="button" data-toggle="dropdown">"""
                  """        <span class="caret"></span>"""
                  """    </button>"""
                  """    <ul class="dropdown-menu">"""
                  """        %(options)s"""
                  """    </ul>"""
                  """    <input type="hidden" name="%(name)s" value="" class="btn-group-value" />"""
                  """</div>"""
                  """%(js)s"""
                  """<noscript>%(noscript)s</noscript>"""
                   % {'attrs': flatatt(final_attrs),
                      'options':self.render_options(choices, [value]),
                      'label': _(u'Marque una opción'),
                      'name': name,
                      'js': SelectWidgetBootstrap.js,
                      'noscript': self.noscript_widget.render(name, value, {}, choices)} ]
        return mark_safe(u'\n'.join(output))

    def render_option(self, selected_choices, option_value, option_label):
        option_value = force_unicode(option_value)
        selected_html = (option_value in selected_choices) and u' selected="selected"' or ''
        return u'<li><a href="javascript:void(0)" data-value="%s"%s>%s</a></li>' % (
            escape(option_value), selected_html,
            conditional_escape(force_unicode(option_label)))

    def render_options(self, choices, selected_choices):
        # Normalize to strings.
        selected_choices = set([force_unicode(v) for v in selected_choices])
        output = []
        for option_value, option_label in chain(self.choices, choices):
            if isinstance(option_label, (list, tuple)):
                output.append(u'<li class="divider" label="%s"></li>' % escape(force_unicode(option_value)))
                for option in option_label:
                    output.append(self.render_option(selected_choices, *option))
            else:
                output.append(self.render_option(selected_choices, option_value, option_label))
        return u'\n'.join(output)

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
                    initial_option, initial_value = '', ''
                    for v in values:
                        id_option = v[0]
                        if selected_options:
                            if selected_options.filter(option__id=id_option):
                                initial_option = id_option
                                initial_value = selected_options.get(option__id=id_option).value
                    values.insert(0,('',u'Marque una opción'))
                    if question.code.startswith('DS'):
                        self.fields[question.code] = forms.ChoiceField(
                            label=question.text,
                            widget=forms.Select(attrs={'class': 'span6'}), choices=values,
                            required=False, initial=initial_option)
                        self.fields[question.code+'_value'] = forms.CharField(label="DS", required=False, widget=forms.TextInput(attrs={'class': 'span2'}),initial=initial_value)
                    else:
                        self.fields[question.code] = forms.ChoiceField(
                            label=question.text,
                            widget=SelectWidgetBootstrap(), choices=values,
                            required=False, initial=initial_option)

                else:
                    initial_options = []
                    for v in values:
                        id_option = v[0]
                        if selected_options:
                            if selected_options.filter(option__id=id_option):
                                initial_options.append(id_option)
                    self.fields[question.code] = forms.MultipleChoiceField(
                            label=question.text,
                            widget=forms.CheckboxSelectMultiple(), choices=values,
                            required=False, initial=initial_options)
        else:
            super(QuestionsForm, self).__init__(*args, **kwargs)

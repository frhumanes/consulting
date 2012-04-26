# -*- encoding: utf-8 -*-

from django.core.urlresolvers import reverse
from django import template
from private_messages.models import Message
from django.utils.translation import ugettext_lazy as _


register = template.Library()


@register.filter('unread_messages')
def get_unread_messages(user):
    if user is None:
        unread_messages = 0
    else:
        unread_messages = Message.objects.get_inbox_for_user(user)\
            .filter(unread=True).count()

    return unread_messages


@register.simple_tag
def get_header(request):
    if reverse('private_messages_inbox') in request.path:
        return _('Bandeja de entrada')
    elif reverse('private_messages_outbox') in request.path:
        return _('Enviados')
    else:
        return ''


@register.simple_tag
def is_sent_url(request):
    if reverse('private_messages_outbox') == request.path:
        return True
    else:
        return False


@register.tag('match_url')
def do_match_url(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, page_url, _as_, var_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument"\
            % token.contents.split()[0])
    if not (page_url[0] == page_url[-1] and page_url[0] in ('"', "'")):
        raise template.TemplateSyntaxError("%r tag's argument should be\
            in quotes" % tag_name)
    return MatchUrl(page_url[1:-1], var_name)


class MatchUrl(template.Node):

    def __init__(self, page_url, var_name):
        self.page_url = page_url
        self.var_name = var_name

    def render(self, context):
        request = context['request']
        context[self.var_name] = reverse(self.page_url) == request.path
        return ''


@register.tag('match_referer')
def do_match_referer(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, page_url, _as_, var_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument"\
            % token.contents.split()[0])
    if not (page_url[0] == page_url[-1] and page_url[0] in ('"', "'")):
        raise template.TemplateSyntaxError("%r tag's argument should be\
            in quotes" % tag_name)
    return MatchReferer(page_url[1:-1], var_name)


class MatchReferer(template.Node):

    def __init__(self, referer_name, var_name):
        self.referer_name = referer_name
        self.var_name = var_name

    def render(self, context):
        request = context['request']
        referer_url = request.META.get('HTTP_REFERER')
        context[self.var_name] = self.referer_name in referer_url
        return ''

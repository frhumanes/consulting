# -*- encoding: utf-8 -*-

from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from private_messages import views as message_views

urlpatterns = patterns('',
    url(r'^inbox/$', message_views.inbox, name="private_messages_inbox"),

    url(r'^outbox/$', message_views.outbox, name="private_messages_outbox"),

    url(r'^new/$', message_views.create_message, name="private_messages_new"),

    url(r'^new/(?P<recipient_id>\d+)/$', message_views.create_message, name="private_messages_new_for"),

    url(r'^view/(?P<id>\d+)/$', message_views.view_message,
        name="private_messages_view"),

    url(r'^reply/(?P<message_id>\d+)/$', message_views.reply_message,
        name="private_messages_reply"),
)

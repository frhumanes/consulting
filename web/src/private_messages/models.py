#!/usr/bin/python
# -*- encoding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from datetime import datetime
from managers import MessageManager


class Message(models.Model):
    author = models.ForeignKey(User, related_name='message_author')
    recipient = models.ForeignKey(User, related_name='message_recipient')
    parent = models.ForeignKey('self', null=True, blank=True)

    subject = models.CharField(max_length=100)
    body = models.CharField(max_length=5000, blank=True, null=True)
    unread = models.BooleanField(default=True)
    sent_at = models.DateTimeField(default=datetime.now(),
        verbose_name=_("Sent at"))

    # manager
    objects = MessageManager()

    def __unicode__(self):
        return u'%s message at %s' % (self.author, self.sent_at)

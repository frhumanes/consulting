#!/usr/bin/python
# -*- encoding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from datetime import datetime
from managers import MessageManager
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mail

class Message(models.Model):
    author = models.ForeignKey(User, verbose_name=_(u'Autor'), related_name='message_author')
    recipient = models.ForeignKey(User, verbose_name=_(u'Destinatario'), related_name='message_recipient')
    parent = models.ForeignKey('self', null=True, blank=True)

    subject = models.CharField(_(u'Asunto'),max_length=256)
    body = models.TextField(_(u'Cuerpo'),max_length=5000, blank=True, null=True)
    unread = models.BooleanField(_(u'No leido'), default=True)
    sent_at = models.DateTimeField(default=datetime.now(),
        verbose_name=_("Enviado"))

    # manager
    objects = MessageManager()

    def __unicode__(self):
        return u'Mensaje de %s para %s [%s]' % (self.author, self.recipient, self.sent_at)

    def get_responses(self):
        return Message.objects.filter(parent=self)

    def save(self, *args, **kwargs):
        warn = False
        if not self.pk:
            warn = True
        super(Message, self).save(*args, **kwargs)
        if warn:
            try:
                subject = render_to_string('private_messages/notifications/notification_email_subject.txt', {'user': self.recipient.get_profile()})
                # Email subject *must not* contain newlines
                subject = ''.join(subject.splitlines())

                message = render_to_string('private_messages/notifications/notification_email_message.txt', {'user': self.recipient.get_profile()})

                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, 
                            [self.recipient.get_profile().email])
            except:
                pass

    class Meta:
        verbose_name = "Mensaje"
        #app_label = u"Messenger"

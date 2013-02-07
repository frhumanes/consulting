#!/usr/bin/python
# -*- encoding: utf-8 -*-
#
# author: fernando ruiz

from django.core.management.base import BaseCommand, CommandError
from private_messages.models import Message
from userprofile.models import Profile
from datetime import date, timedelta
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import translation
from django.utils.translation import ugettext as _


class Command(BaseCommand):
    args = ''
    help = "Send private messages to doctors with next patient's birthdays"

    def handle(self, *args, **options):
        translation.activate(settings.LANGUAGE_CODE)
        today = date.today()
        i = 0
        for doctor in Profile.objects.filter(role=settings.DOCTOR):
            birthdays = Profile.objects.filter(doctor=doctor.user,
                                               dob__month=today.month,
                                               dob__day=today.day)
            if birthdays:
                msg = Message()
                msg.author = doctor.user
                msg.recipient = doctor.user
                msg.subject = "%s %s/%s" % (_(u'Recordatorio de cumpleaños'),
                                            today.day, today.month)
                msg.body = _(u'Hoy es el cumpleaños de:<br></br>')
                for b in birthdays:
                    msg.body += b.get_full_name()+'<br>'
                msg.save()
                i += 1
        self.stdout.write('Sended %s birthday reminders\n' % i)

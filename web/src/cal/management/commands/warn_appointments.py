#!/usr/bin/python
# -*- encoding: utf-8 -*-
#
# author: fernando ruiz

from django.core.management.base import BaseCommand, CommandError
from cal.models import Appointment
from datetime import date, timedelta
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mail
from django.utils import translation


class Command(BaseCommand):
    args = ''
    help = 'Send reminder mails to patients are going to have an appointment tomorrow'

    def handle(self, *args, **options):
        translation.activate(settings.LANGUAGE_CODE)
        for app in Appointment.objects.filter(notify=True,
                                date=date.today()+timedelta(hours=24)).exclude(patient__email__isnull=True):
            if not app.is_canceled():
                self.stdout.write('Warning "%s"\n' % app.patient.get_profile().email)
                app.warn_patient('reminder')

#!/usr/bin/python
# -*- encoding: utf-8 -*-
#
# author: fernando ruiz

from django.core.management.base import BaseCommand
from consulting.models import Task
from datetime import datetime, date
from django.conf import settings
from django.utils import translation


class Command(BaseCommand):
    args = ''
    help = "Send notification mails to patients about recently available  \
        self-administered surveys"

    def handle(self, *args, **options):
        translation.activate(settings.LANGUAGE_CODE)
        for t in Task.objects.filter(self_administered=True,
                                     assess=True,
                                     completed=False,
                                     previous_days__gt=0):
            nextApp = t.patient.get_profile().get_nextAppointment()
            if nextApp and (datetime.combine(nextApp.date, nextApp.start_time) - datetime.combine(date.today(), nextApp.start_time)).days == t.previous_days and t.patient.get_profile().email:
                self.stdout.write('Warning "%s"\n' %
                                  t.patient.get_profile().email)
                nextApp.warn_patient('open_survey')

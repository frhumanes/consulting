#!/usr/bin/python
# -*- encoding: utf-8 -*-
#
# author: fernando ruiz
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from stadistic.utils import *

class Command(BaseCommand):
    args = ''
    help = 'Delete pre-saved reports and rebuild the statistic database'

    def handle(self, *args, **options):
    	self.stdout.write('Loading reports...\n')
    	l = generate_reports(full=True)
    	self.stdout.write('%d reports loaded successfully.\n' % l)
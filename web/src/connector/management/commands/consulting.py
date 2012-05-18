# -*- encoding: utf-8 -*-

import logging
import sys
from django.core.management.base import BaseCommand
from datetime import datetime
from connector.tasks import remove_empty_treatments


class Command(BaseCommand):
    help = 'remove_empty_treatments'

    def setup_log(self):
        logging.basicConfig(level=logging.DEBUG,
                          format='%(asctime)s %(levelname)s %(message)s',
                          stream=sys.stdout)

    def handle(self, *args, **options):
        self.setup_log()
        logging.info(datetime.now().isoformat())
        logging.info("Fetching comments")
        logging.info("----------START HANDLE----------")
        remove_empty_treatments()
        logging.info("----------FINISH HANDLE----------")

# -*- encoding: utf-8 -*-
# from django.core.management.base import NoArgsCommand


# class Command(NoArgsCommand):
#     help = "Breve descripción de lo que hace el comando."

#     def handle_noargs(self, **options):
#         # aquí va el código de mi comando
#         print 'Comando ejecutado'
#!/usr/bin/python
# -*- encoding: utf-8 -*-
#
# author: javi santana


import logging
import sys

from django.core.management.base import BaseCommand
from datetime import datetime


from connector.tasks import remove_empty_treatments


class Command(BaseCommand):
    help = 'get comments from twitter and facebook'

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

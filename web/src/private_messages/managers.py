#! /usr/bin/python
# -*- encoding: utf-8 -*-

from django.db.models import Manager


class MessageManager(Manager):
    def get_outbox_for_user(self, user):
        """
        Get all messages sent from a certain user
        """
        return self.get_query_set().filter(author=user).order_by('-sent_at')

    def get_inbox_for_user(self, user):
        """
            Get all approved messages sent to a certain user
        """
        return self.get_query_set().filter(recipient=user).order_by('-sent_at')

# -*- encoding: utf-8 -*-

from django.db.models.signals import post_delete, post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db import models

from log.actions import log_addition
from log.actions import log_deletion
from log.actions import log_change


class TraceableModel(models.Model):
    created_by = models.ForeignKey(User, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


@receiver(post_save)
def post_save_handler(sender, instance, created, using, **kwargs):
    if isinstance(instance, TraceableModel):
        if created:
            log_addition(instance)
        else:
            log_change(instance)


@receiver(post_delete)
def post_delete_handler(sender, instance, using, **kwargs):
    if isinstance(instance, TraceableModel):
        try:
            log_deletion(instance)
        except:
            pass  # Catch exception when deleting users

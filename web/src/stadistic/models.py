from django.db import models
from django.utils.translation import ugettext_lazy as _
from djangotoolbox.fields import ListField, DictField
from userprofile.models import Profile
from consulting.models import Task

from django_mongodb_engine.contrib import MongoDBManager


class Report(models.Model):
    """task = models.ForeignKey(
        Task,
        related_name='task_reports',
        primary_key=True,
        on_delete=models.DO_NOTHING)
    patient = models.ForeignKey(
        Profile,
        related_name='patient_reports',
        on_delete=models.DO_NOTHING)"""
    task = models.IntegerField(null=False)
    patient = models.IntegerField(null=False)
    date = models.DateTimeField(_(u'Fecha del Informe'), null=True)
    sex = models.IntegerField(null=True)
    blocks = ListField()
    education = models.IntegerField(null=True)
    marital = models.IntegerField(null=True)
    profession = models.CharField(max_length=150)
    age = models.IntegerField(null=True)
    illnesses = ListField()
    treatment = ListField()
    variables = DictField()
    aves = ListField()
    dimensions = DictField()
    status = DictField()
    objects = MongoDBManager()

    class Meta:
        db_table = 'reports'
        managed = False

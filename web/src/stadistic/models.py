from django.db import models
from log.models import TraceableModel
from django.utils.translation import ugettext_lazy as _
from djangotoolbox.fields import ListField, DictField
from userprofile.models import Profile
from consulting.models import Task

class Report(TraceableModel):
    patient = models.ForeignKey(Profile, related_name='patient_reports')
    task = models.ForeignKey(Task, related_name='task_reports')
    date = models.DateTimeField(_(u'Fecha del Informe'), auto_now_add=True)
    variables = DictField()
    aves = ListField()
    dimensions = DictField()
    status = DictField()

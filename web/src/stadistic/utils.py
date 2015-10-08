# -*- encoding: utf-8 -*-
from consulting.models import Task
from stadistic.models import Report


def generate_reports(full=False):
    i = 0
    if full:
        Report.objects.all().delete()
    for task in Task.objects.filter(completed=True):
        try:
            report = Report.objects.get(task=task)
            if report.date == task.end_date:
                continue
        except:
            report = Report()
        profile = task.patient.get_profile()
        report.task = task.id
        report.blocks = [block.code for block in task.treated_blocks.all()]
        report.date = task.end_date
        report.created_by = task.created_by
        report.patient = profile.id
        age = profile.age_at(report.date)
        report.age = age and age or None
        report.sex = profile.sex
        report.education = profile.education
        report.marital = profile.status
        report.illnesses = [ill.code for ill in profile.illnesses.all()]
        report.treatment = [m.component.name for m in profile.get_treatment(report.date)]
        report.profession = profile.profession
        report.variables = dict((k.name, v) for (k, v) in task.get_variables_mark().items())
        report.dimensions = dict((k.name, v) for (k, v) in task.get_dimensions_mark().items())
        report.status = dict((level.scale.key, level.index()) for level in profile.get_medical_status(task.end_date))
        report.aves = task.get_ave_list()
        report.save()
        i += 1
    return i
from consulting.models import Task
from stadistic.models import Report

def generate_reports():
    for task in Task.objects.filter(completed=True):
        report = Report()
        report.task = task
        report.created_by = task.created_by
        report.patient = task.patient.get_profile()
        report.variables = { k.name: v for k, v in task.get_variables_mark().items()}
        report.dimensions = task.get_dimensions_mark(report.variables)
        report.status={'depression': task.get_depression_status()[0],
                       'anxiety': task.get_anxiety_status()[0]
                      }
        report.aves = task.get_ave_list()
        report.save()


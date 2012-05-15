# -*- encoding: utf-8 -*-
from consulting.models import Treatment


def remove_empty_treatments():
    treatments = Treatment.objects.all()
    for t in treatments:
        if t.medications.count() == 0:
            t.delete()

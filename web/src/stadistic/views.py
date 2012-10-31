# -*- encoding: utf-8 -*-
import xlwt
import cStringIO


from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Max
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from datetime import datetime

from decorators import paginate
from decorators import only_doctor_consulting

from stadistic.models import Report
from formula.models import Variable, Dimension
from userprofile.models import Profile
from stadistic.utils import  generate_reports

from stadistic.forms import FiltersForm

################################## STADISTICS #################################
@login_required()
@only_doctor_consulting
def stratification(request):
    dep_list = [[] for i in range(len(settings.BECK.keys()), 1, -1)]
    ans_list = [[] for i in range(len(settings.HAMILTON.keys()), 1, -1)]

    for p in Profile.objects.all():
        ans = p.get_anxiety_status(index=True)
        dep = p.get_depression_status(index=True)
        if ans:
            ans_list[ans-1].append(p)
        if dep:
            dep_list[dep-1].append(p)



    return render_to_response('consulting/stadistic/stratification.html', 
                              {'depression_list':dep_list, 
                               'anxiety_list':ans_list,
                               'num_patient':Profile.objects.filter(role=settings.PATIENT).count()},
                                context_instance=RequestContext(request))


def update_filter(dict_filters, key, value):
  option = ("$gte", "$lte", '$in')
  dv = None
  unpack = key.split('_')
  if len(unpack) == 2:
    name, op = unpack
  elif len(unpack) == 3:
    dv , name, op = unpack
    if not dv in dict_filters:
      dict_filters[dv] = {}
    orig_dict_filters = dict_filters
    dict_filters = dict_filters[dv]
  else:
    name = unpack[0]
    op = None
  if isinstance(value, list):
    op = 2

  option_filter = name.replace('-',' ')

  if not option_filter in dict_filters:
    dict_filters[option_filter] = {}
  if op:
    dict_filters[option_filter].update({ option[int(op)]: value})
  else:
    dict_filters.update({option_filter: value})

  if dv:
    orig_dict_filters[dv].update(dict_filters)
    dict_filters = orig_dict_filters

  return dict_filters

@login_required()
@only_doctor_consulting
def explotation(request):
    data = {}
    marks = {}
    form = FiltersForm()
    reports = []
    filters = {}
    if request.method == 'POST':
      form = FiltersForm(request.POST)
      for k, v in request.POST.items():
        if v:
          if k.startswith('date'):
            month, day, year  = v.split('/')
            filters = update_filter(filters, k, datetime(int(year), int(month), int(day)))
          if k.startswith('age'):
            filters = update_filter(filters, k, int(v))
          if k.startswith('profession'):
            filters = update_filter(filters, k, request.POST.getlist(k))
          if k.startswith('sex'):
            filters = update_filter(filters, k, [int(v) for v in request.POST.getlist(k)])
          if k.startswith('anxiety'):
            filters = update_filter(filters, 'status.Ansiedad', [int(v) for v in request.POST.getlist('anxiety')])
          if k.startswith('depression'):
            filters = update_filter(filters, 'status.Depresión', [int(v) for v in request.POST.getlist('depression')])
          if k.startswith('ave'):
            filters = update_filter(filters, k, [int(v) for v in request.POST.getlist(k)])
          if k.startswith('variables') or k.startswith('dimensions'):
            filters = update_filter(filters, k, int(v))

    reports = Report.objects.raw_query(filters)
    #raise Exception
    for r in reports:
        p = r.patient
        for var, mark in r.variables.items():
            if mark >= 0 and mark:
                if var in data.keys() and p.sex in data[var].keys():
                    data[var][p.sex].append(mark)
                elif var in data.keys():
                     data[var][p.sex] = [mark,]
                else:
                    data[var] = {p.sex:[mark,]}
    for varname, marks in data.items():
        for key, l in marks.items():
            if l:
                data[varname][key]=reduce(lambda x, y: x + y, l) / len(l)
            else:
                data[varname][key] = 0

    if request.GET.get('as', '') == 'xls':
      style_head = xlwt.easyxf('font: name Times New Roman, color-index black, bold on')
      style_value = xlwt.easyxf('font: name Times New Roman, color-index blue', num_format_str='#,##0.00')
      style_int = xlwt.easyxf('font: name Times New Roman, color-index green', num_format_str='#0')
      style_date = xlwt.easyxf(num_format_str='DD-MM-YYYY')

      wb = xlwt.Workbook(encoding='utf-8')
      ws = wb.add_sheet('Data')
      headers = [ 
                 ('age',_(u'Edad'), style_int), 
                 ('sex',_(u'Sexo'), style_int), 
                 ('profession',_(u'Profesión'), style_int), 
                 ('dimensions',[d.name for d in Dimension.objects.all()], style_value),
                 ('variables',[v.name for v in Variable.objects.all()], style_value),
                 ('status', [u'Ansiedad',u'Depresión'], style_int),
                 ('date',_(u'Fecha'), style_date), ]
      ws.write_merge(0, 0, 0, 2, 'Datos demográficos', style_head) 
      ws.write_merge(0, 0, 3, 4, 'Dimensiones', style_head) 
      ws.write_merge(0, 0, 5, 4+Variable.objects.all().count(), 'Variables', style_head) 
      ws.write_merge(0, 0, 5+Variable.objects.all().count(), 7+Variable.objects.all().count(), 'Estratificación', style_head) 
      r, c = 2, 0
      for report in reports:
        for key, name, style in headers:
          if isinstance(name, list):
            values = []
            for n in name:
              try:
                if key == 'status':
                  values.append((n, getattr(report, key)[n]))
                else:
                  values.append((n, getattr(report, key)[n]))
              except:
                values.append((n,''))
          else:
            if key == 'sex':
              values = [(name, report.patient.get_sex()), ]
            else:
              values = [(name, getattr(report, key)), ]
          for n, v in values:
            if r == 2:
              ws.write(1, c, n, style_head)
            ws.write(r, c, v, style)
            c += 1
        r += 1
        c = 0
      tmp_io = cStringIO.StringIO()
      wb.save(tmp_io)
      response = HttpResponse(tmp_io.getvalue(), content_type='application/vnd.ms-excel')
      tmp_io.close()
      response['Content-Disposition'] = 'attachment; filename="consulting30_data.xls"'
      return response

    else:
      return render_to_response('consulting/stadistic/explotation.html', 
                                {'data':data,
                                 'form' : form,
                                 'reports':list(reports),
                                 'variables':Variable.objects.all(),
                                 'dimensions':Dimension.objects.all(),
                                 'status':[u'Ansiedad',u'Depresión'],
                                 }, context_instance=RequestContext(request))

@login_required
@only_doctor_consulting
def regenerate_data(request):
    generate_reports()
    return HttpResponse('')

@login_required
@only_doctor_consulting
@paginate(template_name='consulting/patient/list.html',
    list_name='patients', objects_per_page=settings.OBJECTS_PER_PAGE)
def stratification_list(request, illness, level):
    patients = []
    for p in Profile.objects.all():
        if illness == 'anxiety' and p.get_anxiety_status(index=True) == int(level):
            patients.append(p)
        if illness == 'depression' and p.get_depression_status(index=True) == int(level):
            patients.append(p)

    template_data = dict(patients=patients,
                         context_instance=RequestContext(request))

    return template_data

        
# -*- encoding: utf-8 -*-
import xlwt
import cStringIO

from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.utils.html import strip_tags

from datetime import datetime

from decorators import paginate
from decorators import only_doctor_consulting

from stadistic.models import Report
from survey.models import Block, Survey
from formula.models import Variable, Dimension
from userprofile.models import Profile
from consulting.models import Task
from stadistic.utils import generate_reports

from stadistic.forms import FiltersForm

################################## STADISTICS #################################


@login_required()
@only_doctor_consulting
def stratification(request, option="AD"):
    piramid_list = {}
    task = Task()
    task.id = 1
    task.survey = Survey()
    scales = task.get_scales(exclude='')
    for scale in scales:
        piramid_list[scale['name']] = [
            [] for i in range(len(scale['scale']) + 1)
        ]

    filtered = request.GET.get('filter', '')
    if filtered == 'mine':
        patient_list = Profile.objects.filter(role=settings.PATIENT,
                                              doctor=request.user)
    else:
        patient_list = Profile.objects.filter(role=settings.PATIENT)
    for p in patient_list:
        for scale in scales:
            if not scale['scale']:
                scales.remove(scale)
                continue
            val = getattr(p, 'get_' + scale['hash'] + '_status')(index=True)
            if isinstance(val, int):
                piramid_list[scale['name']][val + 1].append(p)
            else:
                piramid_list[scale['name']][0].append(p)
    return render_to_response('statistic/stratification.html',
                              {'piramid_list': piramid_list,
                               'scales': scales,
                               'filtered': filtered,
                               'num_patient': patient_list.count()},
                              context_instance=RequestContext(request))


def update_filter(dict_filters, key, value):
    option = ("$gte", "$lte", '$in')
    dv = None
    unpack = key.split('_')
    if len(unpack) == 2:
        name, op = unpack
    elif len(unpack) == 3:
        dv, name, op = unpack
        if not dv in dict_filters:
            dict_filters[dv] = {}
        orig_dict_filters = dict_filters
        dict_filters = dict_filters[dv]
    else:
        name = unpack[0]
        op = None
    if key.startswith('\\'):
        name = key.replace('\\', '')
    if isinstance(value, list):
        op = 2

    option_filter = name.replace('-', ' ')

    if not option_filter in dict_filters:
        dict_filters[option_filter] = {}
    if op:
        dict_filters[option_filter].update({option[int(op)]: value})
    else:
        dict_filters.update({option_filter: value})

    if dv:
        orig_dict_filters[dv].update(dict_filters)
        dict_filters = orig_dict_filters

    return dict_filters


@login_required()
@only_doctor_consulting
def explotation(request, block_code=None):
    data, data2 = {}, {}
    data1 = {12: 0, 18: 0, 25: 0, 32: 0, 40: 0, 50: 0, 65: 0, '>65': 0}
    exclude = []
    marks = {}
    form = FiltersForm()
    filters = {}
    block = None
    variables = Variable.objects.all()
    dimensions = Dimension.objects.exclude(name='')
    status = []
    if block_code:
        if Block.objects.filter(code=block_code, is_scored=True).exists():
            block = Block.objects.filter(code=block_code, is_scored=True)[0]
            filters = {'blocks': {'$in': [int(block_code)]}}
        else:
            return HttpResponseRedirect(reverse('explotation_statistic'))

        variables = Variable.objects.filter(
            variables_categories__categories_blocks=block
        ).distinct().order_by('id')

    form = FiltersForm(block=block)

    if block_code == str(settings.ANXIETY_DEPRESSION_BLOCK):
        status = [u'Ansiedad', u'Depresión']
        data2 = {
            u'Ansiedad': [0 for i in range(len(settings.HAMILTON.keys()) + 1)],
            u'Depresión': [0 for i in range(len(settings.BECK.keys()) + 2)]
        }
        exclude = ('suicide', 'unhope', 'ybocs')
    elif block_code == str(settings.UNHOPE_BLOCK):
        status = [u'Desesperanza', u'Suicidio']
        data2 = {
            u'Suicidio': [0 for i in range(len(settings.SUICIDE.keys()) + 2)],
            u'Desesperanza': [
                0 for i in range(len(settings.UNHOPE.keys()) + 4)
            ],
        }
        exclude = ('anxiety', 'depression', 'aves', 'ybocs')
        dimensions = Dimension.objects.none()
        delattr(form, 'dimensions')
    elif block_code == str(settings.YBOCS_BLOCK):
        status = [u'Obsesión/Compulsión']
        data2 = {
            u'Obsesión/Compulsión': [
                0 for i in range(len(settings.Y_BOCS.keys()) + 2)
            ]
        }
        exclude = ('anxiety', 'depression', 'aves', 'suicide', 'unhope')
        dimensions = Dimension.objects.none()
        delattr(form, 'dimensions')
    else:
        exclude = ('anxiety', 'depression', 'aves',
                   'suicide', 'unhope', 'ybocs')
        status = []
        dimensions = Dimension.objects.none()
        delattr(form, 'dimensions')

    for exc in exclude:
        del form.fields[exc]

    reports = []

    group = True
    template_name = 'statistic/explotation.html'
    if request.method == 'POST':
        template_name = 'statistic/explotation-ajax.html'
        form = FiltersForm(request.POST)
        for k, v in request.POST.items():
            if v:
                if k.startswith('date'):
                    day, month, year = v.split('/')
                    filters = update_filter(
                        filters, k, datetime(int(year), int(month), int(day))
                    )
                if k.startswith('age'):
                    filters = update_filter(filters, k, int(v))
                if k.startswith('profession'):
                    filters = update_filter(
                        filters, k, request.POST.getlist(k)
                    )
                if k.startswith('sex'):
                    filters = update_filter(
                        filters, k, [int(v) for v in request.POST.getlist(k)]
                    )
                if k.startswith('marital'):
                    filters = update_filter(
                        filters, k, [int(v) for v in request.POST.getlist(k)]
                    )
                if k.startswith('education'):
                    filters = update_filter(
                        filters, k, [int(v) for v in request.POST.getlist(k)]
                    )
                if k.startswith('anxiety'):
                    filters = update_filter(
                        filters,
                        'status.Ansiedad',
                        [int(v) for v in request.POST.getlist('anxiety')]
                    )
                if k.startswith('depression'):
                    filters = update_filter(
                        filters,
                        'status.Depresión',
                        [int(v) for v in request.POST.getlist('depression')]
                    )
                if k.startswith('unhope'):
                    filters = update_filter(
                        filters,
                        'status.Desesperanza',
                        [int(v) for v in request.POST.getlist('unhope')]
                    )
                if k.startswith('suicide'):
                    filters = update_filter(
                        filters,
                        'status.Suicidio',
                        [int(v) for v in request.POST.getlist('suicide')]
                    )
                if k.startswith('ybocs'):
                    filters = update_filter(
                        filters,
                        'status.Obsesión/Compulsión',
                        [int(v) for v in request.POST.getlist('ybocs')]
                    )
                if k.startswith('treatment'):
                    filters = update_filter(
                        filters,
                        k,
                        [v for v in request.POST.getlist(k)]
                    )
                if k.startswith('illnesses'):
                    filters = update_filter(
                        filters,
                        k,
                        [v for v in request.POST.getlist(k)]
                    )
                if k.startswith('ave'):
                    filters = update_filter(
                        filters,
                        k,
                        [int(v) for v in request.POST.getlist(k)]
                    )
                if k.startswith('variables') or k.startswith('dimensions'):
                    filters = update_filter(filters, k, int(v))
                if k.startswith('options'):
                    for o in request.POST.getlist(k):
                        if o == 'filter':
                            lp = [i['id'] for i in Profile.objects.filter(doctor=request.user).values('id')]
                            filters = update_filter(filters, '\patient_id', lp)
                        if o == 'ungroup':
                            group = False
    reports = Report.objects.raw_query(filters)

    if group:
        for r in reports:
            try:
                #Check for deleted patients
                r.patient
            except:
                # Regenerate ALL the database
                return regenerate_data(request, True)
            if r.patient in data:
                if (not data[r.patient].date
                    or (r.date and
                        data[r.patient].date and
                        r.date > data[r.patient].date)):
                    data[r.patient].date = r.date
                for var, mark in r.variables.items():
                    if isinstance(mark, (int, long, float)):
                        if var in data[r.patient].variables:
                            data[r.patient].variables[var].append(mark)
                        else:
                            data[r.patient].variables[var] = [mark, ]
                for dim, mark in r.dimensions.items():
                    if isinstance(mark, (int, long, float)):
                        if dim in data[r.patient].dimensions:
                            data[r.patient].dimensions[dim].append(mark)
                        else:
                            data[r.patient].dimensions[dim] = [mark, ]
            else:
                data[r.patient] = r
                for var, mark in r.variables.items():
                    if isinstance(mark, (int, long, float)):
                        data[r.patient].variables[var] = [mark, ]
                    else:
                        data[r.patient].variables[var] = []
                for dim, mark in r.dimensions.items():
                    if isinstance(mark, (int, long, float)):
                        data[r.patient].dimensions[dim] = [mark, ]
                    else:
                        data[r.patient].dimensions[dim] = []
                if block_code == str(settings.ANXIETY_DEPRESSION_BLOCK):
                    data[r.patient].status[u'Ansiedad'] = r.patient.get_anxiety_status(index=True)
                    data[r.patient].status[u'Depresión'] = r.patient.get_depression_status(index=True)

        for p in data.keys():
            for key, l in data[p].variables.items():
                if l:
                    data[p].variables[key] = reduce(lambda x, y: x + y, l) / len(l)
                else:
                    data[p].variables[key] = ''
            for key, l in data[p].dimensions.items():
                if l:
                    data[p].dimensions[key] = reduce(lambda x, y: x + y, l) / len(l)
                else:
                    data[p].dimensions[key] = ''
        reports = data.values()
        data = {}


    if status:
        reports = sorted(reports, key=lambda report: -((report.status[u'Ansiedad'] and int(report.status[u'Ansiedad']) or -1) + (report.status[u'Depresión'] and int(report.status[u'Depresión']) or -1)))
    else:
        reports = sorted(reports, key=lambda report: report.date)

    if request.GET.get('as', '') == 'xls':
        style_head = xlwt.easyxf('font: name Times New Roman, \
                                 color-index black, bold on')
        style_value = xlwt.easyxf('font: name Times New Roman, \
                                  color-index blue', num_format_str='#,##0.00')
        style_int = xlwt.easyxf('font: name Times New Roman, \
                                color-index green', num_format_str='#0')
        style_date = xlwt.easyxf(num_format_str='DD-MM-YYYY')

        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Data')
        headers = [('age', _(u'Edad'), style_int),
                   ('sex', _(u'Sexo'), style_int),
                   ('education', _(u'Estudios'), style_int),
                   ('profession', _(u'Profesión'), style_int),
                   ('dimensions', [d.name for d in dimensions], style_value),
                   ('variables', [v.name for v in variables], style_value),
                   ('status', status, style_int),
                   ('date', (group
                             and _(u'Episodio más reciente')
                             or _(u'Fecha')), style_date)]
        ws.write_merge(0, 0, 0, 3, _(u'Datos demográficos'), style_head)
        offset = 4
        if dimensions.count():
            offset += dimensions.count()
            ws.write_merge(0, 0, 4, offset - 1, _(u'Dimensiones'), style_head)
        ws.write_merge(0, 0, offset, offset + variables.count() - 1,
                       _(u'Variables'), style_head)
        offset += variables.count()
        if len(status):
            ws.write_merge(0, 0, offset, offset + len(status),
                           _(u'Estratificación'), style_head)
        r, c = 2, 0
        for report in reports:
            for key, name, style in headers:
                if isinstance(name, list):
                    values = []
                    for n in name:
                        try:
                            if key == 'status':
                                st = ''
                                nst = getattr(report, key)[n]
                                if n == u'Ansiedad':
                                    st = [settings.HAMILTON[k][0] for k in sorted(settings.HAMILTON.keys())][nst]
                                elif n == u'Depresión':
                                    st = [settings.BECK[k][0] for k in sorted(settings.BECK.keys())][nst]
                                elif n == u'Desesperanza':
                                    st = [settings.UNHOPE[k][0] for k in sorted(settings.UNHOPE.keys())][nst]
                                elif n == u'Obsesión/Compulsión':
                                    st = [settings.Y_BOCS[k][0] for k in sorted(settings.Y_BOCS.keys())][nst]
                                elif n == u'Suicidio':
                                    st = [settings.SUICIDE[k][0] for k in sorted(settings.SUICIDE.keys())][nst]
                                values.append((n, strip_tags(st)))
                            else:
                                values.append((n, getattr(report, key)[n]))
                        except:
                            values.append((n, ''))
                else:
                    if key == 'sex':
                        values = [(name, report.patient.get_sex()), ]
                    elif key == 'education':
                        values = [(name, report.patient.get_education()), ]
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
        response = HttpResponse(tmp_io.getvalue(),
                                content_type='application/vnd.ms-excel')
        tmp_io.close()
        response['Content-Disposition'] = 'attachment; \
                filename="consulting30_data.xls"'
        return response

    else:
        #### Pyramids ####
        for r in reports:
            p = r.patient
            for var, mark in r.variables.items():
                if mark >= 0 and mark:
                    if var in data.keys() and p.sex in data[var].keys():
                        data[var][p.sex].append(mark)
                    elif var in data.keys():
                        data[var][p.sex] = [mark, ]
                    else:
                        data[var] = {p.sex: [mark, ]}
            found = False
            for age in sorted(data1.keys())[:-1]:
                if r.age <= age:
                    data1[age] += 1
                    found = True
                    break
            if not found:
                data1['>65'] += 1
            if data2:
                for k in status:
                    v = r.status[k]
                    if not isinstance(v, int):
                        v = 0
                    else:
                        if v > 0:
                            #Fix Offsets for scales shorter than Beck
                            if k == u"Desesperanza":
                                v += 3
                            elif k in [u"Ansiedad",
                                       u"Suicidio",
                                       u"Obsesión/Compulsión"]:
                                v += 1
                        v += 1
                    data2[k][v] += 1

        for varname, marks in data.items():
            for key, l in marks.items():
                if l:
                    data[varname][key] = reduce(lambda x, y: x + y, l) / len(l)
                else:
                    data[varname][key] = 0
        prev = None
        for age in sorted(data1.keys()):
            if prev and isinstance(age, int):
                label = "%d-%d" % (prev, age)
                data1[label] = data1[age]
                data1.pop(age)
            prev = age

        return render_to_response(template_name,
                                  {'data': data,
                                   'data1': data1,
                                   'data2': data2,
                                   'labels_for_data1': sorted(data1.keys()),
                                   'survey_block': block,
                                   'group': group,
                                   'form': form,
                                   'reports': list(reports),
                                   'variables': variables,
                                   'dimensions': dimensions,
                                   'status': status},
                                  context_instance=RequestContext(request))


@login_required
@only_doctor_consulting
def regenerate_data(request, full=False):
    generate_reports(full)
    if full:
        return HttpResponseRedirect(reverse('explotation_statistic'))
    else:
        return HttpResponse('')


@login_required
@only_doctor_consulting
@paginate(template_name='consulting/patient/list.html',
          list_name='patients', objects_per_page=settings.OBJECTS_PER_PAGE)
def stratification_list(request, illness, level):
    patients = []

    filtered = request.GET.get('filter', '')
    if int(level) < 0:
        level = ''
    else:
        level = int(level)
    if filtered == 'mine':
        patient_list = Profile.objects.filter(role=settings.PATIENT,
                                              doctor=request.user)
    else:
        patient_list = Profile.objects.filter(role=settings.PATIENT)
    if callable(getattr(request.user.get_profile(),
                        'get_' + illness + '_status')):
        for p in patient_list:
            if getattr(p, 'get_' + illness + '_status')(index=True) == level:
                patients.append(p)

    template_data = dict(patients=patients,
                         context_instance=RequestContext(request))

    return template_data


@login_required
@only_doctor_consulting
def stratification_label(request, illness, level):
    if illness == 'anxiety':
        scale = settings.HAMILTON
    elif illness == 'depression':
        scale = settings.BECK
    elif illness == 'unhope':
        scale = settings.UNHOPE
    elif illness == 'suicide':
        scale = settings.SUICIDE
    elif illness == 'ybocs':
        scale = settings.Y_BOCS

    try:
        scale[0] = (_(u'No diagnosticados'), '')
        pkeys = scale.keys()
        pkeys.sort()
        return HttpResponse(strip_tags(scale[pkeys[int(level) + 1]][0]))
    except:
        return HttpResponse('')

from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Max
from django.core.urlresolvers import reverse

from stadistic.models import Report
from formula.models import Variable, Dimension
from userprofile.models import Profile
from stadistic.utils import  generate_reports

################################## STADISTICS #################################
@login_required()
def stratification(request):
    logged_user_profile = request.user.get_profile()
    if not logged_user_profile.is_doctor():
        return HttpResponseRedirect(reverse('consulting_index'))

    if logged_user_profile.is_doctor():
    	dep_list = [[] for i in range(len(settings.BECK.keys()), 1, -1)]
    	ans_list = [[] for i in range(len(settings.HAMILTON.keys()), 1, -1)]

    	for p in Profile.objects.all():
    		ans = p.get_anxiety_status(True)
    		dep = p.get_depression_status(True)
    		if ans:
    			ans_list[ans-1].append(p)
    		if dep:
    			dep_list[dep-1].append(p)


        return render_to_response('consulting/stadistic/stratification.html', 
        						  {'depression_list':dep_list, 
        						   'anxiety_list':ans_list,
        						   'num_patient':Profile.objects.filter(role=settings.PATIENT).count()},
                            	context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))

@login_required()
def explotation(request):
    logged_user_profile = request.user.get_profile()
    if not logged_user_profile.is_doctor():
        return HttpResponseRedirect(reverse('consulting_index'))
    data = {}
    marks = {}
    for r in Report.objects.all():
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
    return render_to_response('consulting/stadistic/explotation.html', 
                                {'data':data,
                                 'reports':list(Report.objects.all()),
                                 'variables':Variable.objects.filter(),
                                 'dimensions':Dimension.objects.all(),
                                 'status':r.status.keys(),
                                 }, context_instance=RequestContext(request))

@login_required
def regenerate_data(request):
	generate_reports()
	return HttpResponse('')
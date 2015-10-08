# Create your views here.
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.middleware.csrf import get_token
from django.conf import settings

from decorators import *

from survey.models import Survey

@login_required
@only_doctor_consulting
@paginate(template_name='survey/index.html',
          list_name='surveys', objects_per_page=settings.OBJECTS_PER_PAGE)
def index(request):
    surveys = Survey.objects.all()
    template_data = {}
    template_data.update({'surveys': surveys,
                          'csrf_token': get_token(request)})
    return template_data


@login_required
@only_doctor_consulting
def view(request, id_survey):
    survey = get_object_or_404(Survey, id=id_survey)
    return render_to_response('survey/view.html', {'survey': survey},
                                  context_instance=RequestContext(request))

    

# -*- encoding: utf-8 -*-

from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from datetime import datetime

from models import Message
from forms import MessageForm, ReplyMessageForm

import conf
from decorators import paginate


@login_required
@paginate(template_name='private_messages/message_list.html',
    list_name='messages', objects_per_page=conf.OBJECTS_PER_PAGE)
def outbox(request):
    """
    List messages sent from an user
    """
    template_data = {}
    messages = Message.objects.get_outbox_for_user(request.user)
    template_data.update({'messages': messages})

    return template_data


@login_required
@paginate(template_name='private_messages/message_list.html',
    list_name='messages', objects_per_page=conf.OBJECTS_PER_PAGE)
def inbox(request):
    """
    List messages sent to an user
    """
    template_data = {}
    messages = Message.objects.get_inbox_for_user(request.user)
    template_data.update({'messages': messages})

    return template_data


@login_required
def create_message(request):
    """
    Create a new message
    """
    if request.method == 'POST':
        form = MessageForm(request.POST, user=request.user)

        if form.is_valid():
            message = form.save(commit=False)
            message.author = request.user
            message.sent_at = datetime.now()
            message.save()
            return redirect(reverse("private_messages_inbox"))

    else:
        form = MessageForm(user=request.user)

    return render_to_response("private_messages/message_new.html",
                {"form": form}, context_instance=RequestContext(request))


@login_required
def view_message(request, id):
    """
    View a message
    """
    message_to_view = get_object_or_404(Message, pk=int(id))
    message_to_view.unread = False
    message_to_view.save()
    return render_to_response("private_messages/message_view.html",
        {"message": message_to_view}, context_instance=RequestContext(request))


@login_required
def reply_message(request, message_id):
    """
    Reply a mesage
    """
    message_to_reply = get_object_or_404(Message, pk=int(message_id))
    message_to_reply.subject = 'Re: ' + message_to_reply.subject
    message_to_reply.body = ' \n------ \n' + message_to_reply.body
    form = MessageForm(user=request.user,
        instance=message_to_reply,
        initial={'recipient': message_to_reply.author})

    return render_to_response("private_messages/message_reply.html",
                {"form": form}, context_instance=RequestContext(request))
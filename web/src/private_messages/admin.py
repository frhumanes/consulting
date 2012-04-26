from django.contrib import admin
from private_messages.models import *


class MessageAdmin(admin.ModelAdmin):
    fieldsets = [('Message', {'fields': ['author', 'recipient', 'parent',
                'subject', 'body', 'unread', 'sent_at']})]
    list_display = ('author', 'recipient', 'parent',
                'subject', 'body', 'unread', 'sent_at')
    search_fields = ('author', 'recipient', 'parent',
                'subject', 'body', 'unread', 'sent_at')
    ordering = ('author', 'recipient', 'parent',
                'subject', 'body', 'unread', 'sent_at')

admin.site.register(Message, MessageAdmin)

from django.contrib import admin
from django.utils.translation import ugettext as _
from private_messages.models import *


class MessageAdmin(admin.ModelAdmin):
    fieldsets = [
    			('De', {
    				'fields': ['author' ]
    			}),
    			('Para',{
    				'fields': ['recipient']
    			}),
    			('Mensaje', {
                	'fields': ['subject', 'body']
                }),
                ('Estado', {
                	'fields': ['unread', 'sent_at']
                }), 
    			]
    list_display = ('author', 'recipient', 
                'subject', 'unread', 'sent_at')
    list_filter = ['author', 'recipient', 'unread', 'sent_at' ]
    search_fields = ('subject', 'body',)
    ordering = ('-sent_at',)

admin.site.register(Message, MessageAdmin)

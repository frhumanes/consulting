from django.contrib import admin
from illness.models import *


class IllnessAdmin(admin.ModelAdmin):
    fieldsets = [('Illnesses', {'fields': ['code', 'name', 'surveys']})]
    list_display = ('code', 'name')
    search_fields = ('code', 'name')
    ordering = ('code', )

admin.site.register(Illness, IllnessAdmin)

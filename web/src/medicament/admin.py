from django.contrib import admin
from medicament.models import *


class GroupAdmin(admin.ModelAdmin):
    fieldsets = [('Groups', {'fields': ['name', 'adverse_reaction']})]
    list_display = ('name', 'adverse_reaction')
    search_fields = ('name', 'adverse_reaction')
    ordering = ('name',)

admin.site.register(Group, GroupAdmin)


class ComponentAdmin(admin.ModelAdmin):
    fieldsets = [('Components', {'fields':
                ['kind_component', 'name', 'groups']})]
    list_display = ('kind_component', 'name',)
    search_fields = ('kind_component', 'name',)
    ordering = ('kind_component', 'name',)

admin.site.register(Component, ComponentAdmin)

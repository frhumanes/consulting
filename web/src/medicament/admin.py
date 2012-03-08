from django.contrib import admin
from medicament.models import *


class GroupAdmin(admin.ModelAdmin):
    fieldsets = [('Groups', {'fields': ['name', 'adverse_reaction']})]
    list_display = ('name', 'adverse_reaction')
    search_fields = ('name', 'adverse_reaction')
    ordering = ('name',)

admin.site.register(Group, GroupAdmin)


class MedicineAdmin(admin.ModelAdmin):
    fieldsets = [('Medicines', {'fields': ['group', 'name',
                'active_ingredient']})]
    list_display = ('group', 'name', 'active_ingredient')
    search_fields = ('group', 'name', 'active_ingredient')
    ordering = ('group', 'name', 'active_ingredient')

admin.site.register(Medicine, MedicineAdmin)

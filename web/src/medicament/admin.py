from django.contrib import admin
from medicament.models import *


class GroupAdmin(admin.ModelAdmin):
    fieldsets = [('Groups', {'fields': ['name', 'adverse_reaction']})]
    list_display = ('name', 'adverse_reaction')
    search_fields = ('name', 'adverse_reaction')
    ordering = ('name',)

admin.site.register(Group, GroupAdmin)


class ActiveIngredientAdmin(admin.ModelAdmin):
    fieldsets = [('ActiveIngredients', {'fields': ['name']})]
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

admin.site.register(ActiveIngredient, ActiveIngredientAdmin)


class MedicineAdmin(admin.ModelAdmin):
    fieldsets = [('Medicines', {'fields': ['group', 'name',
                                'active_ingredients']})]
    list_display = ('name', 'group')
    search_fields = ('group', 'name')
    ordering = ('group', 'name')

admin.site.register(Medicine, MedicineAdmin)

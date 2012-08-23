from django.contrib import admin
from survey.models import *


class SurveyAdmin(admin.ModelAdmin):
    fieldsets = [('Surveys', {'fields': ['name', 'code', 'blocks', 'kind']})]
    list_display = ('code', 'name', 'kind')
    search_fields = ('code', 'name', 'kind')
    ordering = ('code', 'name', 'kind')

admin.site.register(Survey, SurveyAdmin)


class CategoryAdmin(admin.ModelAdmin):
    fieldsets = [('Categorys', {'fields': ['name', 'code', 'kind',
                                            'questions']})]
    list_display = ('code', 'name', 'kind')
    search_fields = ('code', 'name', 'kind')
    ordering = ('code', 'name', 'kind')

admin.site.register(Category, CategoryAdmin)


class BlockAdmin(admin.ModelAdmin):
    fieldsets = [('Blocks', {'fields': ['name', 'code', 'kind',
                'categories', 'formulas']})]
    list_display = ('code', 'name', 'kind')
    search_fields = ('code', 'name', 'kind')
    ordering = ('code', 'kind')

admin.site.register(Block, BlockAdmin)


class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [('Questions', {'fields': ['text', 'code']})]
    list_display = ('code', 'text')
    search_fields = ('code', 'text')
    ordering = ('code',)

admin.site.register(Question, QuestionAdmin)


class OptionAdmin(admin.ModelAdmin):
    fieldsets = [('Options', {'fields': ['text', 'code', 'kind', 'weight',
                'question']})]
    list_display = ('code', 'text', 'weight', 'kind', 'question')
    search_fields = ('code', 'text', 'kind', 'weight', 'kind', 'question')
    ordering = ('code',)

admin.site.register(Option, OptionAdmin)

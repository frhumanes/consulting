from django import template
from django.conf import settings

register = template.Library()


@register.filter
def name_with_title(value):
	return value.get_full_name(title=True)
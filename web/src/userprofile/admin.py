from django.contrib import admin
from userprofile.models import Profile


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'first_surname', 'second_surname', 'sex',
                    'address', 'town', 'postcode', 'dob', 'status',
                    'profession', 'is_doctor')
    search_fields = ('user', 'name', 'first_surname', 'second_surname', 'sex',
                    'address', 'town', 'postcode', 'dob', 'status',
                    'profession', 'is_doctor')
    ordering = ('user',)

admin.site.register(Profile, ProfileAdmin)

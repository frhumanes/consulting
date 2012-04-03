from django.contrib import admin
from userprofile.models import Profile


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'doctor', 'name', 'first_surname',
                    'second_surname', 'sex', 'address', 'town', 'postcode',
                    'dob', 'status', 'phone1', 'phone2', 'profession', 'role')
    search_fields = ('user', 'doctor', 'name', 'first_surname',
                    'second_surname', 'sex', 'address', 'town', 'postcode',
                    'dob', 'status', 'phone1', 'phone2', 'profession', 'role')
    ordering = ('user', 'role')

admin.site.register(Profile, ProfileAdmin)

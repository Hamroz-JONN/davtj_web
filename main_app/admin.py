from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import ExtendedUser
from django import forms
# Register your models here.

class ExtendedUserAdminForm(forms.ModelForm):
    class Meta:
        model = ExtendedUser
        fields = ["strava_id"]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['strava_id'].widget.attrs.update({
            'style': 'width: 300px;',
        })

class ExtendedUserInLine(admin.StackedInline):
    model = ExtendedUser
    form = ExtendedUserAdminForm
    can_delete = False


# Define a new User admin
class CustomUserAdmin(BaseUserAdmin):
    inlines = [ExtendedUserInLine]

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
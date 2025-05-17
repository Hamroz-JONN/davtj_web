from django import forms
from django.contrib.auth.models import User
from .models import ExtendedUser

class UserRegistrationForm(forms.ModelForm):
    password_retry = forms.CharField(max_length=30, widget=forms.PasswordInput(attrs={
        'rows': 1,
        'cols': 40,
        'style': 'font-size: 13px;'  
    }))
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']
        # fields = "__all__"
        help_texts = {'username': None}
        
        widgets = {
            'first_name': forms.TextInput(attrs={'style': 'font-size: 15px;'}),
            'last_name': forms.TextInput(attrs={'style': 'font-size: 15px;'}),
            'username': forms.TextInput(attrs={'style': 'font-size: 13px;'}),
            'email': forms.EmailInput(attrs={'style': 'font-size: 13px;'}),
            'password': forms.PasswordInput(attrs={'style': 'font-size: 13px;'}),
        }
        
class ExtendedUserRegistrationForm(forms.Form):
    strava_account_link = forms.URLField(required=True, help_text="Go to Strava > Profile > Share and copy the link here", widget=forms.TextInput(attrs={
        'style': 'font-size: 13px;', 
        'cols':40
    }))
        
class UserSigninForm(forms.Form):
    username = forms.CharField(max_length=100)
    # password = forms.CharField(max_length=100, widget=forms.PasswordInput)
    password = forms.CharField(max_length=100)

class StatsChartForm(forms.Form):
    field_choices = [
        ('pace', 'Pace (km/minute)'),
        ('distance', 'Distance (km)'),
        ('activity_date', 'Activity Date'),
        ('active_time', 'Activity Time'),
        ('elevation_gain', 'Elevation Gain'),
    ]
    
    field_types = [
        ('quantitative', 'Numeric'),
        ('quantitative-bin', 'Numeric, binned'),
        ('temporal', 'Date/Time'),
        ('temporal-bin', 'Date/Time, binned'),
        ('ordinal', 'Label'),
        ('nominal', 'Category'),
    ]
    
    graph_types = [
        ('bar', 'Bar'),
        ('line', 'Line'),
        ('circle', 'Scatter (dots)'),   
    ]
    
    swap_fields = [
        ('')
    ]
    
    graph_type = forms.ChoiceField(choices=graph_types)
    swap_fields = forms.BooleanField(initial=False, required=False, label='Swap X and Y fields')
    field_X = forms.ChoiceField(choices=field_choices)
    field_X_type = forms.ChoiceField(choices=field_types)
    field_Y = forms.ChoiceField(choices=field_choices)
    field_Y_type = forms.ChoiceField(choices=field_types)
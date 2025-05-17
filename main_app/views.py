from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.forms.models import model_to_dict
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

from .forms import *
from .tokens import account_activation_token
from .decorators import *
from .models import *
from .tasks import scrape_graph

import requests
import bs4 as BeautifulSoup
import re
import time
import logging
from datetime import datetime
from celery import shared_task

# user has received activation link in email, and clicked in it. here we will activate their account (they'll be able to login)
def activateAccount(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None
        
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()

        messages.success(request, "Thank you for your email confirmation. Now you can login your account.")
        return redirect('signin')
    else:
        messages.error(request, "Activation link is invalid!")

    return redirect('index')

def sendConfirmationEmail(request, user:User):
    user_email = user.email
    subject = "DAV.TJ Confirmation Email"
    
    message = render_to_string("main_app/utilities/email_confirmation.html", {
        'user': user.username,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        "protocol": 'https' if request.is_secure() else 'http'
    })
    
    email = EmailMessage(subject, message, to=[user_email])
    if email.send():
        messages.success(request, f"A Confirmation Email will be sent to {user_email}. Please activate your account through it. (Check your Spam folder too)")
    else:
        messages.error(request, f"Couldn't send email to {user_email}. Please check you typed it correctly and you have connection to internet.")

def index(request):
    print("here")
    def build_graph_link(strava_id, chart_form):
        field_type = {
            'pace': 'quantitative',
            'distance': 'quantitative',
            'elevation_gain': 'quantitative',
            'activity_date':'temporal',
            'active_time':'temporal'
        }
        
        gmark = chart_form.cleaned_data['graph_type']
        gx_column = chart_form.cleaned_data['field_X']
        gx_type = chart_form.cleaned_data['field_X_type']
        gy_column = chart_form.cleaned_data['field_Y']
        gy_type = chart_form.cleaned_data['field_Y_type']
        
        if chart_form.cleaned_data['swap_fields'] is True:
            gx_column, gy_column = gy_column, gx_column
            gx_type, gy_type = gy_type, gx_type
        
        
        return f"https://strava.dav.tj:8002/strava/v_activity?pace__lt=10&athlete_id__exact={strava_id}&distance__gte=3#g.mark={gmark}&g.x_column={gx_column}&g.x_type={gx_type}&g.y_column={gy_column}&g.y_type={gy_type}"

    if request.user.is_authenticated:
        graph_path = None
        if request.method == "POST":
            chart_form = StatsChartForm(request.POST)
            
            if chart_form.is_valid():
                graph_link = build_graph_link(request.user.extendeduser.strava_id, chart_form)
                print("LINK", graph_link)
                
                graph_path = scrape_graph.delay(graph_link)
                try:
                    graph_path = graph_path.get(timeout=20)
                except Exception as e:
                    print(f"❌Cant load the chart\n\n{e}")
                    messages.error(request, "Cant load the chart: Timeout.")
                
                graph_path = graph_path.split('media', 1)[1] # cut off the part before /media (required for linking image in html)
        elif request.method == "GET":
            chart_form = StatsChartForm()
        return render(request, 'main_app/profile.html', {
            'form':chart_form,
            'MEDIA_URL': settings.MEDIA_URL,
            'graph_path': graph_path
        })
    else:
        return render(request, 'main_app/index.html')

@user_not_authenticated
def signup(request):
    def refill_form():
        messages.error(request, "Please fix above errors to complete the registration. Thank you.")
        return render(request, 'main_app/signup.html', {
            "form": reg_form,
            "ext_form":ext_reg_form
        })
    
    if request.method == "POST":
        reg_form = UserRegistrationForm(request.POST)
        ext_reg_form = ExtendedUserRegistrationForm(request.POST)

        if reg_form.is_valid() and ext_reg_form.is_valid():
            # validate passwords
            if reg_form.data['password'] != reg_form.data['password_retry']:
                reg_form.add_error('password_retry', 'Your passwords dont match!')
                
            username:str = reg_form.cleaned_data['username']
            email:str = reg_form.cleaned_data['email']
            
            # check if email is unique
            if User.objects.filter(email=email).exists():
                messages.error(request, f"Your Email is already registered. You can Sign In here.")
                return redirect('signin') 
            
            # check if username is unique
            if User.objects.filter(username=username).exists():
                reg_form.add_error('username', 'Such Username already exists. Please use different one.')

            # check if username is unique
            if not username.replace('-', '').replace('_', '').isalnum():
                reg_form.add_error('username', 'Username should contain letters, numbers, dashes(-) and underscore(_).')
            
            # validate strava id
            strava_link = ext_reg_form.cleaned_data['strava_account_link']
            
            fin_url = requests.get(strava_link, headers=
                            {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel  Mac OS  X 10_15_7) AppleWebKit/605.1.15  (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15'}).url
            
            strava_id = re.findall(r'\d+', fin_url)
            strava_id = int(strava_id[0])
            
            if ExtendedUser.objects.filter(strava_id=strava_id).exists():
                ext_reg_form.add_error('strava_account_link', 'Strava account is already claimed by someone else. If you believe this account is yours, please contact the Admin.')

            if reg_form.errors or ext_reg_form.errors:
                return refill_form()
                
            user:User = reg_form.save(commit=False)
            user.set_password(reg_form.cleaned_data['password'])
            user.is_active = False
            user.save()

            ext_user = ExtendedUser.objects.create(user=user, strava_id=strava_id)
            
            sendConfirmationEmail(request, user)
            
            messages.success(request, f"Your account has been successfully created.")    
            return redirect('signin') 
        else: # if vorm isnt valid
            return refill_form()
    elif request.method == "GET":
        reg_form = UserRegistrationForm()
        ext_reg_form = ExtendedUserRegistrationForm()
        return render(request, 'main_app/signup.html', {
            "form": reg_form,
            "ext_form":ext_reg_form
        })
    else:
        return HttpResponse("❌Only GET and POST are supported.")
    
@user_not_authenticated
def signin(request):
    if(request.method == "POST"):
        userSignin = UserSigninForm(request.POST) 

        # dont use request.POST, use form.cleaned_data instead

        if userSignin.is_valid():
            print("u:", userSignin.cleaned_data['username']) 
            print("p:", userSignin.cleaned_data['password']) 
            user = authenticate(username = userSignin.cleaned_data['username'], password = userSignin.cleaned_data['password'])
            if user != None:
                print("User found")

                login(request, user)

                request.session['user'] = user.id
                request.session['isAdmin'] = user.username == '__Admin'

                return redirect("index")
            else:
                messages.error(request, "Incorrect Username or Password")
                pass

    userSignin = UserSigninForm()
    return render(request, "main_app/signin.html", {
        "form" : userSignin
    })

@login_required
def signout(request):
    name = request.user.username
    logout(request)
    messages.success(request, f"Good Bye {name}. Looking forward to see you again")
    return redirect('index')

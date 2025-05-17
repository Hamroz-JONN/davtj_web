from django.urls import path
from django.shortcuts import redirect

from . import views

urlpatterns = [
    path('index/', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('activate/<uidb64>/<token>/', views.activateAccount, name='activate'),
    path('signin/', views.signin, name='signin'),
    path('signout/', views.signout, name='signout'),
    
    path('', lambda request: redirect('index')),
]
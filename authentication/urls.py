# authentication/urls.py
from django.urls import path
from . import views   # our own views, not Django's built-in ones

app_name = 'authentication'   # makes 'authentication:login' work

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
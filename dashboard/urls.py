from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('teacher', views.teacher_dashboard, name='teacher'),#name='teacher is a nickname which is use to call the view function in the template file using {% url 'dashboard:teacher' %}
    path('admin-panel/', views.admin_home, name='admin_home'),
    path('admin-panel/resources/', views.resources, name='resources'),
    path('admin-panel/schedules/', views.schedules, name='schedules'),
    path('admin-panel/inventory/', views.inventory, name='inventory'),
]
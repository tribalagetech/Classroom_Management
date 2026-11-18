# students/urls.py  (create this file)
from django.urls import path
from . import views
from django.views.generic import RedirectView

app_name = 'students'

urlpatterns = [
    path('subjects/', views.subject_manage, name='subjects'),
    path('subjects/<int:pk>/delete/', views.subject_delete, name='subject_delete'),
    path('', RedirectView.as_view(pattern_name='students:register'), name='index'),
    path('register/', views.student_register, name='register'),
    path('subjects/', views.subject_manage, name='subjects'),
    path('subjects/<int:pk>/delete/', views.subject_delete, name='subject_delete'),

    path('subjects/<int:pk>/edit/', views.subject_edit, name='subject_edit'),
    path('classes/', views.class_manage, name='classes'),
    path('classes/<int:pk>/edit/', views.class_manage, name='class_edit'),
    path('classes/<int:pk>/delete/', views.class_delete, name='class_delete'),

]
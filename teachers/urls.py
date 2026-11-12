# teachers/urls.py  (create this file)
from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    path('', views.teacher_list, name='list'),
    path('register/', views.register_teacher, name='register'),
    # <int:pk> captures the teacher's id from the URL and passes it to the view
    path('<int:pk>/create-credentials/', views.create_credentials, name='create_credentials'),
]
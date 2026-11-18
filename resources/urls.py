from django.urls import path
from . import views

app_name = 'resources'

urlpatterns = [
    path('', views.centre, name='centre'),
    path('<int:pk>/download/', views.download, name='download'),
    path('<int:pk>/publish/', views.toggle_publish, name='toggle_publish'),
    path('<int:pk>/delete/', views.delete, name='delete'),
]
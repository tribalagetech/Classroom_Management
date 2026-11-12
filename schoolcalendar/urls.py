# schoolcalendar/urls.py  (new file)
from django.urls import path
from . import views

app_name = 'schoolcalendar'

urlpatterns = [
    path('', views.month_view, name='month'),                                   # current month
    path('<int:year>/<int:month>/', views.month_view, name='month_ym'),
    path('event/add/', views.event_create, name='event_add'),
    path('event/<int:pk>/edit/', views.event_edit, name='event_edit'),
    path('event/<int:pk>/delete/', views.event_delete, name='event_delete'),
    path('term/save/', views.term_save, name='term_save'),
    path('event/quick-add/', views.event_quick_add, name='event_quick_add'),
]
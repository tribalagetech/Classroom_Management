# classroom_management/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # root URL (/) forwards to the login page, using the route name instead of a hardcoded path
    path('', RedirectView.as_view(pattern_name='authentication:login')),

    # login/ and logout/ live in the authentication app now
    path('', include('authentication.urls')),

    path('dashboard/', include('dashboard.urls')),
    path('teachers/', include('teachers.urls')),

    # student/urls.py  (add one line to urlpatterns)
    path('students/', include('students.urls')),
    
    path('calendar/', include('schoolcalendar.urls')),

    # classroom_management/urls.py (add one line to urlpatterns)
    path('resources/', include('resources.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)   # dev only
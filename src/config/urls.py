from django.contrib import admin
from django.urls import include, path

from api import api as api_root
from teachers import views as teachers_views

urlpatterns = [
    path('', teachers_views.HomeRedirectView.as_view(), name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('teacher/', include('teachers.urls')),
    path('api/', api_root.api.urls),
]

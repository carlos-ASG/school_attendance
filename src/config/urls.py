from django.conf import settings
from django.conf.urls.static import static
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

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.contrib import admin
from django.urls import include, path

from school import views as school_views

urlpatterns = [
    path('', school_views.HomeRedirectView.as_view(), name='home'),
    path('admin/', admin.site.urls),
    path('panel/', include('school.urls')),
]

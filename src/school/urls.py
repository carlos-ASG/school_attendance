from django.urls import path

from . import views

app_name = 'school'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('classrooms/<int:pk>/', views.ClassroomDetailView.as_view(), name='classroom_detail'),
    path('sessions/<int:pk>/', views.SessionDetailView.as_view(), name='session_detail'),
]

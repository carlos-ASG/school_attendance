from django.urls import path

from . import views

app_name = 'teachers'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('courses/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('courses/<int:pk>/history/', views.CourseSessionHistoryView.as_view(), name='course_session_history'),
    path('sessions/<int:pk>/', views.SessionDetailView.as_view(), name='session_detail'),
    path('sessions/<int:pk>/edit/', views.SessionUpdateView.as_view(), name='session_edit'),
    path('sessions/<int:pk>/delete/', views.SessionDeleteView.as_view(), name='session_delete'),
    path(
        'records/<int:pk>/toggle-status/',
        views.RecordToggleStatusView.as_view(),
        name='record_toggle_status',
    ),
]

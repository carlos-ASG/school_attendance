from django.urls import path

from . import views

app_name = 'teachers'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('courses/<int:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path(
        'courses/<int:pk>/sessions/today/',
        views.TodaySessionCreateView.as_view(),
        name='today_session_create',
    ),
    path(
        'courses/<int:pk>/history/',
        views.CourseSessionHistoryView.as_view(),
        name='course_session_history',
    ),
    path(
        'sessions/<int:pk>/today/',
        views.TodaySessionDetailView.as_view(),
        name='today_session_detail',
    ),
    path('sessions/<int:pk>/', views.PreviousSessionDetailView.as_view(), name='session_detail'),
    path('sessions/<int:pk>/delete/', views.SessionDeleteView.as_view(), name='session_delete'),
]

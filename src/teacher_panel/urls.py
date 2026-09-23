from django.urls import path

from . import views

app_name = 'teacher_panel'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('courses/<uuid:pk>/', views.CourseDetailView.as_view(), name='course_detail'),
    path(
        'courses/<uuid:course_pk>/students/<uuid:pk>/',
        views.StudentDetailView.as_view(),
        name='course_student_detail',
    ),
    path(
        'courses/<uuid:pk>/sessions/today/',
        views.TodaySessionCreateView.as_view(),
        name='today_session_create',
    ),
    path(
        'courses/<uuid:pk>/history/',
        views.CourseSessionHistoryView.as_view(),
        name='course_session_history',
    ),
    path(
        'sessions/<uuid:pk>/today/',
        views.TodaySessionDetailView.as_view(),
        name='today_session_detail',
    ),
    path('sessions/<uuid:pk>/', views.PreviousSessionDetailView.as_view(), name='session_detail'),
    path('sessions/<uuid:pk>/delete/', views.SessionDeleteView.as_view(), name='session_delete'),
]

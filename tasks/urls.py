from django.urls import path
from . import views

urlpatterns = [
    # Dashboard URLs
    path('', views.dashboard_view, name='dashboard'),

    # Task URLs
    path('tasks/', views.TaskListView.as_view(), name='task_list'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('tasks/create/', views.AdminTaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/update/', views.EmployeeTaskUpdateView.as_view(), name='task_update'),
    path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),

    # Task Status and Approval URLs
    path('tasks/<int:pk>/status/', views.update_task_status, name='update_task_status'),
    path('tasks/<int:task_id>/approve/', views.approve_task, name='approve_task'),
    path('tasks/<int:task_id>/reject/', views.reject_task, name='reject_task'),

    # Admin-specific URLs
    path('pending-approvals/', views.pending_approvals_view, name='pending_approvals'),

    # Comment URLs
    path('tasks/<int:pk>/comment/', views.add_comment, name='add_comment'),

    # Notification URLs
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:notification_id>/approve/', views.approve_from_notification, name='approve_from_notification'),
    path('notifications/<int:notification_id>/reject/', views.reject_from_notification, name='reject_from_notification'),

    # Time Tracking URLs
    path('tasks/<int:task_id>/timer/start/', views.start_timer, name='start_timer'),
    path('tasks/<int:task_id>/timer/pause/', views.pause_timer, name='pause_timer'),
    path('tasks/<int:task_id>/timer/resume/', views.resume_timer, name='resume_timer'),
    path('tasks/<int:task_id>/timer/status/', views.get_timer_status, name='get_timer_status'),

    # Request URLs
    path('tasks/<int:task_id>/send-request/', views.send_request, name='send_request'),

    # Authentication URLs
    path('register/', views.register_view, name='register'),
]

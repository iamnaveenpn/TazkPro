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

    # Authentication URLs
    path('register/', views.register_view, name='register'),
]

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, Count, Avg
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction
from django.views.decorators.http import require_POST
from .models import (Task, Category, Priority, Comment, TaskHistory, 
                    UserProfile, TaskApproval, Notification, TimeTracking)
from .forms import (TaskForm, CategoryForm, CommentForm, TaskFilterForm, 
                   CustomUserCreationForm, TaskApprovalForm, UserProfileForm,
                   EmployeeTaskForm, AdminTaskAssignForm)
from .decorators import admin_required, employee_required, AdminRequiredMixin

# Dashboard Views
@login_required
def dashboard_view(request):
    """Main dashboard - different views for admin vs employee"""
    user_profile = request.user.profile

    if user_profile.is_admin():
        return admin_dashboard(request)
    else:
        return employee_dashboard(request)

@admin_required
def admin_dashboard(request):
    """Admin dashboard with comprehensive stats"""
    # Get all tasks statistics
    total_tasks = Task.objects.count()
    pending_approval = Task.objects.filter(approval_status='pending').count()
    overdue_tasks = Task.objects.filter(
        due_date__lt=timezone.now(), 
        status__in=['assigned', 'in_progress', 'completed']
    ).count()

    # Employee statistics
    employees = User.objects.filter(profile__role='employee', profile__is_active_employee=True)
    employee_stats = []
    for emp in employees[:5]:  # Limit to top 5 for dashboard
        emp_tasks = Task.objects.filter(assigned_to=emp)
        employee_stats.append({
            'employee': emp,
            'total_tasks': emp_tasks.count(),
            'completed_tasks': emp_tasks.filter(status='approved').count(),
            'pending_tasks': emp_tasks.filter(status__in=['assigned', 'in_progress']).count(),
            'overdue_tasks': emp_tasks.filter(due_date__lt=timezone.now(), status__in=['assigned', 'in_progress']).count()
        })

    # Recent activities
    recent_tasks = Task.objects.select_related('assigned_to', 'category', 'priority').order_by('-created_at')[:10]
    tasks_needing_approval = Task.objects.filter(approval_status='pending').order_by('-completed_at')[:5]

    # Category-wise distribution
    category_stats = Category.objects.annotate(
        task_count=Count('task'),
        completed_count=Count('task', filter=Q(task__status='approved'))
    ).filter(is_active=True).order_by('-task_count')[:5]

    context = {
        'total_tasks': total_tasks,
        'pending_approval': pending_approval,
        'overdue_tasks': overdue_tasks,
        'total_employees': employees.count(),
        'employee_stats': employee_stats,
        'recent_tasks': recent_tasks,
        'tasks_needing_approval': tasks_needing_approval,
        'category_stats': category_stats,
        'unread_notifications': request.user.notifications.filter(is_read=False).count(),
    }
    return render(request, 'tasks/admin_dashboard.html', context)

@employee_required  
def employee_dashboard(request):
    """Employee dashboard showing assigned tasks"""
    user_tasks = Task.objects.filter(assigned_to=request.user)

    context = {
        'total_tasks': user_tasks.count(),
        'assigned_tasks': user_tasks.filter(status='assigned').count(),
        'in_progress_tasks': user_tasks.filter(status='in_progress').count(),
        'completed_tasks': user_tasks.filter(status='completed').count(),
        'approved_tasks': user_tasks.filter(status='approved').count(),
        'overdue_tasks': user_tasks.filter(due_date__lt=timezone.now(), status__in=['assigned', 'in_progress']).count(),
        'recent_tasks': user_tasks.order_by('-created_at')[:5],
        'urgent_tasks': user_tasks.filter(priority__level__gte=3, status__in=['assigned', 'in_progress']).order_by('-priority__level', 'due_date')[:3],
        'unread_notifications': request.user.notifications.filter(is_read=False).count(),
    }
    return render(request, 'tasks/employee_dashboard.html', context)

# Task Management Views
class TaskListView(LoginRequiredMixin, ListView):
    """Task list with role-based filtering"""
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 15

    def get_queryset(self):
        user_profile = self.request.user.profile

        # Admin can see all tasks, employee only their assigned tasks
        if user_profile.is_admin():
            queryset = Task.objects.select_related('assigned_to', 'created_by', 'category', 'priority')
        else:
            queryset = Task.objects.filter(assigned_to=self.request.user).select_related('created_by', 'category', 'priority')

        # Apply filters
        status = self.request.GET.get('status')
        category = self.request.GET.get('category')
        priority = self.request.GET.get('priority')
        assigned_to = self.request.GET.get('assigned_to')
        approval_status = self.request.GET.get('approval_status')
        search = self.request.GET.get('search')

        if status:
            queryset = queryset.filter(status=status)
        if category:
            queryset = queryset.filter(category_id=category)
        if priority:
            queryset = queryset.filter(priority_id=priority)
        if assigned_to and user_profile.is_admin():
            queryset = queryset.filter(assigned_to_id=assigned_to)
        if approval_status and user_profile.is_admin():
            queryset = queryset.filter(approval_status=approval_status)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search)
            )

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_profile = self.request.user.profile

        context['filter_form'] = TaskFilterForm(self.request.GET, user=self.request.user)
        context['is_admin'] = user_profile.is_admin()

        # Get base queryset
        if user_profile.is_admin():
            base_queryset = Task.objects.select_related('assigned_to', 'created_by', 'category', 'priority')
            context['task_counts'] = {
                'total': Task.objects.count(),
                'assigned': Task.objects.filter(status='assigned').count(),
                'in_progress': Task.objects.filter(status='in_progress').count(),
                'completed': Task.objects.filter(status='completed').count(),
                'approved': Task.objects.filter(status='approved').count(),
                'pending_approval': Task.objects.filter(approval_status='pending').count(),
            }
        else:
            base_queryset = Task.objects.filter(assigned_to=self.request.user).select_related('created_by', 'category', 'priority')
            user_tasks = Task.objects.filter(assigned_to=self.request.user)
            context['task_counts'] = {
                'total': user_tasks.count(),
                'assigned': user_tasks.filter(status='assigned').count(),
                'in_progress': user_tasks.filter(status='in_progress').count(),
                'completed': user_tasks.filter(status='completed').count(),
                'approved': user_tasks.filter(status='approved').count(),
            }

        # Separate completed and pending tasks
        context['completed_tasks'] = base_queryset.filter(status__in=['completed', 'approved']).order_by('-completed_at', '-created_at')
        context['pending_tasks'] = base_queryset.exclude(status__in=['completed', 'approved', 'cancelled']).order_by('-created_at')
        
        # Daily tasks (due today or start_date is today)
        today = timezone.now().date()
        context['daily_tasks'] = base_queryset.filter(
            Q(due_date__date=today) | Q(start_date=today)
        ).exclude(status__in=['completed', 'approved', 'cancelled']).order_by('due_date', 'priority__level')
        
        # Weekly tasks (due this week or start_date is this week)
        from datetime import timedelta
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        context['weekly_tasks'] = base_queryset.filter(
            Q(due_date__date__range=[week_start, week_end]) | 
            Q(start_date__range=[week_start, week_end])
        ).exclude(status__in=['completed', 'approved', 'cancelled']).order_by('due_date', 'priority__level')

        return context

class TaskDetailView(LoginRequiredMixin, DetailView):
    """Enhanced task detail view with approval actions"""
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'

    def get_object(self):
        task = super().get_object()
        user_profile = self.request.user.profile

        # Check permissions
        if not user_profile.is_admin() and task.assigned_to != self.request.user:
            messages.error(self.request, "You don't have permission to view this task.")
            return redirect('dashboard')

        return task

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.select_related('author')
        context['comment_form'] = CommentForm(user=self.request.user)
        context['history'] = self.object.history.select_related('user')[:10]
        context['approval_history'] = self.object.approval_history.select_related('approved_by')
        context['is_admin'] = self.request.user.profile.is_admin()
        context['can_approve'] = (self.request.user.profile.is_admin() and 
                                 self.object.can_be_approved)

        if self.request.user.profile.is_admin():
            context['approval_form'] = TaskApprovalForm()

        return context

class AdminTaskCreateView(AdminRequiredMixin, CreateView):
    """Admin task creation with employee assignment"""
    model = Task
    form_class = AdminTaskAssignForm
    template_name = 'tasks/admin_task_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        task = form.save()

        # Create notification for assigned employee
        Notification.objects.create(
            recipient=task.assigned_to,
            sender=self.request.user,
            task=task,
            notification_type='task_assigned',
            title=f'New task assigned: {task.title}',
            message=f'You have been assigned a new task: {task.title}'
        )

        # Create history record
        TaskHistory.objects.create(
            task=task,
            user=self.request.user,
            action='Task created and assigned',
            new_value=f'Assigned to {task.assigned_to.get_full_name()}'
        )

        messages.success(self.request, f'Task "{task.title}" assigned to {task.assigned_to.get_full_name()} successfully!')
        return super().form_valid(form)

class EmployeeTaskUpdateView(LoginRequiredMixin, UpdateView):
    """Employee task update - limited fields"""
    model = Task
    form_class = EmployeeTaskForm
    template_name = 'tasks/employee_task_form.html'

    def get_queryset(self):
        # Employees can only update their own tasks
        return Task.objects.filter(assigned_to=self.request.user)

    def form_valid(self, form):
        old_status = Task.objects.get(pk=self.object.pk).status
        new_status = form.instance.status

        if old_status != new_status:
            # Create history record
            TaskHistory.objects.create(
                task=self.object,
                user=self.request.user,
                action=f'Status changed from {old_status} to {new_status}',
                old_value=old_status,
                new_value=new_status
            )

            # If task completed, notify admin
            if new_status == 'completed':
                admins = User.objects.filter(profile__role='admin')
                for admin in admins:
                    Notification.objects.create(
                        recipient=admin,
                        sender=self.request.user,
                        task=self.object,
                        notification_type='task_completed',
                        title=f'Task completed: {self.object.title}',
                        message=f'{self.request.user.get_full_name()} has completed the task: {self.object.title}'
                    )

        messages.success(self.request, 'Task updated successfully!')
        return super().form_valid(form)

class TaskDeleteView(AdminRequiredMixin, DeleteView):
    """Delete view for tasks (admin only)"""
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('task_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Task deleted successfully!')
        return super().delete(request, *args, **kwargs)

@admin_required
@require_POST
def approve_task(request, task_id):
    """Admin approve task"""
    task = get_object_or_404(Task, id=task_id)

    if not task.can_be_approved:
        messages.error(request, 'Task cannot be approved at this time.')
        return redirect('task_detail', pk=task_id)

    approval_notes = request.POST.get('approval_notes', '')

    # Approve the task
    task.approve_task(request.user, approval_notes)

    # Create approval record
    TaskApproval.objects.create(
        task=task,
        approved_by=request.user,
        action='approved',
        notes=approval_notes
    )

    # Notify employee
    Notification.objects.create(
        recipient=task.assigned_to,
        sender=request.user,
        task=task,
        notification_type='task_approved',
        title=f'Task approved: {task.title}',
        message=f'Your task "{task.title}" has been approved by {request.user.get_full_name()}'
    )

    messages.success(request, f'Task "{task.title}" has been approved!')
    return redirect('task_detail', pk=task_id)

@admin_required
@require_POST  
def reject_task(request, task_id):
    """Admin reject task"""
    task = get_object_or_404(Task, id=task_id)

    if task.status != 'completed':
        messages.error(request, 'Only completed tasks can be rejected.')
        return redirect('task_detail', pk=task_id)

    rejection_notes = request.POST.get('approval_notes', '')

    if not rejection_notes.strip():
        messages.error(request, 'Rejection notes are required.')
        return redirect('task_detail', pk=task_id)

    # Reject the task
    task.reject_task(request.user, rejection_notes)

    # Create approval record
    TaskApproval.objects.create(
        task=task,
        approved_by=request.user,
        action='rejected',
        notes=rejection_notes
    )

    # Notify employee
    Notification.objects.create(
        recipient=task.assigned_to,
        sender=request.user,
        task=task,
        notification_type='task_rejected',
        title=f'Task rejected: {task.title}',
        message=f'Your task "{task.title}" has been rejected. Please check the feedback and resubmit.'
    )

    messages.warning(request, f'Task "{task.title}" has been rejected and sent back to the employee.')
    return redirect('task_detail', pk=task_id)

# Additional views for notifications, comments, etc.
@login_required
@require_POST
def add_comment(request, pk):
    """Add comment to a task"""
    task = get_object_or_404(Task, pk=pk)

    # Check permissions
    user_profile = request.user.profile
    if not user_profile.is_admin() and task.assigned_to != request.user:
        messages.error(request, "You don't have permission to comment on this task.")
        return redirect('task_detail', pk=pk)

    form = CommentForm(request.POST, user=request.user)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.task = task
        comment.author = request.user
        comment.save()
        messages.success(request, 'Comment added successfully!')
    else:
        messages.error(request, 'Error adding comment.')

    return redirect('task_detail', pk=pk)

@login_required  
@require_POST
def update_task_status(request, pk):
    """AJAX endpoint for status updates"""
    task = get_object_or_404(Task, pk=pk)
    user_profile = request.user.profile

    # Check permissions
    if not user_profile.is_admin() and task.assigned_to != request.user:
        return JsonResponse({'success': False, 'error': 'Permission denied'})

    new_status = request.POST.get('status')
    if new_status not in dict(Task.STATUS_CHOICES):
        return JsonResponse({'success': False, 'error': 'Invalid status'})

    old_status = task.status
    task.status = new_status
    task.save()

    # Create history record
    TaskHistory.objects.create(
        task=task,
        user=request.user,
        action=f'Status changed from {old_status} to {new_status}',
        old_value=old_status,
        new_value=new_status
    )

    return JsonResponse({'success': True, 'new_status': new_status})

# User registration and profile views
def register_view(request):
    """Enhanced user registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.get_full_name()}! Your account has been created successfully.')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

# Placeholder views for admin functions
@admin_required
def pending_approvals_view(request):
    """Admin view for pending approvals"""
    pending_tasks = Task.objects.filter(
        approval_status='pending'
    ).select_related('assigned_to', 'category', 'priority').order_by('-completed_at')

    context = {
        'pending_tasks': pending_tasks,
        'count': pending_tasks.count()
    }
    return render(request, 'tasks/pending_approvals.html', context)

@login_required
def notifications_view(request):
    """User notifications view - with error handling"""
    try:
        notifications = request.user.notifications.order_by('-created_at')[:50]
        
        # Mark as read when viewed
        unread_notifications = notifications.filter(is_read=False)
        unread_notifications.update(is_read=True)
        
        context = {
            'notifications': notifications,
            'is_admin': request.user.profile.is_admin() if hasattr(request.user, 'profile') else False
        }
        return render(request, 'tasks/notifications.html', context)
    except Exception as e:
        # If notifications don't work, show error
        context = {
            'notifications': [],
            'error_message': f'Notifications are currently unavailable: {str(e)}',
            'is_admin': False
        }
        return render(request, 'tasks/notifications.html', context)

# Time Tracking Views
@login_required
@require_POST
def start_timer(request, task_id):
    """Start timer for a task"""
    task = get_object_or_404(Task, id=task_id)
    
    # Check permissions - only assigned user can track time
    if task.assigned_to != request.user:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    # Check if there's already an active timer for this task
    active_timer = task.get_active_timer()
    if active_timer:
        return JsonResponse({'success': False, 'error': 'Timer already running'})
    
    # Create new timer
    timer = TimeTracking.objects.create(
        task=task,
        user=request.user,
        start_time=timezone.now(),
        is_active=True
    )
    
    return JsonResponse({
        'success': True,
        'timer_id': timer.id,
        'start_time': timer.start_time.isoformat()
    })

@login_required
@require_POST
def pause_timer(request, task_id):
    """Pause/stop timer for a task"""
    task = get_object_or_404(Task, id=task_id)
    
    # Check permissions
    if task.assigned_to != request.user:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    # Get active timer
    timer = task.get_active_timer()
    if not timer:
        return JsonResponse({'success': False, 'error': 'No active timer found'})
    
    # Stop the timer
    timer.end_time = timezone.now()
    timer.is_active = False
    timer.save()
    
    # Update task total_time
    task.update_total_time()
    
    return JsonResponse({
        'success': True,
        'duration': str(timer.duration) if timer.duration else None,
        'total_time': str(task.total_time) if task.total_time else None
    })

@login_required
@require_POST
def resume_timer(request, task_id):
    """Resume timer for a task"""
    task = get_object_or_404(Task, id=task_id)
    
    # Check permissions
    if task.assigned_to != request.user:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    # Check if there's already an active timer
    if task.has_active_timer:
        return JsonResponse({'success': False, 'error': 'Timer already running'})
    
    # Create new timer session
    timer = TimeTracking.objects.create(
        task=task,
        user=request.user,
        start_time=timezone.now(),
        is_active=True
    )
    
    return JsonResponse({
        'success': True,
        'timer_id': timer.id,
        'start_time': timer.start_time.isoformat()
    })

@login_required
def get_timer_status(request, task_id):
    """Get current timer status for a task"""
    task = get_object_or_404(Task, id=task_id)
    
    # Check permissions
    if task.assigned_to != request.user:
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    active_timer = task.get_active_timer()
    
    if active_timer:
        elapsed = timezone.now() - active_timer.start_time
        return JsonResponse({
            'success': True,
            'is_active': True,
            'start_time': active_timer.start_time.isoformat(),
            'elapsed_seconds': int(elapsed.total_seconds()),
            'total_time': str(task.total_time) if task.total_time else None
        })
    else:
        return JsonResponse({
            'success': True,
            'is_active': False,
            'total_time': str(task.total_time) if task.total_time else None
        })

# Notification actions
@admin_required
@require_POST
def approve_from_notification(request, notification_id):
    """Approve task directly from notification"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    
    if not notification.task:
        messages.error(request, 'No task associated with this notification.')
        return redirect('notifications')
    
    task = notification.task
    if not task.can_be_approved:
        messages.error(request, 'Task cannot be approved at this time.')
        return redirect('notifications')
    
    approval_notes = request.POST.get('approval_notes', '')
    task.approve_task(request.user, approval_notes)
    
    # Create approval record
    TaskApproval.objects.create(
        task=task,
        approved_by=request.user,
        action='approved',
        notes=approval_notes
    )
    
    # Notify employee
    Notification.objects.create(
        recipient=task.assigned_to,
        sender=request.user,
        task=task,
        notification_type='task_approved',
        title=f'Task approved: {task.title}',
        message=f'Your task "{task.title}" has been approved by {request.user.get_full_name()}'
    )
    
    # Mark notification as read
    notification.is_read = True
    notification.save()
    
    messages.success(request, f'Task "{task.title}" has been approved!')
    return redirect('notifications')

@admin_required
@require_POST
def reject_from_notification(request, notification_id):
    """Reject task directly from notification"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    
    if not notification.task:
        messages.error(request, 'No task associated with this notification.')
        return redirect('notifications')
    
    task = notification.task
    if task.status != 'completed':
        messages.error(request, 'Only completed tasks can be rejected.')
        return redirect('notifications')
    
    rejection_notes = request.POST.get('approval_notes', '')
    if not rejection_notes.strip():
        messages.error(request, 'Rejection notes are required.')
        return redirect('notifications')
    
    task.reject_task(request.user, rejection_notes)
    
    # Create approval record
    TaskApproval.objects.create(
        task=task,
        approved_by=request.user,
        action='rejected',
        notes=rejection_notes
    )
    
    # Notify employee
    Notification.objects.create(
        recipient=task.assigned_to,
        sender=request.user,
        task=task,
        notification_type='task_rejected',
        title=f'Task rejected: {task.title}',
        message=f'Your task "{task.title}" has been rejected. Please check the feedback and resubmit.'
    )
    
    # Mark notification as read
    notification.is_read = True
    notification.save()
    
    messages.warning(request, f'Task "{task.title}" has been rejected.')
    return redirect('notifications')

@login_required
@require_POST
def send_request(request, task_id):
    """Employee sends a request (e.g., for clarification, extension, etc.)"""
    task = get_object_or_404(Task, id=task_id)
    
    # Check permissions
    if task.assigned_to != request.user:
        messages.error(request, "You don't have permission to send requests for this task.")
        return redirect('task_detail', pk=task_id)
    
    request_type = request.POST.get('request_type', 'general')
    request_message = request.POST.get('message', '')
    
    if not request_message.strip():
        messages.error(request, 'Request message is required.')
        return redirect('task_detail', pk=task_id)
    
    # Notify admins
    admins = User.objects.filter(profile__role='admin')
    for admin in admins:
        Notification.objects.create(
            recipient=admin,
            sender=request.user,
            task=task,
            notification_type='request_sent',
            title=f'Request from {request.user.get_full_name()}: {task.title}',
            message=request_message,
            request_data={'type': request_type, 'message': request_message}
        )
    
    messages.success(request, 'Your request has been sent to administrators.')
    return redirect('task_detail', pk=task_id)


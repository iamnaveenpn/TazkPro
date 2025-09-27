from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

# Custom User Profile to extend user functionality
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('employee', 'Employee'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='employee')
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    is_active_employee = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    def is_admin(self):
        return self.role == 'admin'

    def is_employee(self):
        return self.role == 'employee'

class Category(models.Model):
    """Model for task categories"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=7, default='#007bff')  # Hex color code
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_categories')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'pk': self.pk})

class Priority(models.Model):
    """Model for task priorities"""
    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Critical'),
        (5, 'Emergency'),
    ]

    name = models.CharField(max_length=20)
    level = models.IntegerField(choices=PRIORITY_CHOICES, unique=True)
    color = models.CharField(max_length=7, default='#6c757d')
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Priorities"
        ordering = ['level']

    def __str__(self):
        return self.name

class Task(models.Model):
    """Enhanced Task model with approval system"""
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'), 
        ('completed', 'Completed (Pending Approval)'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold'),
    ]

    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('not_required', 'Not Required'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.ForeignKey(Priority, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')

    # User relationships
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_tasks')

    # Approval system
    approval_status = models.CharField(max_length=15, choices=APPROVAL_STATUS_CHOICES, default='not_required')
    approval_notes = models.TextField(blank=True, null=True, help_text="Admin notes for approval/rejection")
    requires_approval = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    # Additional fields
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    completion_notes = models.TextField(blank=True, null=True, help_text="Employee notes on task completion")
    attachment = models.FileField(upload_to='task_attachments/', null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['due_date']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['approval_status']),
        ]
        permissions = [
            ('can_assign_tasks', 'Can assign tasks to employees'),
            ('can_approve_tasks', 'Can approve completed tasks'),
            ('can_view_all_tasks', 'Can view all tasks'),
            ('can_manage_employees', 'Can manage employees'),
        ]

    def __str__(self):
        return f"{self.title} - {self.assigned_to.username}"

    def get_absolute_url(self):
        return reverse('task_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        # Auto-set timestamps based on status changes
        if self.status == 'in_progress' and not self.started_at:
            self.started_at = timezone.now()
        elif self.status == 'completed' and not self.completed_at:
            self.completed_at = timezone.now()
            if self.requires_approval:
                self.approval_status = 'pending'
        elif self.status == 'approved' and not self.approved_at:
            self.approved_at = timezone.now()
            self.approval_status = 'approved'

        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        """Check if task is overdue"""
        if self.due_date and self.status not in ['approved', 'cancelled']:
            return timezone.now() > self.due_date
        return False

    @property
    def days_until_due(self):
        """Calculate days until due date"""
        if self.due_date:
            delta = self.due_date.date() - timezone.now().date()
            return delta.days
        return None

    @property
    def can_be_approved(self):
        """Check if task can be approved"""
        return self.status == 'completed' and self.approval_status == 'pending'

    def approve_task(self, approved_by, notes=""):
        """Approve the task"""
        self.status = 'approved'
        self.approval_status = 'approved'
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.approval_notes = notes
        self.save()

    def reject_task(self, rejected_by, notes=""):
        """Reject the task"""
        self.status = 'in_progress'  # Send back to in progress
        self.approval_status = 'rejected'
        self.approved_by = rejected_by
        self.approval_notes = notes
        self.completed_at = None  # Clear completion time
        self.save()

class TaskApproval(models.Model):
    """Model to track task approval history"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='approval_history')
    approved_by = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=[
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('requested', 'Approval Requested'),
    ])
    notes = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Task Approval'
        verbose_name_plural = 'Task Approvals'

    def __str__(self):
        return f"{self.task.title} - {self.action} by {self.approved_by.username}"

class Comment(models.Model):
    """Model for task comments"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_internal = models.BooleanField(default=False, help_text="Internal admin/management comments")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment by {self.author.username} on {self.task.title}'

class TaskHistory(models.Model):
    """Model to track all task changes"""
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    old_value = models.CharField(max_length=200, blank=True, null=True)
    new_value = models.CharField(max_length=200, blank=True, null=True)
    changes = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Task histories"

    def __str__(self):
        return f'{self.action} on {self.task.title} by {self.user.username}'

class Notification(models.Model):
    """Model for user notifications"""
    NOTIFICATION_TYPES = [
        ('task_assigned', 'Task Assigned'),
        ('task_completed', 'Task Completed'),
        ('task_approved', 'Task Approved'),
        ('task_rejected', 'Task Rejected'),
        ('task_overdue', 'Task Overdue'),
        ('approval_requested', 'Approval Requested'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.recipient.username}"

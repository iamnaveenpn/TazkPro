from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from .models import (Task, Category, Priority, Comment, TaskHistory, 
                    UserProfile, TaskApproval, Notification)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role_display', 'employee_id', 'department', 'is_active_employee', 'created_at')
    list_filter = ('role', 'is_active_employee', 'department', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'employee_id', 'department')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'role', 'is_active_employee')
        }),
        ('Employee Details', {
            'fields': ('employee_id', 'department', 'phone_number'),
            'classes': ('collapse',)
        }),
        ('Profile', {
            'fields': ('avatar', 'created_at'),
            'classes': ('collapse',)
        })
    )

    def role_display(self, obj):
        colors = {'admin': '#dc3545', 'employee': '#198754'}
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.role, '#000'), obj.get_role_display()
        )
    role_display.short_description = 'Role'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'color_display', 'task_count', 'is_active', 'created_by', 'created_at')
    list_filter = ('is_active', 'created_at', 'created_by')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)

    def color_display(self, obj):
        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 16px;">●</span> {}',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'

    def task_count(self, obj):
        count = obj.task_set.count()
        return format_html('<strong>{}</strong>', count)
    task_count.short_description = 'Tasks'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by').annotate(
            task_count=Count('task')
        )

@admin.register(Priority)
class PriorityAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'color_display', 'task_count')
    ordering = ('level',)

    def color_display(self, obj):
        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 16px;">●</span> {}',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'

    def task_count(self, obj):
        count = obj.task_set.count()
        return format_html('<strong>{}</strong>', count)
    task_count.short_description = 'Tasks'

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('created_at', 'author')
    fields = ('author', 'content', 'is_internal', 'created_at')

class TaskHistoryInline(admin.TabularInline):
    model = TaskHistory
    extra = 0
    readonly_fields = ('timestamp', 'user', 'action')
    fields = ('user', 'action', 'old_value', 'new_value', 'timestamp')

class TaskApprovalInline(admin.TabularInline):
    model = TaskApproval
    extra = 0
    readonly_fields = ('timestamp', 'approved_by', 'action')
    fields = ('approved_by', 'action', 'notes', 'timestamp')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'assigned_to_display', 'status_display', 'priority_display', 
        'approval_status_display', 'due_date', 'created_at', 'is_overdue_display'
    )
    list_filter = (
        'status', 'approval_status', 'category', 'priority', 'created_at', 
        'due_date', 'assigned_to', 'created_by', 'requires_approval'
    )
    search_fields = (
        'title', 'description', 'assigned_to__username', 'assigned_to__first_name',
        'assigned_to__last_name', 'created_by__username'
    )
    date_hierarchy = 'created_at'
    inlines = [CommentInline, TaskHistoryInline, TaskApprovalInline]
    readonly_fields = ('created_at', 'updated_at', 'started_at', 'completed_at', 'approved_at')

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'priority')
        }),
        ('Assignment & Status', {
            'fields': ('assigned_to', 'created_by', 'status', 'requires_approval')
        }),
        ('Approval Information', {
            'fields': ('approval_status', 'approved_by', 'approval_notes'),
            'classes': ('collapse',)
        }),
        ('Time Information', {
            'fields': ('due_date', 'estimated_hours', 'actual_hours'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'started_at', 'completed_at', 'approved_at'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('completion_notes', 'attachment'),
            'classes': ('collapse',)
        })
    )

    actions = ['mark_as_approved', 'mark_as_rejected']

    def assigned_to_display(self, obj):
        profile = obj.assigned_to.profile
        color = '#198754' if profile.role == 'employee' else '#dc3545'
        return format_html(
            '<span style="color: {};">{}</span>',
            color, obj.assigned_to.get_full_name() or obj.assigned_to.username
        )
    assigned_to_display.short_description = 'Assigned To'

    def priority_display(self, obj):
        if obj.priority:
            return format_html(
                '<span style="color: {}; font-weight: bold;">{} {}</span>',
                obj.priority.color, '●' * obj.priority.level, obj.priority.name
            )
        return '-'
    priority_display.short_description = 'Priority'

    def status_display(self, obj):
        colors = {
            'assigned': '#6c757d',
            'in_progress': '#0dcaf0',
            'completed': '#ffc107',
            'approved': '#198754',
            'rejected': '#dc3545',
            'cancelled': '#495057',
            'on_hold': '#fd7e14'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            colors.get(obj.status, '#000'), obj.get_status_display()
        )
    status_display.short_description = 'Status'

    def approval_status_display(self, obj):
        if not obj.requires_approval:
            return format_html('<em style="color: #6c757d;">Not Required</em>')

        colors = {
            'pending': '#ffc107',
            'approved': '#198754', 
            'rejected': '#dc3545',
            'not_required': '#6c757d'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            colors.get(obj.approval_status, '#000'), obj.get_approval_status_display()
        )
    approval_status_display.short_description = 'Approval'

    def is_overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: #dc3545;">⚠ Overdue</span>')
        return format_html('<span style="color: #198754;">✓ On Time</span>')
    is_overdue_display.short_description = 'Status'

    def mark_as_approved(self, request, queryset):
        """Bulk approve selected tasks"""
        updated = 0
        for task in queryset.filter(status='completed', approval_status='pending'):
            task.approve_task(request.user, "Bulk approved from admin")
            updated += 1

        self.message_user(
            request,
            f'{updated} task(s) were successfully approved.',
            messages.SUCCESS
        )
    mark_as_approved.short_description = "Mark selected tasks as approved"

    def mark_as_rejected(self, request, queryset):
        """Bulk reject selected tasks"""
        updated = 0
        for task in queryset.filter(status='completed'):
            task.reject_task(request.user, "Bulk rejected from admin - please review")
            updated += 1

        self.message_user(
            request,
            f'{updated} task(s) were rejected and sent back to employees.',
            messages.WARNING
        )
    mark_as_rejected.short_description = "Mark selected tasks as rejected"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'category', 'priority', 'assigned_to', 'assigned_to__profile',
            'created_by', 'approved_by'
        )

@admin.register(TaskApproval)
class TaskApprovalAdmin(admin.ModelAdmin):
    list_display = ('task_title', 'approved_by', 'action_display', 'timestamp')
    list_filter = ('action', 'timestamp', 'approved_by')
    search_fields = ('task__title', 'approved_by__username', 'notes')
    readonly_fields = ('timestamp',)

    def task_title(self, obj):
        return obj.task.title
    task_title.short_description = 'Task'

    def action_display(self, obj):
        colors = {
            'approved': '#198754',
            'rejected': '#dc3545',
            'requested': '#ffc107'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.action, '#000'), obj.get_action_display()
        )
    action_display.short_description = 'Action'

    def has_add_permission(self, request):
        return False  # Approvals are created automatically

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task_title', 'author', 'content_preview', 'is_internal', 'created_at')
    list_filter = ('is_internal', 'created_at', 'author')
    search_fields = ('content', 'task__title', 'author__username')
    readonly_fields = ('created_at', 'updated_at')

    def task_title(self, obj):
        return obj.task.title
    task_title.short_description = 'Task'

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'

@admin.register(TaskHistory)
class TaskHistoryAdmin(admin.ModelAdmin):
    list_display = ('task_title', 'user', 'action', 'timestamp')
    list_filter = ('action', 'timestamp', 'user')
    search_fields = ('task__title', 'user__username', 'action')
    readonly_fields = ('timestamp',)

    def task_title(self, obj):
        return obj.task.title
    task_title.short_description = 'Task'

    def has_add_permission(self, request):
        return False  # History is auto-generated

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'notification_type_display', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'recipient__username')
    readonly_fields = ('created_at',)

    actions = ['mark_as_read', 'mark_as_unread']

    def notification_type_display(self, obj):
        colors = {
            'task_assigned': '#0dcaf0',
            'task_completed': '#ffc107',
            'task_approved': '#198754',
            'task_rejected': '#dc3545',
            'task_overdue': '#fd7e14',
            'approval_requested': '#6f42c1'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            colors.get(obj.notification_type, '#000'), obj.get_notification_type_display()
        )
    notification_type_display.short_description = 'Type'

    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(
            request,
            f'{updated} notification(s) marked as read.',
            messages.SUCCESS
        )
    mark_as_read.short_description = "Mark selected as read"

    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(
            request,
            f'{updated} notification(s) marked as unread.',
            messages.SUCCESS
        )
    mark_as_unread.short_description = "Mark selected as unread"

# Customize admin site header and title
admin.site.site_header = "Task Pro Administration"
admin.site.site_title = "Task Pro Admin"
admin.site.index_title = "Welcome to Task Pro Administration"

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import (Task, Category, Priority, Comment, UserProfile, 
                    TaskApproval, Notification)
from django.utils import timezone

class CustomUserCreationForm(UserCreationForm):
    """Enhanced user registration form with role selection"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    employee_id = forms.CharField(
        max_length=20, 
        required=False,
        help_text="Required for employees"
    )
    department = forms.CharField(max_length=100, required=False)
    phone_number = forms.CharField(max_length=15, required=False)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id')
        role = self.cleaned_data.get('role')

        if role == 'employee' and not employee_id:
            raise forms.ValidationError("Employee ID is required for employee accounts.")

        if employee_id and UserProfile.objects.filter(employee_id=employee_id).exists():
            raise forms.ValidationError("This Employee ID already exists.")

        return employee_id

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]

        if commit:
            user.save()
            # Update or create profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = self.cleaned_data['role']
            profile.employee_id = self.cleaned_data.get('employee_id')
            profile.department = self.cleaned_data.get('department')
            profile.phone_number = self.cleaned_data.get('phone_number')
            profile.save()

        return user

class AdminTaskAssignForm(forms.ModelForm):
    """Admin form for creating and assigning tasks"""

    class Meta:
        model = Task
        fields = [
            'title', 'description', 'category', 'priority', 
            'assigned_to', 'due_date', 'start_date', 'end_date',
            'estimated_hours', 'requires_approval', 'attachment'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter task title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Describe the task in detail...'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local', 
                'class': 'form-control'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0'
            }),
            'requires_approval': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active employees in assignment dropdown
        self.fields['assigned_to'].queryset = User.objects.filter(
            profile__role='employee',
            profile__is_active_employee=True,
            is_active=True
        ).order_by('first_name', 'last_name')

        # Add helpful labels and help text
        self.fields['assigned_to'].label = "Assign to Employee"
        self.fields['due_date'].help_text = "Set deadline for task completion"
        self.fields['start_date'].help_text = "Planned start date for the task"
        self.fields['end_date'].help_text = "Planned end date for the task"
        self.fields['estimated_hours'].help_text = "Estimated hours to complete"
        self.fields['requires_approval'].help_text = "Check if task requires admin approval after completion"

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < timezone.now():
            raise forms.ValidationError("Due date cannot be in the past.")
        return due_date

class EmployeeTaskForm(forms.ModelForm):
    """Employee form for updating assigned tasks (limited fields)"""

    class Meta:
        model = Task
        fields = ['status', 'actual_hours', 'completion_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'actual_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0'
            }),
            'completion_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add any notes about task completion...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Limit status choices based on current status
        instance = kwargs.get('instance')
        if instance:
            current_status = instance.status

            # Define allowed transitions
            status_transitions = {
                'assigned': ['in_progress'],
                'in_progress': ['completed', 'on_hold'],
                'completed': [],  # Can't change from completed
                'approved': [],   # Can't change from approved
                'rejected': ['in_progress'],  # Can restart from rejected
                'on_hold': ['in_progress'],
                'cancelled': []   # Can't change from cancelled
            }

            allowed_statuses = status_transitions.get(current_status, [])
            allowed_statuses.append(current_status)  # Can keep current status

            status_choices = [
                (status, label) for status, label in Task.STATUS_CHOICES
                if status in allowed_statuses
            ]

            self.fields['status'].choices = status_choices

        # Help text
        self.fields['actual_hours'].help_text = "How many hours did you actually spend?"
        self.fields['completion_notes'].help_text = "Provide details about what was accomplished"

class TaskFilterForm(forms.Form):
    """Enhanced form for filtering tasks with role-based options"""
    STATUS_CHOICES = [('', 'All Statuses')] + Task.STATUS_CHOICES
    APPROVAL_CHOICES = [('', 'All')] + Task.APPROVAL_STATUS_CHOICES

    status = forms.ChoiceField(
        choices=STATUS_CHOICES, 
        required=False, 
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    approval_status = forms.ChoiceField(
        choices=APPROVAL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    priority = forms.ModelChoiceField(
        queryset=Priority.objects.all(),
        required=False,
        empty_label="All Priorities",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(
            profile__role='employee',
            is_active=True
        ),
        required=False,
        empty_label="All Employees",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search tasks...'
        })
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Hide admin-only fields for employees
        if user and hasattr(user, 'profile') and not user.profile.is_admin():
            del self.fields['assigned_to']
            del self.fields['approval_status']

class CategoryForm(forms.ModelForm):
    """Form for creating and updating categories"""

    class Meta:
        model = Category
        fields = ['name', 'description', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'color': forms.TextInput(attrs={
                'type': 'color',
                'class': 'form-control form-control-color'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].help_text = "Brief description of this category"

class CommentForm(forms.ModelForm):
    """Form for adding comments to tasks"""

    class Meta:
        model = Comment
        fields = ['content', 'is_internal']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add a comment...'
            }),
            'is_internal': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Only admins can mark comments as internal
        if user and hasattr(user, 'profile') and not user.profile.is_admin():
            del self.fields['is_internal']
        else:
            self.fields['is_internal'].help_text = "Internal comments are only visible to admins"

class TaskApprovalForm(forms.Form):
    """Form for task approval/rejection"""
    action = forms.ChoiceField(
        choices=[('approve', 'Approve'), ('reject', 'Reject')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add approval/rejection notes...'
        }),
        required=False,
        help_text="Notes are optional for approval, required for rejection"
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        notes = cleaned_data.get('notes', '').strip()

        if action == 'reject' and not notes:
            raise forms.ValidationError("Rejection notes are required when rejecting a task.")

        return cleaned_data

class UserProfileForm(forms.ModelForm):
    """Form for updating user profile"""
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = UserProfile
        fields = ['employee_id', 'department', 'phone_number', 'avatar']
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            # Update user fields
            profile.user.first_name = self.cleaned_data['first_name']
            profile.user.last_name = self.cleaned_data['last_name']
            profile.user.email = self.cleaned_data['email']
            profile.user.save()
            profile.save()
        return profile

# Basic TaskForm for backward compatibility
class TaskForm(AdminTaskAssignForm):
    """Basic task form - alias for AdminTaskAssignForm"""
    pass

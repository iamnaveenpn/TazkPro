from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from .models import Task, Category, Priority, UserProfile

class TaskManagerTestCase(TestCase):
    def setUp(self):
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123'
        )
        self.admin_user.profile.role = 'admin'
        self.admin_user.profile.save()

        self.employee_user = User.objects.create_user(
            username='employee_test',
            email='employee@test.com',
            password='testpass123'
        )
        self.employee_user.profile.role = 'employee'
        self.employee_user.profile.save()

        # Create test data
        self.category = Category.objects.create(
            name='Test Category',
            description='Test Description',
            created_by=self.admin_user
        )

        self.priority = Priority.objects.create(
            name='High',
            level=3
        )

        self.client = Client()

    def test_user_profile_creation(self):
        """Test that user profiles are created automatically"""
        user = User.objects.create_user(
            username='newuser',
            password='testpass123'
        )
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.role, 'employee')  # Default role

    def test_admin_dashboard_access(self):
        """Test that admin can access admin dashboard"""
        self.client.login(username='admin_test', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_employee_dashboard_access(self):
        """Test that employee can access employee dashboard"""
        self.client.login(username='employee_test', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_task_creation_by_admin(self):
        """Test that admin can create and assign tasks"""
        self.client.login(username='admin_test', password='testpass123')

        task_data = {
            'title': 'Test Task',
            'description': 'Test Description',
            'category': self.category.id,
            'priority': self.priority.id,
            'assigned_to': self.employee_user.id,
            'requires_approval': True,
        }

        response = self.client.post(reverse('task_create'), task_data)
        self.assertEqual(response.status_code, 302)  # Redirect after creation

        task = Task.objects.get(title='Test Task')
        self.assertEqual(task.assigned_to, self.employee_user)
        self.assertEqual(task.created_by, self.admin_user)
        self.assertEqual(task.status, 'assigned')

    def test_task_status_update_by_employee(self):
        """Test that employee can update task status"""
        task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            assigned_to=self.employee_user,
            created_by=self.admin_user,
            status='assigned'
        )

        self.client.login(username='employee_test', password='testpass123')

        # Update task status to in_progress
        response = self.client.post(
            reverse('update_task_status', kwargs={'pk': task.pk}),
            {'status': 'in_progress'}
        )

        task.refresh_from_db()
        self.assertEqual(task.status, 'in_progress')
        self.assertIsNotNone(task.started_at)

    def test_task_approval_workflow(self):
        """Test the complete approval workflow"""
        task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            assigned_to=self.employee_user,
            created_by=self.admin_user,
            status='in_progress',
            requires_approval=True
        )

        # Employee completes task
        task.status = 'completed'
        task.save()

        self.assertEqual(task.approval_status, 'pending')
        self.assertTrue(task.can_be_approved)

        # Admin approves task
        task.approve_task(self.admin_user, 'Good work!')

        self.assertEqual(task.status, 'approved')
        self.assertEqual(task.approval_status, 'approved')
        self.assertEqual(task.approved_by, self.admin_user)
        self.assertIsNotNone(task.approved_at)

    def test_employee_cannot_access_admin_views(self):
        """Test that employee cannot access admin-only views"""
        self.client.login(username='employee_test', password='testpass123')

        # Try to access admin-only view
        response = self.client.get(reverse('pending_approvals'))
        self.assertEqual(response.status_code, 302)  # Redirect to dashboard

    def test_task_overdue_property(self):
        """Test task overdue detection"""
        past_date = timezone.now() - timezone.timedelta(days=1)

        task = Task.objects.create(
            title='Overdue Task',
            description='Test Description',
            assigned_to=self.employee_user,
            created_by=self.admin_user,
            due_date=past_date,
            status='in_progress'
        )

        self.assertTrue(task.is_overdue)

        # Completed tasks should not be overdue
        task.status = 'approved'
        task.save()
        self.assertFalse(task.is_overdue)

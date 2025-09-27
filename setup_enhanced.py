#!/usr/bin/env python
"""
Task Pro Setup Script
Run this after extracting the zip file to set up the complete system
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_enhanced_system():
    """Setup the enhanced role-based task manager system"""
    print("🚀 Setting up Task Pro with Role-Based Access...")

    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_manager.settings')

    try:
        django.setup()

        # Import models after Django setup
        from django.contrib.auth.models import User
        from tasks.models import UserProfile, Priority, Category

        print("📋 Step 1: Creating database migrations...")
        execute_from_command_line(['manage.py', 'makemigrations'])

        print("💾 Step 2: Applying migrations...")
        execute_from_command_line(['manage.py', 'migrate'])

        print("👤 Step 3: Creating user profiles for existing users...")
        for user in User.objects.all():
            profile, created = UserProfile.objects.get_or_create(user=user)
            if created:
                # Set role based on superuser status
                if user.is_superuser or user.is_staff:
                    profile.role = 'admin'
                else:
                    profile.role = 'employee'
                profile.save()
                print(f"   ✅ Created {profile.role} profile for {user.username}")

        print("🏷️  Step 4: Creating priorities...")
        priorities = [
            {'name': 'Low', 'level': 1, 'color': '#17a2b8'},
            {'name': 'Medium', 'level': 2, 'color': '#ffc107'},
            {'name': 'High', 'level': 3, 'color': '#fd7e14'},
            {'name': 'Critical', 'level': 4, 'color': '#dc3545'},
            {'name': 'Emergency', 'level': 5, 'color': '#6f42c1'},
        ]

        for priority_data in priorities:
            priority, created = Priority.objects.get_or_create(
                level=priority_data['level'],
                defaults=priority_data
            )
            if created:
                print(f"   ✅ Created priority: {priority.name}")

        print("📂 Step 5: Creating categories...")
        admin_user = User.objects.filter(is_superuser=True).first()

        if admin_user:
            categories = [
                {'name': 'Development', 'description': 'Software development tasks', 'color': '#007bff'},
                {'name': 'Testing', 'description': 'Quality assurance and testing', 'color': '#28a745'},
                {'name': 'Documentation', 'description': 'Documentation and reporting', 'color': '#6f42c1'},
                {'name': 'Maintenance', 'description': 'System maintenance tasks', 'color': '#fd7e14'},
                {'name': 'Support', 'description': 'Customer support tasks', 'color': '#e83e8c'},
            ]

            for category_data in categories:
                category_data['created_by'] = admin_user
                category, created = Category.objects.get_or_create(
                    name=category_data['name'],
                    defaults=category_data
                )
                if created:
                    print(f"   ✅ Created category: {category.name}")

        print("\n🎉 Task Pro setup completed successfully!")
        print("\n📚 Next steps:")
        print("1. Create test users: python create_test_users.py")
        print("2. Start the server: python manage.py runserver")
        print("3. Login with admin account to assign tasks")
        print("4. Login with employee account to work on tasks")
        print("\n🌐 Access URLs:")
        print("   Main App: http://127.0.0.1:8000/")
        print("   Admin Panel: http://127.0.0.1:8000/admin/")
        print("\n🔐 Demo Credentials (create with create_test_users.py):")
        print("   Admin: admin / admin123")
        print("   Employee: john.doe / emp123")

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        print("\n🔧 Manual steps:")
        print("1. Install requirements: pip install -r requirements.txt")
        print("2. Run: python manage.py makemigrations")
        print("3. Run: python manage.py migrate")
        print("4. Run: python manage.py createsuperuser")
        print("5. Run: python create_test_users.py")
        return False

    return True

if __name__ == '__main__':
    setup_enhanced_system()

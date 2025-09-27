#!/usr/bin/env python
"""
Create test users for the Task Pro
Run this script to create sample admin and employee accounts
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_manager.settings')
django.setup()

from django.contrib.auth.models import User
from tasks.models import UserProfile

def create_test_users():
    """Create test admin and employee users"""
    print("👥 Creating test users for Task Pro...")

    # Create admin user
    admin_data = {
        'username': 'admin',
        'email': 'admin@taskmanager.com',
        'password': 'admin123',
        'first_name': 'System',
        'last_name': 'Administrator'
    }

    admin, created = User.objects.get_or_create(
        username=admin_data['username'],
        defaults=admin_data
    )

    if created:
        admin.set_password(admin_data['password'])
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()

        # Set admin profile
        admin.profile.role = 'admin'
        admin.profile.department = 'Administration'
        admin.profile.phone_number = '+1-555-0001'
        admin.profile.save()

        print(f"   ✅ Created admin user: {admin.username} (password: admin123)")
    else:
        print(f"   ⚠️  Admin user already exists: {admin.username}")

    # Create employee users
    employees_data = [
        {
            'username': 'john.doe',
            'email': 'john.doe@taskmanager.com', 
            'password': 'emp123',
            'first_name': 'John',
            'last_name': 'Doe',
            'employee_id': 'EMP001',
            'department': 'Development',
            'phone_number': '+1-555-0101'
        },
        {
            'username': 'jane.smith',
            'email': 'jane.smith@taskmanager.com',
            'password': 'emp123', 
            'first_name': 'Jane',
            'last_name': 'Smith',
            'employee_id': 'EMP002',
            'department': 'Development',
            'phone_number': '+1-555-0102'
        },
        {
            'username': 'mike.wilson',
            'email': 'mike.wilson@taskmanager.com',
            'password': 'emp123',
            'first_name': 'Mike', 
            'last_name': 'Wilson',
            'employee_id': 'EMP003',
            'department': 'Testing',
            'phone_number': '+1-555-0103'
        },
        {
            'username': 'sarah.johnson',
            'email': 'sarah.johnson@taskmanager.com',
            'password': 'emp123',
            'first_name': 'Sarah',
            'last_name': 'Johnson', 
            'employee_id': 'EMP004',
            'department': 'Documentation',
            'phone_number': '+1-555-0104'
        }
    ]

    for emp_data in employees_data:
        employee, created = User.objects.get_or_create(
            username=emp_data['username'],
            defaults={
                'email': emp_data['email'],
                'first_name': emp_data['first_name'],
                'last_name': emp_data['last_name']
            }
        )

        if created:
            employee.set_password(emp_data['password'])
            employee.save()

            # Set employee profile
            employee.profile.role = 'employee'
            employee.profile.employee_id = emp_data['employee_id']
            employee.profile.department = emp_data['department']
            employee.profile.phone_number = emp_data['phone_number']
            employee.profile.save()

            print(f"   ✅ Created employee: {employee.username} (password: emp123)")
        else:
            print(f"   ⚠️  Employee already exists: {employee.username}")

    print("\n🎉 Test users created successfully!")
    print("\n📋 Login Credentials:")
    print("\n👨‍💼 Admin Account:")
    print("   Username: admin")
    print("   Password: admin123")
    print("   Role: System Administrator")

    print("\n👥 Employee Accounts:")
    for emp_data in employees_data:
        print(f"   Username: {emp_data['username']}")
        print(f"   Password: emp123")
        print(f"   Role: Employee ({emp_data['department']})")
        print("")

    print("🚀 You can now login and test the role-based functionality!")
    print("\n🔗 Access URLs:")
    print("   Main App: http://127.0.0.1:8000/")
    print("   Admin Panel: http://127.0.0.1:8000/admin/")

if __name__ == '__main__':
    create_test_users()

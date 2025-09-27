# QUICK CATEGORY POPULATION SCRIPT
# Save this as populate_categories.py in your project root

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_manager.settings')
django.setup()

from tasks.models import Category, Priority
from django.contrib.auth.models import User

def populate_categories():
    print("🚀 Populating categories and priorities...")

    # Get or create admin user
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.first()

    if not admin_user:
        print("❌ No users found. Create a user first!")
        return

    # Categories to create
    categories = [
        {'name': 'Development', 'description': 'Software development and programming tasks', 'color': '#007bff'},
        {'name': 'Testing', 'description': 'Quality assurance and testing tasks', 'color': '#28a745'},
        {'name': 'Documentation', 'description': 'Documentation and technical writing', 'color': '#6f42c1'},
        {'name': 'Bug Fix', 'description': 'Bug fixing and maintenance tasks', 'color': '#dc3545'},
        {'name': 'Research', 'description': 'Research and analysis tasks', 'color': '#fd7e14'},
        {'name': 'Meeting', 'description': 'Meetings and discussions', 'color': '#20c997'},
        {'name': 'Support', 'description': 'Customer support and help desk', 'color': '#e83e8c'},
        {'name': 'Design', 'description': 'UI/UX and graphic design tasks', 'color': '#f012be'},
    ]

    # Create categories
    created_count = 0
    for cat_data in categories:
        category, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={
                'description': cat_data['description'],
                'color': cat_data['color'],
                'created_by': admin_user,
                'is_active': True
            }
        )
        if created:
            print(f"  ✅ Created: {category.name}")
            created_count += 1
        else:
            print(f"  ➡️ Exists: {category.name}")

    # Create priorities if missing
    priorities = [
        {'name': 'Low', 'level': 1, 'color': '#17a2b8'},
        {'name': 'Medium', 'level': 2, 'color': '#ffc107'},
        {'name': 'High', 'level': 3, 'color': '#fd7e14'},
        {'name': 'Critical', 'level': 4, 'color': '#dc3545'},
        {'name': 'Emergency', 'level': 5, 'color': '#6f42c1'},
    ]

    priority_created_count = 0
    for priority_data in priorities:
        priority, created = Priority.objects.get_or_create(
            level=priority_data['level'],
            defaults=priority_data
        )
        if created:
            print(f"  ✅ Created priority: {priority.name}")
            priority_created_count += 1

    print(f"\n🎉 Done! Created {created_count} categories and {priority_created_count} priorities.")
    print(f"📊 Total categories: {Category.objects.count()}")
    print(f"📊 Total priorities: {Priority.objects.count()}")

if __name__ == '__main__':
    populate_categories()

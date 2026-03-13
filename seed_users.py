import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'strategy.settings')
django.setup()

from myapp.models import User

def create_test_users():
    # Admin
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(username='admin', password='adminpassword', role='admin', email='admin@example.com')
        print("Created admin user")

    # Aspirant
    if not User.objects.filter(username='aspirant').exists():
        User.objects.create_user(username='aspirant', password='aspirantpassword', role='aspirant', email='aspirant@example.com')
        print("Created aspirant user")

    # Staff
    if not User.objects.filter(username='staff').exists():
        User.objects.create_user(username='staff', password='staffpassword', role='staff', email='staff@example.com')
        print("Created staff user")

if __name__ == "__main__":
    create_test_users()

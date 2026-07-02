
from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = "List all users in the database"

    def handle(self, *args, **options):
        self.stdout.write("--- ALL USERS ---\n")
        
        users = User.objects.all().order_by("-created_at")
        
        if not users.exists():
            self.stdout.write(self.style.WARNING("No users found!"))
            return

        for user in users:
            self.stdout.write(f"📧 Email: {user.email}")
            self.stdout.write(f"👤 Name: {user.first_name} {user.last_name}")
            self.stdout.write(f"🏷️ Role: {user.role}")
            self.stdout.write(f"🔐 Is Staff: {'✅' if user.is_staff else '❌'}")
            self.stdout.write(f"👑 Is Superuser: {'✅' if user.is_superuser else '❌'}")
            self.stdout.write(f"🔓 Is Active: {'✅' if user.is_active else '❌'}")
            self.stdout.write(f"✅ Is Verified: {'✅' if user.is_verified else '❌'}")
            self.stdout.write("---\n")
        
        self.stdout.write(self.style.SUCCESS(f"Total users: {users.count()}"))


from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = "Reset a user's password and optionally mark as staff/admin"

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="Email address of the user")
        parser.add_argument("password", type=str, help="New password for the user")
        parser.add_argument(
            "--ensure-staff",
            action="store_true",
            help="Ensure the user has is_staff=True",
        )
        parser.add_argument(
            "--ensure-superuser",
            action="store_true",
            help="Ensure the user has is_superuser=True",
        )

    def handle(self, *args, **options):
        email = options["email"].lower().strip()
        password = options["password"]

        try:
            user = User.objects.get(email=email)
            user.set_password(password)

            if options["ensure_staff"]:
                user.is_staff = True
                self.stdout.write(f"✅ Set {email} as staff")

            if options["ensure_superuser"]:
                user.is_superuser = True
                user.role = User.Roles.super_admin
                self.stdout.write(f"✅ Set {email} as superuser (role: super_admin)")

            user.save()
            self.stdout.write(self.style.SUCCESS(f"Successfully updated password for {email}!"))

            self.stdout.write(f"\nUser details:")
            self.stdout.write(f"  Email: {user.email}")
            self.stdout.write(f"  Name: {user.first_name} {user.last_name}")
            self.stdout.write(f"  Role: {user.role}")
            self.stdout.write(f"  Is Staff: {user.is_staff}")
            self.stdout.write(f"  Is Superuser: {user.is_superuser}")
            self.stdout.write(f"  Is Active: {user.is_active}")

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User with email {email} does NOT exist!"))


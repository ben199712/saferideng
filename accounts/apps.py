from django.apps import AppConfig
from django.db.utils import OperationalError
from django.db.models.signals import post_migrate


def create_default_admin(sender, **kwargs):
    import os
    from .models import User

    # Default superuser credentials - from environment variables or use defaults
    DEFAULT_ADMIN_EMAIL = os.environ.get(
        "DJANGO_DEFAULT_ADMIN_EMAIL",
        "admin@rideguarde.com"
    )
    DEFAULT_ADMIN_PASSWORD = os.environ.get(
        "DJANGO_DEFAULT_ADMIN_PASSWORD",
        "ChangeMe123!"
    )
    DEFAULT_ADMIN_FIRST_NAME = os.environ.get(
        "DJANGO_DEFAULT_ADMIN_FIRST_NAME",
        "RideGuarde"
    )
    DEFAULT_ADMIN_LAST_NAME = os.environ.get(
        "DJANGO_DEFAULT_ADMIN_LAST_NAME",
        "Admin"
    )
    DEFAULT_ADMIN_PHONE = os.environ.get(
        "DJANGO_DEFAULT_ADMIN_PHONE",
        "000-000-0000"
    )

    try:
        if not User.objects.filter(email=DEFAULT_ADMIN_EMAIL).exists():
            print(f"Creating default admin user: {DEFAULT_ADMIN_EMAIL}")
            User.objects.create_superuser(
                email=DEFAULT_ADMIN_EMAIL,
                password=DEFAULT_ADMIN_PASSWORD,
                first_name=DEFAULT_ADMIN_FIRST_NAME,
                last_name=DEFAULT_ADMIN_LAST_NAME,
                phone_number=DEFAULT_ADMIN_PHONE
            )
            print(f"✅ Default admin created!")
        else:
            print(f"✅ Default admin already exists: {DEFAULT_ADMIN_EMAIL}")
    except OperationalError:
        # This happens if tables haven't been created yet - that's okay!
        print("⚠️  Database tables not ready yet - skipping default admin creation (will try again after migrations)")


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        # Connect the signal so it runs after migrations are complete
        post_migrate.connect(create_default_admin, sender=self)



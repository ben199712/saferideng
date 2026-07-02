from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        import os
        from django.conf import settings
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


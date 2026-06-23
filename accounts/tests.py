from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import User


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class AuthViewTests(TestCase):
    def test_password_reset_urls_reverse(self):
        self.assertEqual(reverse("forgot_password"), "/forgot-password/")
        self.assertEqual(reverse("password_reset_done"), "/password-reset/done/")
        self.assertEqual(reverse("password_reset_complete"), "/reset/done/")

    def test_login_redirects_driver_to_profile(self):
        user = User.objects.create_user(
            email="driver@example.com",
            password="password123",
            first_name="Driver",
            last_name="User",
            phone_number="+2348000000000",
        )
        client = Client()

        response = client.post(
            reverse("login"),
            {
                "username": user.email,
                "password": "password123",
                "remember_me": True,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("driver_profile"))

    def test_login_redirects_admin_to_dashboard(self):
        user = User.objects.create_user(
            email="admin@example.com",
            password="password123",
            first_name="Admin",
            last_name="User",
            phone_number="+2348000000001",
            role=User.Roles.admin,
            is_staff=True,
        )
        client = Client()

        response = client.post(
            reverse("login"),
            {
                "username": user.email,
                "password": "password123",
                "remember_me": True,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard_home"))

    def test_create_superuser_is_staff_for_admin_login(self):
        user = User.objects.create_superuser(
            email="NewAdmin@example.com",
            password="password123",
            first_name="New",
            last_name="Admin",
            phone_number="+2348000000003",
        )

        self.assertEqual(user.email, "newadmin@example.com")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertEqual(user.role, User.Roles.super_admin)

    def test_register_creates_unverified_driver(self):
        response = Client().post(
            reverse("register"),
            {
                "first_name": "New",
                "last_name": "Driver",
                "email": "new.driver@example.com",
                "phone_number": "+2348000000002",
                "password1": "password123",
                "password2": "password123",
            },
        )

        user = User.objects.get(email="new.driver@example.com")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login"))
        self.assertEqual(user.role, User.Roles.driver)
        self.assertFalse(user.is_verified)

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.views import (
    PasswordResetCompleteView as DjangoPasswordResetCompleteView,
    PasswordResetConfirmView as DjangoPasswordResetConfirmView,
    PasswordResetDoneView as DjangoPasswordResetDoneView,
    PasswordResetView,
)
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView

from .forms import LoginForm, RegisterForm
from .models import User


def redirect_after_login(request):
    user = request.user
    if user.role == User.Roles.driver:
        return redirect("driver_profile")
    return redirect("dashboard_home")


def is_admin_user(user):
    return user.is_authenticated and (
        user.is_superuser or user.role in (User.Roles.super_admin, User.Roles.admin)
    )


class LoginView(FormView):
    template_name = "auth/login.html"
    form_class = LoginForm
    success_url = reverse_lazy("dashboard_home")

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)

        if not form.cleaned_data.get("remember_me", False):
            self.request.session.set_expiry(0)
        else:
            self.request.session.set_expiry(60 * 60 * 24 * 30)

        return redirect_after_login(self.request)


class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect("login")


class RegisterView(FormView):
    template_name = "auth/register.html"
    form_class = RegisterForm
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, "Account created. Please login.")
        return super().form_valid(form)


class ForgotPasswordView(PasswordResetView):
    template_name = "auth/forgot_password.html"
    email_template_name = "auth/password_reset_email.txt"
    subject_template_name = "auth/password_reset_subject.txt"
    success_url = reverse_lazy("password_reset_done")


class RideGuardePasswordResetDoneView(DjangoPasswordResetDoneView):
    template_name = "auth/password_reset_done.html"


class RideGuardePasswordResetConfirmView(DjangoPasswordResetConfirmView):
    template_name = "auth/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")


class RideGuardePasswordResetCompleteView(DjangoPasswordResetCompleteView):
    template_name = "auth/password_reset_complete.html"

from django.urls import path

from .views import (
    ForgotPasswordView,
    LoginView,
    LogoutView,
    RegisterView,
    SafeRidePasswordResetCompleteView,
    SafeRidePasswordResetConfirmView,
    SafeRidePasswordResetDoneView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot_password"),
    path("password-reset/done/", SafeRidePasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", SafeRidePasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", SafeRidePasswordResetCompleteView.as_view(), name="password_reset_complete"),
]

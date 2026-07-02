from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from accounts.models import User

def is_admin_user(user):
    return user.is_authenticated and (
        user.is_superuser or user.role in (User.Roles.super_admin, User.Roles.admin)
    )

class AdminRequiredMixin(AccessMixin):
    @method_decorator(user_passes_test(is_admin_user))
    def dispatch(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

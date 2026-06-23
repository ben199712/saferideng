from django.urls import path

from .views import DashboardHomeView, DriverApprovalView

urlpatterns = [
    path("", DashboardHomeView.as_view(), name="dashboard_home"),
    path("driver/<int:pk>/approval/", DriverApprovalView.as_view(), name="driver_approval"),
]


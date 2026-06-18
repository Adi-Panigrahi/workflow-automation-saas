from django.urls import path
from .views import (
    MeView,
    AdminDashboardView,
    ManagerDashboardView,
    EmployeeDashboardView,
)

urlpatterns = [

    path(
        "me/",
        MeView.as_view(),
    ),

    path(
        "admin/",
        AdminDashboardView.as_view(),
    ),

    path(
        "manager/",
        ManagerDashboardView.as_view(),
    ),

    path(
        "employee/",
        EmployeeDashboardView.as_view(),
    ),
]
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    MeView,
    AdminDashboardView,
    ManagerDashboardView,
    EmployeeDashboardView,
    UserViewSet,
)

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")

urlpatterns = router.urls + [

    path(
        "me/",
        MeView.as_view(),
    ),

    path(
        "admin/",
        AdminDashboardView.as_view(),
        name="admin-dashboard",
    ),

    path(
        "manager/",
        ManagerDashboardView.as_view(),
        name="manager-dashboard",
    ),

    path(
        "employee/",
        EmployeeDashboardView.as_view(),
        name="employee-dashboard",
    ),
]

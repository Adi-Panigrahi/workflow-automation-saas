from django.urls import path

from .views import MeView, AdminDashboardView

urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path(
    "api/admin/dashboard/",
    AdminDashboardView.as_view(),
)
]
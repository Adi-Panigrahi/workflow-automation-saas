from django.urls import path
from .views import health_check
from .views import OrganizationListCreateView, OrganizationDetailView
urlpatterns = [
    path("health/", health_check),
    path("organizations/",OrganizationListCreateView.as_view(),name="organizations"),
    path("organizations/<int:pk>/",OrganizationDetailView.as_view(),name="organization-detail",),
]
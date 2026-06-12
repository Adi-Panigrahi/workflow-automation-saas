from django.urls import path
from .views import health_check
from .views import OrganizationListCreateView
urlpatterns = [
    path("health/", health_check),
    path("organizations/",OrganizationListCreateView.as_view(),name="organizations"),
]
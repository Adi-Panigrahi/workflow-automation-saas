from django.contrib import admin
from django.urls import include, path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/", include("core.urls")),

    path(
        "api/auth/login/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),

    path(
        "api/auth/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),

    path(
        "api/auth/",
        include("accounts.urls"),
    ),

    path(
        "api/",
        include("workflow_instances.urls"),
    ),

    path(
        "api/",
        include("workflows.urls"),
    ),

    path(
        "api/",
        include("departments.urls"),
    ),

    path(
        "api/",
        include("approvals.urls"),
    ),
]

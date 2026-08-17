from django.contrib import admin

from .models import Approval


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "workflow_instance",
        "workflow_step",
        "assigned_to",
        "status",
        "approved_at",
        "created_at",
    )

    list_filter = (
        "status",
        "workflow_step",
        "created_at",
    )

    search_fields = (
        "assigned_to__email",
        "workflow_instance__workflow__name",
        "comments",
    )

    readonly_fields = (
        "approved_at",
        "created_at",
        "updated_at",
    )

    ordering = (
        "-created_at",
    )

    list_per_page = 25
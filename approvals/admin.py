from django.contrib import admin
from .models import Approval


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = (
        "workflow_instance",
        "workflow_step",
        "assigned_to",
        "status",
        "approved_at",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "assigned_to__email",
    )
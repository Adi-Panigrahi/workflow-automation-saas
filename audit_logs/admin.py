from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "action",
        "workflow_instance",
        "actor",
        "previous_status",
        "new_status",
        "created_at",
    )
    list_filter = ("action", "organization", "created_at")
    search_fields = ("workflow_instance__id", "actor__email")
    readonly_fields = (
        "organization",
        "workflow_instance",
        "approval",
        "actor",
        "action",
        "previous_status",
        "new_status",
        "metadata",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

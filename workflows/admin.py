from django.contrib import admin

from .models import WorkflowStep, WorkflowTemplate


@admin.register(WorkflowTemplate)
class WorkflowTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "is_active", "created_at")
    list_filter = ("is_active", "organization")
    search_fields = ("name", "organization__name")

    def has_change_permission(self, request, obj=None):
        if obj and obj.instances.exists():
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.instances.exists():
            return False
        return super().has_delete_permission(request, obj)


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = ("name", "workflow", "order", "role_required", "assigned_to")
    list_filter = ("role_required",)
    search_fields = ("name", "workflow__name", "assigned_to__email")

    def has_change_permission(self, request, obj=None):
        if obj and obj.workflow.instances.exists():
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.workflow.instances.exists():
            return False
        return super().has_delete_permission(request, obj)

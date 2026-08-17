from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    ACTION_WORKFLOW_STARTED = "WORKFLOW_STARTED"
    ACTION_APPROVAL_APPROVED = "APPROVAL_APPROVED"
    ACTION_APPROVAL_REJECTED = "APPROVAL_REJECTED"

    ACTION_CHOICES = (
        (ACTION_WORKFLOW_STARTED, "Workflow Started"),
        (ACTION_APPROVAL_APPROVED, "Approval Approved"),
        (ACTION_APPROVAL_REJECTED, "Approval Rejected"),
    )

    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        related_name="audit_logs",
    )
    workflow_instance = models.ForeignKey(
        "workflow_instances.WorkflowInstance",
        on_delete=models.CASCADE,
        related_name="audit_logs",
    )
    approval = models.ForeignKey(
        "approvals.Approval",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} on workflow instance {self.workflow_instance_id}"

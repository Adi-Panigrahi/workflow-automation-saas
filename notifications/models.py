from django.conf import settings
from django.db import models


class Notification(models.Model):
    TYPE_APPROVAL_REQUESTED = "APPROVAL_REQUESTED"
    TYPE_APPROVAL_REASSIGNED = "APPROVAL_REASSIGNED"
    TYPE_WORKFLOW_COMPLETED = "WORKFLOW_COMPLETED"
    TYPE_WORKFLOW_REJECTED = "WORKFLOW_REJECTED"

    TYPE_CHOICES = (
        (TYPE_APPROVAL_REQUESTED, "Approval Requested"),
        (TYPE_APPROVAL_REASSIGNED, "Approval Reassigned"),
        (TYPE_WORKFLOW_COMPLETED, "Workflow Completed"),
        (TYPE_WORKFLOW_REJECTED, "Workflow Rejected"),
    )

    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    workflow_instance = models.ForeignKey(
        "workflow_instances.WorkflowInstance",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    approval = models.ForeignKey(
        "approvals.Approval",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    notification_type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["recipient", "read_at", "created_at"],
                name="notification_recipient_read_created_idx",
            ),
        ]

    def __str__(self):
        return f"{self.notification_type} for {self.recipient.email}"

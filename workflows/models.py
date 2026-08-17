from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from core.models import Organization


class WorkflowTemplate(models.Model):

    name = models.CharField(
        max_length=255
    )

    description = models.TextField(
        blank=True
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="workflow_templates"
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name

class WorkflowStep(models.Model):

    workflow = models.ForeignKey(
        WorkflowTemplate,
        on_delete=models.CASCADE,
        related_name="steps"
    )

    name = models.CharField(
        max_length=255
    )

    order = models.PositiveIntegerField()

    role_required = models.CharField(
        max_length=20
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_workflow_steps",
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def clean(self):
        super().clean()

        if not self.assigned_to_id:
            return

        if self.assigned_to.organization_id != self.workflow.organization_id:
            raise ValidationError(
                {
                    "assigned_to": (
                        "The assigned approver must belong to the workflow's "
                        "organization."
                    )
                }
            )

        if self.assigned_to.role != self.role_required:
            raise ValidationError(
                {
                    "assigned_to": (
                        "The assigned approver must have the role required by "
                        "this workflow step."
                    )
                }
            )

    def __str__(self):
        return f"{self.workflow.name} - {self.name}"

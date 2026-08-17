from django.core.exceptions import ValidationError
from django.db import transaction

from workflow_instances.models import WorkflowInstance
from workflows.models import WorkflowStep

from .models import Approval


class WorkflowConfigurationError(Exception):
    """Raised when a workflow cannot be started from its configured steps."""


class InvalidWorkflowStateError(Exception):
    """Raised when an operation is not valid for the workflow's current state."""


@transaction.atomic
def start_workflow(instance: WorkflowInstance) -> Approval:
    """Create the first pending approval and move an instance into progress."""
    locked_instance = (
        WorkflowInstance.objects.select_for_update()
        .select_related("workflow", "submitted_by")
        .get(pk=instance.pk)
    )

    if locked_instance.status != "PENDING":
        raise InvalidWorkflowStateError(
            "Only pending workflow instances can be started."
        )

    if (
        locked_instance.submitted_by.organization_id
        != locked_instance.workflow.organization_id
    ):
        raise WorkflowConfigurationError(
            "The submitting user must belong to the workflow organization."
        )

    first_step = (
        WorkflowStep.objects.select_related("workflow", "assigned_to")
        .filter(workflow=locked_instance.workflow)
        .order_by("order", "id")
        .first()
    )

    if not first_step:
        raise WorkflowConfigurationError(
            "A workflow template needs at least one step before it can start."
        )

    if not first_step.assigned_to_id:
        raise WorkflowConfigurationError(
            "The first workflow step must have an assigned approver."
        )

    try:
        first_step.full_clean()
    except ValidationError as error:
        raise WorkflowConfigurationError(error.message_dict) from error

    approval = Approval.objects.create(
        workflow_instance=locked_instance,
        workflow_step=first_step,
        assigned_to=first_step.assigned_to,
    )

    locked_instance.current_step = first_step
    locked_instance.status = "IN_PROGRESS"
    locked_instance.save(update_fields=["current_step", "status"])

    return approval

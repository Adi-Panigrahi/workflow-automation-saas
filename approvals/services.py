from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from audit_logs.models import AuditLog
from audit_logs.services import log_workflow_event
from workflow_instances.models import WorkflowInstance
from workflows.models import WorkflowStep

from .models import Approval


class WorkflowConfigurationError(Exception):
    """Raised when a workflow cannot be started from its configured steps."""


class InvalidWorkflowStateError(Exception):
    """Raised when an operation is not valid for the workflow's current state."""


def _get_locked_approval(approval_id: int) -> Approval:
    return (
        Approval.objects.select_for_update()
        .select_related(
            "assigned_to",
            "workflow_step__workflow",
            "workflow_instance__workflow",
        )
        .get(pk=approval_id)
    )


def _validate_approval_action(approval: Approval, actor) -> None:
    instance = approval.workflow_instance

    if approval.assigned_to_id != actor.id:
        raise PermissionDenied("This approval is assigned to another user.")

    if instance.workflow.organization_id != actor.organization_id:
        raise PermissionDenied("You cannot act on another organization's approval.")

    if approval.workflow_step.role_required != actor.role:
        raise PermissionDenied("Your role cannot act on this approval.")

    if approval.status != "PENDING":
        raise InvalidWorkflowStateError("This approval has already been resolved.")

    if instance.status != "IN_PROGRESS":
        raise InvalidWorkflowStateError("This workflow is not in progress.")

    if instance.current_step_id != approval.workflow_step_id:
        raise InvalidWorkflowStateError("This approval is not the current step.")


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

    log_workflow_event(
        workflow_instance=locked_instance,
        actor=locked_instance.submitted_by,
        action=AuditLog.ACTION_WORKFLOW_STARTED,
        previous_status="PENDING",
        new_status="IN_PROGRESS",
        approval=approval,
        metadata={"step_id": first_step.id},
    )

    return approval


@transaction.atomic
def approve_approval(approval: Approval, actor, comments: str = "") -> Approval:
    """Approve the current step and advance or complete its workflow."""
    locked_approval = _get_locked_approval(approval.pk)
    _validate_approval_action(locked_approval, actor)

    locked_approval.status = "APPROVED"
    locked_approval.comments = comments
    locked_approval.approved_at = timezone.now()
    locked_approval.save(update_fields=["status", "comments", "approved_at", "updated_at"])

    instance = locked_approval.workflow_instance
    next_step = (
        WorkflowStep.objects.select_related("workflow", "assigned_to")
        .filter(
            workflow=instance.workflow,
            order__gt=locked_approval.workflow_step.order,
        )
        .order_by("order", "id")
        .first()
    )

    if not next_step:
        instance.status = "COMPLETED"
        instance.save(update_fields=["status"])
        log_workflow_event(
            workflow_instance=instance,
            actor=actor,
            action=AuditLog.ACTION_APPROVAL_APPROVED,
            previous_status="IN_PROGRESS",
            new_status="COMPLETED",
            approval=locked_approval,
        )
        return locked_approval

    if not next_step.assigned_to_id:
        raise WorkflowConfigurationError(
            "The next workflow step must have an assigned approver."
        )

    try:
        next_step.full_clean()
    except ValidationError as error:
        raise WorkflowConfigurationError(error.message_dict) from error

    Approval.objects.create(
        workflow_instance=instance,
        workflow_step=next_step,
        assigned_to=next_step.assigned_to,
    )
    instance.current_step = next_step
    instance.save(update_fields=["current_step"])
    log_workflow_event(
        workflow_instance=instance,
        actor=actor,
        action=AuditLog.ACTION_APPROVAL_APPROVED,
        previous_status="IN_PROGRESS",
        new_status="IN_PROGRESS",
        approval=locked_approval,
        metadata={"next_step_id": next_step.id},
    )
    return locked_approval


@transaction.atomic
def reject_approval(approval: Approval, actor, comments: str = "") -> Approval:
    """Reject the current step and stop the workflow."""
    locked_approval = _get_locked_approval(approval.pk)
    _validate_approval_action(locked_approval, actor)

    locked_approval.status = "REJECTED"
    locked_approval.comments = comments
    locked_approval.approved_at = timezone.now()
    locked_approval.save(update_fields=["status", "comments", "approved_at", "updated_at"])

    instance = locked_approval.workflow_instance
    instance.status = "REJECTED"
    instance.save(update_fields=["status"])
    log_workflow_event(
        workflow_instance=instance,
        actor=actor,
        action=AuditLog.ACTION_APPROVAL_REJECTED,
        previous_status="IN_PROGRESS",
        new_status="REJECTED",
        approval=locked_approval,
    )
    return locked_approval

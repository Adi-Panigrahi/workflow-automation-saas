from .models import AuditLog


def log_workflow_event(
    *,
    workflow_instance,
    actor,
    action,
    previous_status,
    new_status,
    approval=None,
    metadata=None,
):
    """Create an append-only audit record for a workflow state transition."""
    return AuditLog.objects.create(
        organization=workflow_instance.workflow.organization,
        workflow_instance=workflow_instance,
        approval=approval,
        actor=actor,
        action=action,
        previous_status=previous_status,
        new_status=new_status,
        metadata=metadata or {},
    )

from .models import Notification


def create_notification(
    *,
    recipient,
    workflow_instance,
    notification_type,
    title,
    message="",
    approval=None,
    metadata=None,
):
    """Create an in-app notification for a user in the workflow organization."""
    if not recipient.is_active:
        return None

    if recipient.organization_id != workflow_instance.workflow.organization_id:
        raise ValueError("Notification recipients must belong to the workflow organization.")

    return Notification.objects.create(
        organization=workflow_instance.workflow.organization,
        recipient=recipient,
        workflow_instance=workflow_instance,
        approval=approval,
        notification_type=notification_type,
        title=title,
        message=message,
        metadata=metadata or {},
    )

from django.db.models import Count, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsAdmin
from approvals.serializers import ApprovalSerializer
from approvals.services import InvalidWorkflowStateError, cancel_workflow
from audit_logs.serializers import AuditLogSerializer
from .models import WorkflowInstance
from .serializers import WorkflowInstanceSerializer


class WorkflowInstanceViewSet(viewsets.ModelViewSet):
    serializer_class = WorkflowInstanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = WorkflowInstance.objects.select_related(
                "workflow",
                "submitted_by",
                "current_step",
            ).filter(workflow__organization=self.request.user.organization)

        if self.request.user.role != "ADMIN":
            queryset = queryset.filter(
                Q(submitted_by=self.request.user)
                | Q(approvals__assigned_to=self.request.user)
            ).distinct()

        workflow_id = self.request.query_params.get("workflow")
        if workflow_id:
            queryset = queryset.filter(workflow_id=workflow_id)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            valid_statuses = {value for value, _ in WorkflowInstance.STATUS_CHOICES}
            if status_filter not in valid_statuses:
                raise ValidationError(
                    {"status": "Use a valid workflow-instance status."}
                )
            queryset = queryset.filter(status=status_filter)

        return queryset.order_by("-created_at")

    def update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Workflow requests cannot be edited after submission."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Workflow requests cannot be deleted."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        instance = self.get_object()
        try:
            cancelled_instance = cancel_workflow(instance, request.user)
        except InvalidWorkflowStateError as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(self.get_serializer(cancelled_instance).data)

    @action(detail=True, methods=["get"])
    def timeline(self, request, pk=None):
        """Return ordered approval and audit history for an accessible request."""
        instance = self.get_object()
        approvals = instance.approvals.select_related(
            "workflow_step", "assigned_to"
        ).order_by("created_at", "id")
        events = instance.audit_logs.select_related("actor", "approval").order_by(
            "created_at", "id"
        )

        return Response(
            {
                "workflow_instance": instance.pk,
                "status": instance.status,
                "current_step": instance.current_step_id,
                "approvals": ApprovalSerializer(approvals, many=True).data,
                "events": AuditLogSerializer(events, many=True).data,
            }
        )

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated, IsAdmin])
    def analytics(self, request):
        """Return tenant-level request volumes for the administrator dashboard."""
        instances = WorkflowInstance.objects.filter(
            workflow__organization=request.user.organization
        )
        status_counts = {status: 0 for status, _ in WorkflowInstance.STATUS_CHOICES}
        status_counts.update(
            {
                row["status"]: row["count"]
                for row in instances.values("status").annotate(count=Count("id"))
            }
        )
        workflows = instances.values("workflow_id", "workflow__name").annotate(
            total=Count("id", distinct=True),
            in_progress=Count("id", filter=Q(status="IN_PROGRESS"), distinct=True),
            completed=Count("id", filter=Q(status="COMPLETED"), distinct=True),
            rejected=Count("id", filter=Q(status="REJECTED"), distinct=True),
            cancelled=Count("id", filter=Q(status="CANCELLED"), distinct=True),
            pending_approvals=Count(
                "approvals",
                filter=Q(approvals__status="PENDING"),
            ),
        ).order_by("workflow__name", "workflow_id")

        return Response(
            {
                "status_counts": status_counts,
                "workflows": list(workflows),
            }
        )

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Approval
from .serializers import (
    ApprovalActionSerializer,
    ApprovalReassignSerializer,
    ApprovalSerializer,
)
from .services import (
    InvalidWorkflowStateError,
    WorkflowConfigurationError,
    approve_approval,
    reassign_approval,
    reject_approval,
)


class ApprovalViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ApprovalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = (
            Approval.objects.select_related(
                "workflow_instance__workflow",
                "workflow_step",
                "assigned_to",
            )
            .filter(assigned_to=self.request.user)
            .order_by("-created_at")
        )

        workflow_instance_id = self.request.query_params.get("workflow_instance")
        if workflow_instance_id:
            queryset = queryset.filter(workflow_instance_id=workflow_instance_id)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            valid_statuses = {value for value, _ in Approval.STATUS_CHOICES}
            if status_filter not in valid_statuses:
                raise ValidationError({"status": "Use a valid approval status."})
            queryset = queryset.filter(status=status_filter)

        return queryset

    def _resolve(self, request, operation):
        approval = self.get_object()
        serializer = ApprovalActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            resolved_approval = operation(
                approval=approval,
                actor=request.user,
                comments=serializer.validated_data.get("comments", ""),
            )
        except (InvalidWorkflowStateError, WorkflowConfigurationError) as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resolved_approval.refresh_from_db()
        workflow_instance = resolved_approval.workflow_instance
        workflow_instance.refresh_from_db()

        return Response(
            {
                "message": "Approval processed successfully.",
                "approval": ApprovalSerializer(resolved_approval).data,
                "workflow_status": workflow_instance.status,
                "next_step": workflow_instance.current_step_id,
            }
        )

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._resolve(request, approve_approval)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._resolve(request, reject_approval)

    @action(detail=True, methods=["post"])
    def reassign(self, request, pk=None):
        approval = self.get_object()
        serializer = ApprovalReassignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            reassigned_approval = reassign_approval(
                approval=approval,
                actor=request.user,
                assigned_to=serializer.validated_data["assigned_to"],
                comments=serializer.validated_data.get("comments", ""),
            )
        except (InvalidWorkflowStateError, WorkflowConfigurationError) as error:
            return Response(
                {"detail": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(ApprovalSerializer(reassigned_approval).data)

# Create your views here.

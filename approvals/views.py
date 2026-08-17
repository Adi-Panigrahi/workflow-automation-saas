from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Approval
from .serializers import ApprovalActionSerializer, ApprovalSerializer
from .services import (
    InvalidWorkflowStateError,
    WorkflowConfigurationError,
    approve_approval,
    reject_approval,
)


class ApprovalViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ApprovalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Approval.objects.select_related(
                "workflow_instance__workflow",
                "workflow_step",
                "assigned_to",
            )
            .filter(assigned_to=self.request.user)
            .order_by("-created_at")
        )

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

# Create your views here.

from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from approvals.services import InvalidWorkflowStateError, cancel_workflow
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

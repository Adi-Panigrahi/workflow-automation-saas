from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import WorkflowInstance
from .serializers import WorkflowInstanceSerializer


class WorkflowInstanceViewSet(viewsets.ModelViewSet):
    serializer_class = WorkflowInstanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            WorkflowInstance.objects.select_related(
                "workflow",
                "submitted_by",
                "current_step",
            )
            .filter(workflow__organization=self.request.user.organization)
            .order_by("-created_at")
        )

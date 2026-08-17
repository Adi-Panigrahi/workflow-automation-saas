from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsAdmin

from .models import WorkflowStep, WorkflowTemplate
from .serializers import WorkflowStepSerializer, WorkflowTemplateSerializer


class OrganizationWorkflowQuerySetMixin:
    def get_organization(self):
        return self.request.user.organization


class WorkflowTemplateViewSet(OrganizationWorkflowQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = WorkflowTemplateSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return WorkflowTemplate.objects.filter(
            organization=self.get_organization()
        ).order_by("name")

    def perform_create(self, serializer):
        serializer.save(organization=self.get_organization())


class WorkflowStepViewSet(OrganizationWorkflowQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = WorkflowStepSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return WorkflowStep.objects.select_related(
            "workflow",
            "assigned_to",
        ).filter(
            workflow__organization=self.get_organization()
        ).order_by("workflow_id", "order", "id")

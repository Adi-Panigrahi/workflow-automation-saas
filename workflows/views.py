from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsAdmin

from .models import WorkflowStep, WorkflowTemplate
from .serializers import (
    WorkflowCloneSerializer,
    WorkflowStepSerializer,
    WorkflowTemplateSerializer,
)


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

    def perform_update(self, serializer):
        template = self.get_object()
        changed_fields = set(self.request.data) - {
            "id",
            "organization",
            "created_at",
            "updated_at",
        }
        if template.instances.exists() and changed_fields - {"is_active"}:
            raise ValidationError(
                {
                    "detail": (
                        "This workflow has submitted requests and is locked. "
                        "Clone it to create an editable revision."
                    )
                }
            )
        serializer.save()

    def perform_destroy(self, instance):
        if instance.instances.exists():
            raise ValidationError(
                {
                    "detail": (
                        "A workflow with submitted requests cannot be deleted. "
                        "Deactivate it instead."
                    )
                }
            )
        instance.delete()

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def clone(self, request, pk=None):
        source = self.get_object()
        serializer = WorkflowCloneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        clone = WorkflowTemplate.objects.create(
            organization=self.get_organization(),
            name=serializer.validated_data["name"],
            description=source.description,
            request_schema=source.request_schema,
            is_active=serializer.validated_data["is_active"],
        )
        steps = source.steps.select_related("assigned_to").order_by("order", "id")
        for step in steps:
            if not step.assigned_to_id:
                raise ValidationError(
                    {"detail": "Cannot clone a workflow step without an approver."}
                )
            cloned_step = WorkflowStep(
                workflow=clone,
                name=step.name,
                order=step.order,
                role_required=step.role_required,
                assigned_to=step.assigned_to,
            )
            try:
                cloned_step.full_clean()
            except DjangoValidationError as error:
                raise ValidationError(
                    {"detail": f"Cannot clone an invalid workflow step: {error}."}
                ) from error
            cloned_step.save()

        return Response(
            WorkflowTemplateSerializer(clone).data,
            status=status.HTTP_201_CREATED,
        )


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

    def perform_create(self, serializer):
        workflow = serializer.validated_data["workflow"]
        if workflow.instances.exists():
            raise ValidationError(
                {"detail": "Workflow steps are locked after the first request is submitted."}
            )
        serializer.save()

    def perform_update(self, serializer):
        if self.get_object().workflow.instances.exists():
            raise ValidationError(
                {"detail": "Workflow steps are locked after the first request is submitted."}
            )
        serializer.save()

    def perform_destroy(self, instance):
        if instance.workflow.instances.exists():
            raise ValidationError(
                {"detail": "Workflow steps are locked after the first request is submitted."}
            )
        instance.delete()

from django.db import transaction
from rest_framework import serializers

from approvals.services import WorkflowConfigurationError, start_workflow

from .models import WorkflowInstance


class WorkflowInstanceSerializer(serializers.ModelSerializer):

    submitted_by = serializers.PrimaryKeyRelatedField(read_only=True)
    current_step = serializers.PrimaryKeyRelatedField(read_only=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = WorkflowInstance
        fields = [
            "id",
            "workflow",
            "submitted_by",
            "request_data",
            "status",
            "current_step",
            "created_at",
        ]

    def validate_workflow(self, workflow):
        user = self.context["request"].user

        if workflow.organization_id != user.organization_id:
            raise serializers.ValidationError(
                "You cannot submit a request for another organization."
            )

        if not workflow.is_active:
            raise serializers.ValidationError("This workflow is inactive.")

        return workflow

    @transaction.atomic
    def create(self, validated_data):
        instance = WorkflowInstance.objects.create(
            submitted_by=self.context["request"].user,
            **validated_data,
        )

        try:
            start_workflow(instance)
        except WorkflowConfigurationError as error:
            raise serializers.ValidationError({"workflow": error.args[0]}) from error

        instance.refresh_from_db()
        return instance

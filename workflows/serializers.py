from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import WorkflowStep, WorkflowTemplate


User = get_user_model()


class WorkflowTemplateSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = WorkflowTemplate
        fields = [
            "id",
            "name",
            "description",
            "organization",
            "is_active",
            "request_schema",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]

    def validate_request_schema(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("The request schema must be an object.")

        required_fields = value.get("required", [])
        if not isinstance(required_fields, list) or not all(
            isinstance(field, str) and field.strip() for field in required_fields
        ):
            raise serializers.ValidationError(
                "The 'required' value must be a list of non-empty field names."
            )

        if len(required_fields) != len(set(required_fields)):
            raise serializers.ValidationError(
                "The 'required' field names must not contain duplicates."
            )

        return value


class WorkflowCloneSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    is_active = serializers.BooleanField(required=False, default=True)


class WorkflowStepSerializer(serializers.ModelSerializer):
    role_required = serializers.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = WorkflowStep
        fields = [
            "id",
            "workflow",
            "name",
            "order",
            "role_required",
            "assigned_to",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        workflow = attrs.get("workflow", self.instance.workflow if self.instance else None)
        assigned_to = attrs.get(
            "assigned_to",
            self.instance.assigned_to if self.instance else None,
        )
        role_required = attrs.get(
            "role_required",
            self.instance.role_required if self.instance else None,
        )
        step_order = attrs.get("order", self.instance.order if self.instance else None)

        if workflow.organization_id != self.context["request"].user.organization_id:
            raise serializers.ValidationError(
                {"workflow": "You cannot configure another organization's workflow."}
            )

        if not assigned_to:
            raise serializers.ValidationError(
                {"assigned_to": "Every workflow step needs an assigned approver."}
            )

        if assigned_to.organization_id != workflow.organization_id:
            raise serializers.ValidationError(
                {"assigned_to": "The approver must belong to this organization."}
            )

        if assigned_to.role != role_required:
            raise serializers.ValidationError(
                {"assigned_to": "The approver must have the required role."}
            )

        duplicate_order = WorkflowStep.objects.filter(
            workflow=workflow,
            order=step_order,
        )
        if self.instance:
            duplicate_order = duplicate_order.exclude(pk=self.instance.pk)

        if duplicate_order.exists():
            raise serializers.ValidationError(
                {"order": "A workflow cannot have two steps with the same order."}
            )

        return attrs

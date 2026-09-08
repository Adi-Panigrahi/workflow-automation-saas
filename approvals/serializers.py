from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Approval


class ApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Approval
        fields = [
            "id",
            "workflow_instance",
            "workflow_step",
            "assigned_to",
            "status",
            "comments",
            "approved_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ApprovalActionSerializer(serializers.Serializer):
    comments = serializers.CharField(required=False, allow_blank=True, max_length=5000)


class ApprovalReassignSerializer(ApprovalActionSerializer):
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all())

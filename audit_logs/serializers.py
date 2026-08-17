from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id",
            "organization",
            "workflow_instance",
            "approval",
            "actor",
            "action",
            "previous_status",
            "new_status",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields

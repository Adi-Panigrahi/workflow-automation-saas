from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "workflow_instance",
            "approval",
            "notification_type",
            "title",
            "message",
            "metadata",
            "read_at",
            "created_at",
        ]
        read_only_fields = fields

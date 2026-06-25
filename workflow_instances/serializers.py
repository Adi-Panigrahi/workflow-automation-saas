from rest_framework import serializers
from .models import WorkflowInstance


class WorkflowInstanceSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkflowInstance
        fields = "__all__"
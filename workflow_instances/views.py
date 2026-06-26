from rest_framework import viewsets
from .models import WorkflowInstance
from .serializers import WorkflowInstanceSerializer


class WorkflowInstanceViewSet(viewsets.ModelViewSet):
    queryset = WorkflowInstance.objects.all()
    serializer_class = WorkflowInstanceSerializer
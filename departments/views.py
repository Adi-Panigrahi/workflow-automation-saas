from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsAdmin

from .models import Department
from .serializers import DepartmentSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return Department.objects.filter(
            organization=self.request.user.organization
        ).order_by("name")

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)

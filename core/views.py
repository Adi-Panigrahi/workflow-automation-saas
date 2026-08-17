from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from .models import Organization
from .serializers import OrganizationSerializer

@api_view(['GET'])
def health_check(request):
    return Response({
        "status": "running"
    })

class OrganizationListCreateView(ListCreateAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Organization.objects.all()

        if not self.request.user.organization_id:
            return Organization.objects.none()

        return Organization.objects.filter(pk=self.request.user.organization_id)

    def perform_create(self, serializer):
        if not self.request.user.is_superuser:
            raise PermissionDenied(
                "Only platform administrators can create organizations."
            )

        serializer.save()


class OrganizationDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Organization.objects.all()

        if not self.request.user.organization_id:
            return Organization.objects.none()

        return Organization.objects.filter(pk=self.request.user.organization_id)

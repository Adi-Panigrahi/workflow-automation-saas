from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.generics import ListCreateAPIView
from .models import Organization
from .serializers import OrganizationSerializer

@api_view(['GET'])
def health_check(request):
    return Response({
        "status": "running"
    })

class OrganizationListCreateView(ListCreateAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
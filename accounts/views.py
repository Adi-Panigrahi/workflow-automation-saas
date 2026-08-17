from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from approvals.models import Approval
from departments.models import Department
from workflow_instances.models import WorkflowInstance
from workflows.models import WorkflowTemplate
from .models import User
from .serializers import UserManagementSerializer, UserSerializer
from .permissions import (
    IsAdmin,
    IsManager,
    IsEmployee,
)

class MeView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        serializer = UserSerializer(request.user)

        return Response(serializer.data)
    
class AdminDashboardView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]

    def get(self, request):

        return Response(
            {
                "organization_id": request.user.organization_id,
                "users": request.user.organization.users.count(),
                "departments": Department.objects.filter(
                    organization=request.user.organization
                ).count(),
                "workflows": WorkflowTemplate.objects.filter(
                    organization=request.user.organization
                ).count(),
                "workflow_instances": WorkflowInstance.objects.filter(
                    workflow__organization=request.user.organization
                ).count(),
                "pending_approvals": Approval.objects.filter(
                    workflow_instance__workflow__organization=request.user.organization,
                    status="PENDING",
                ).count(),
            }
        )

class ManagerDashboardView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsManager,
    ]

    def get(self, request):

        return Response(
            {
                "pending_approvals": Approval.objects.filter(
                    assigned_to=request.user,
                    status="PENDING",
                ).count(),
                "approved_approvals": Approval.objects.filter(
                    assigned_to=request.user,
                    status="APPROVED",
                ).count(),
                "rejected_approvals": Approval.objects.filter(
                    assigned_to=request.user,
                    status="REJECTED",
                ).count(),
            }
        )
        
class EmployeeDashboardView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsEmployee,
    ]

    def get(self, request):

        return Response(
            {
                "in_progress_requests": WorkflowInstance.objects.filter(
                    submitted_by=request.user,
                    status="IN_PROGRESS",
                ).count(),
                "completed_requests": WorkflowInstance.objects.filter(
                    submitted_by=request.user,
                    status="COMPLETED",
                ).count(),
                "rejected_requests": WorkflowInstance.objects.filter(
                    submitted_by=request.user,
                    status="REJECTED",
                ).count(),
            }
        )


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserManagementSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        return User.objects.select_related("organization", "department").filter(
            organization=self.request.user.organization
        ).order_by("email")

    def perform_create(self, serializer):
        serializer.save(organization=self.request.user.organization)

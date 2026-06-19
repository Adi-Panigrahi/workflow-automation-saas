from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UserSerializer
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
                "message": "Welcome Admin"
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
                "message": "Welcome Manager"
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
                "message": "Welcome Employee"
            }
        )
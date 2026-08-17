from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from core.models import Organization
from departments.models import Department
from workflow_instances.models import WorkflowInstance
from workflows.models import WorkflowTemplate

from .models import User


class UserManagementApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.organization = Organization.objects.create(
            name="Google",
            slug="google",
        )
        self.other_organization = Organization.objects.create(
            name="Microsoft",
            slug="microsoft",
        )
        self.admin = User.objects.create_user(
            email="admin@google.com",
            username="admin",
            password="test-password",
            role="ADMIN",
            organization=self.organization,
        )
        self.department = Department.objects.create(
            name="Engineering",
            organization=self.organization,
        )

    def test_admin_can_create_a_user_in_their_organization(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            reverse("user-list"),
            {
                "email": "employee@google.com",
                "username": "employee",
                "password": "secure-password",
                "role": "EMPLOYEE",
                "department": self.department.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email="employee@google.com")
        self.assertEqual(user.organization, self.organization)
        self.assertEqual(user.department, self.department)
        self.assertTrue(user.check_password("secure-password"))

    def test_admin_cannot_assign_a_department_from_another_organization(self):
        other_department = Department.objects.create(
            name="Engineering",
            organization=self.other_organization,
        )
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            reverse("user-list"),
            {
                "email": "employee@google.com",
                "username": "employee",
                "password": "secure-password",
                "role": "EMPLOYEE",
                "department": other_department.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(email="employee@google.com").exists())

    def test_non_admin_cannot_manage_users(self):
        employee = User.objects.create_user(
            email="employee@google.com",
            username="employee",
            password="test-password",
            role="EMPLOYEE",
            organization=self.organization,
        )
        self.client.force_authenticate(employee)

        response = self.client.get(reverse("user-list"))

        self.assertEqual(response.status_code, 403)

    def test_employee_dashboard_returns_only_their_request_metrics(self):
        employee = User.objects.create_user(
            email="employee@google.com",
            username="employee",
            password="test-password",
            role="EMPLOYEE",
            organization=self.organization,
        )
        workflow = WorkflowTemplate.objects.create(
            name="Leave Request",
            organization=self.organization,
        )
        WorkflowInstance.objects.create(
            workflow=workflow,
            submitted_by=employee,
            status="IN_PROGRESS",
        )
        WorkflowInstance.objects.create(
            workflow=workflow,
            submitted_by=employee,
            status="COMPLETED",
        )
        self.client.force_authenticate(employee)

        response = self.client.get(reverse("employee-dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["in_progress_requests"], 1)
        self.assertEqual(response.data["completed_requests"], 1)
        self.assertEqual(response.data["rejected_requests"], 0)

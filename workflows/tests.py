from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User
from core.models import Organization

from .models import WorkflowStep, WorkflowTemplate


class WorkflowApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.organization = Organization.objects.create(
            name="Google",
            slug="google",
        )
        self.admin = User.objects.create_user(
            email="admin@google.com",
            username="admin",
            password="test-password",
            role="ADMIN",
            organization=self.organization,
        )
        self.manager = User.objects.create_user(
            email="manager@google.com",
            username="manager",
            password="test-password",
            role="MANAGER",
            organization=self.organization,
        )
        self.employee = User.objects.create_user(
            email="employee@google.com",
            username="employee",
            password="test-password",
            role="EMPLOYEE",
            organization=self.organization,
        )
        self.client.force_authenticate(self.admin)

    def test_admin_can_create_a_workflow_for_their_organization(self):
        response = self.client.post(
            reverse("workflow-list"),
            {"name": "Leave Request", "description": "Leave approval flow"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["organization"], self.organization.id)

    def test_admin_can_create_a_valid_workflow_step(self):
        workflow = WorkflowTemplate.objects.create(
            name="Leave Request",
            organization=self.organization,
        )

        response = self.client.post(
            reverse("workflow-step-list"),
            {
                "workflow": workflow.id,
                "name": "Manager Approval",
                "order": 1,
                "role_required": "MANAGER",
                "assigned_to": self.manager.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(WorkflowStep.objects.count(), 1)

    def test_step_approver_must_have_the_required_role(self):
        workflow = WorkflowTemplate.objects.create(
            name="Leave Request",
            organization=self.organization,
        )

        response = self.client.post(
            reverse("workflow-step-list"),
            {
                "workflow": workflow.id,
                "name": "Manager Approval",
                "order": 1,
                "role_required": "MANAGER",
                "assigned_to": self.employee.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_non_admin_cannot_manage_workflows(self):
        self.client.force_authenticate(self.employee)

        response = self.client.get(reverse("workflow-list"))

        self.assertEqual(response.status_code, 403)

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User
from approvals.models import Approval
from core.models import Organization
from workflows.models import WorkflowStep, WorkflowTemplate


class WorkflowInstanceApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.organization = Organization.objects.create(
            name="Google",
            slug="google",
        )
        self.employee = User.objects.create_user(
            email="employee@google.com",
            username="employee",
            password="test-password",
            role="EMPLOYEE",
            organization=self.organization,
        )
        self.manager = User.objects.create_user(
            email="manager@google.com",
            username="manager",
            password="test-password",
            role="MANAGER",
            organization=self.organization,
        )
        self.workflow = WorkflowTemplate.objects.create(
            name="Leave Request",
            organization=self.organization,
        )
        WorkflowStep.objects.create(
            workflow=self.workflow,
            name="Manager Approval",
            order=1,
            role_required="MANAGER",
            assigned_to=self.manager,
        )

    def test_authenticated_user_can_submit_an_instance(self):
        self.client.force_authenticate(self.employee)

        response = self.client.post(
            reverse("workflow-instance-list"),
            {
                "workflow": self.workflow.id,
                "request_data": {
                    "start_date": "2026-08-20",
                    "end_date": "2026-08-22",
                    "reason": "Family event",
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["submitted_by"], self.employee.id)
        self.assertEqual(response.data["status"], "IN_PROGRESS")
        self.assertEqual(response.data["request_data"]["reason"], "Family event")
        self.assertEqual(Approval.objects.count(), 1)
        self.assertEqual(Approval.objects.get().assigned_to, self.manager)

    def test_user_cannot_submit_another_organization_workflow(self):
        other_organization = Organization.objects.create(
            name="Microsoft",
            slug="microsoft",
        )
        other_workflow = WorkflowTemplate.objects.create(
            name="Expense Request",
            organization=other_organization,
        )
        self.client.force_authenticate(self.employee)

        response = self.client.post(
            reverse("workflow-instance-list"),
            {"workflow": other_workflow.id},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Approval.objects.count(), 0)

    def test_unauthenticated_user_cannot_submit_an_instance(self):
        response = self.client.post(
            reverse("workflow-instance-list"),
            {"workflow": self.workflow.id},
            format="json",
        )

        self.assertEqual(response.status_code, 401)

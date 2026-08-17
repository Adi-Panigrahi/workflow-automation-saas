from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User
from approvals.services import start_workflow
from core.models import Organization
from workflow_instances.models import WorkflowInstance
from workflows.models import WorkflowStep, WorkflowTemplate

from .models import AuditLog


class AuditLogTests(TestCase):
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

    def test_starting_a_workflow_creates_an_audit_log(self):
        instance = WorkflowInstance.objects.create(
            workflow=self.workflow,
            submitted_by=self.employee,
        )

        start_workflow(instance)

        audit_log = AuditLog.objects.get()
        self.assertEqual(audit_log.action, AuditLog.ACTION_WORKFLOW_STARTED)
        self.assertEqual(audit_log.actor, self.employee)
        self.assertEqual(audit_log.previous_status, "PENDING")
        self.assertEqual(audit_log.new_status, "IN_PROGRESS")

    def test_admin_can_list_organization_audit_logs(self):
        instance = WorkflowInstance.objects.create(
            workflow=self.workflow,
            submitted_by=self.employee,
        )
        start_workflow(instance)
        self.client.force_authenticate(self.admin)

        response = self.client.get(reverse("audit-log-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_non_admin_cannot_list_audit_logs(self):
        self.client.force_authenticate(self.employee)

        response = self.client.get(reverse("audit-log-list"))

        self.assertEqual(response.status_code, 403)

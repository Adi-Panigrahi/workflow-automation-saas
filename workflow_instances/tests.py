from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User
from approvals.models import Approval
from audit_logs.models import AuditLog
from core.models import Organization
from workflows.models import WorkflowStep, WorkflowTemplate

from .models import WorkflowInstance


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

    def test_submission_requires_fields_declared_by_workflow_schema(self):
        self.workflow.request_schema = {"required": ["reason", "start_date"]}
        self.workflow.save(update_fields=["request_schema"])
        self.client.force_authenticate(self.employee)

        response = self.client.post(
            reverse("workflow-instance-list"),
            {
                "workflow": self.workflow.id,
                "request_data": {"reason": "Family event"},
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("start_date", response.data["request_data"][0])

    def test_instance_list_can_be_filtered_by_status(self):
        instance = WorkflowInstance.objects.create(
            workflow=self.workflow,
            submitted_by=self.employee,
            status="COMPLETED",
        )
        self.client.force_authenticate(self.employee)

        response = self.client.get(
            reverse("workflow-instance-list"),
            {"status": "COMPLETED"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], instance.id)

    def test_instance_list_rejects_an_invalid_status_filter(self):
        self.client.force_authenticate(self.employee)

        response = self.client.get(
            reverse("workflow-instance-list"),
            {"status": "UNKNOWN"},
        )

        self.assertEqual(response.status_code, 400)

    def test_employee_cannot_list_another_employees_request(self):
        other_employee = User.objects.create_user(
            email="other@google.com",
            username="other",
            password="test-password",
            role="EMPLOYEE",
            organization=self.organization,
        )
        other_instance = WorkflowInstance.objects.create(
            workflow=self.workflow,
            submitted_by=other_employee,
        )
        self.client.force_authenticate(self.employee)

        response = self.client.get(reverse("workflow-instance-list"))

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(other_instance.id, [item["id"] for item in response.data])

    def test_submitter_can_cancel_an_in_progress_request(self):
        instance = WorkflowInstance.objects.create(
            workflow=self.workflow,
            submitted_by=self.employee,
        )
        from approvals.services import start_workflow
        start_workflow(instance)
        approval = Approval.objects.get(workflow_instance=instance)
        self.client.force_authenticate(self.employee)

        response = self.client.post(
            reverse("workflow-instance-cancel", kwargs={"pk": instance.pk}),
            format="json",
        )

        instance.refresh_from_db()
        approval.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(instance.status, "CANCELLED")
        self.assertIsNotNone(instance.cancelled_at)
        self.assertEqual(approval.status, "CANCELLED")
        self.assertTrue(
            AuditLog.objects.filter(
                workflow_instance=instance,
                action=AuditLog.ACTION_WORKFLOW_CANCELLED,
            ).exists()
        )

    def test_workflow_requests_cannot_be_updated_or_deleted(self):
        instance = WorkflowInstance.objects.create(
            workflow=self.workflow,
            submitted_by=self.employee,
        )
        self.client.force_authenticate(self.employee)

        update_response = self.client.patch(
            reverse("workflow-instance-detail", kwargs={"pk": instance.pk}),
            {"request_data": {"reason": "Changed"}},
            format="json",
        )
        delete_response = self.client.delete(
            reverse("workflow-instance-detail", kwargs={"pk": instance.pk})
        )

        self.assertEqual(update_response.status_code, 405)
        self.assertEqual(delete_response.status_code, 405)

    def test_submitter_can_view_their_workflow_timeline(self):
        from approvals.services import start_workflow

        instance = WorkflowInstance.objects.create(
            workflow=self.workflow,
            submitted_by=self.employee,
        )
        start_workflow(instance)
        self.client.force_authenticate(self.employee)

        response = self.client.get(
            reverse("workflow-instance-timeline", kwargs={"pk": instance.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["workflow_instance"], instance.id)
        self.assertEqual(len(response.data["approvals"]), 1)
        self.assertEqual(len(response.data["events"]), 1)
        self.assertEqual(response.data["events"][0]["action"], "WORKFLOW_STARTED")

    def test_unrelated_user_cannot_view_a_workflow_timeline(self):
        from approvals.services import start_workflow

        unrelated_employee = User.objects.create_user(
            email="unrelated@google.com",
            username="unrelated",
            password="test-password",
            role="EMPLOYEE",
            organization=self.organization,
        )
        instance = WorkflowInstance.objects.create(
            workflow=self.workflow,
            submitted_by=self.employee,
        )
        start_workflow(instance)
        self.client.force_authenticate(unrelated_employee)

        response = self.client.get(
            reverse("workflow-instance-timeline", kwargs={"pk": instance.pk})
        )

        self.assertEqual(response.status_code, 404)

    def test_admin_can_view_tenant_workflow_analytics(self):
        admin = User.objects.create_user(
            email="admin@google.com",
            username="admin",
            password="test-password",
            role="ADMIN",
            organization=self.organization,
        )
        WorkflowInstance.objects.create(
            workflow=self.workflow,
            submitted_by=self.employee,
            status="COMPLETED",
        )
        WorkflowInstance.objects.create(
            workflow=self.workflow,
            submitted_by=self.employee,
            status="REJECTED",
        )
        self.client.force_authenticate(admin)

        response = self.client.get(reverse("workflow-instance-analytics"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status_counts"]["COMPLETED"], 1)
        self.assertEqual(response.data["status_counts"]["REJECTED"], 1)
        self.assertEqual(response.data["workflows"][0]["total"], 2)

    def test_employee_cannot_view_workflow_analytics(self):
        self.client.force_authenticate(self.employee)

        response = self.client.get(reverse("workflow-instance-analytics"))

        self.assertEqual(response.status_code, 403)

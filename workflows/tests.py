from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from accounts.models import User
from core.models import Organization
from workflow_instances.models import WorkflowInstance

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
            {
                "name": "Leave Request",
                "description": "Leave approval flow",
                "request_schema": {"required": ["start_date", "end_date"]},
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["organization"], self.organization.id)
        self.assertEqual(response.data["request_schema"]["required"], ["start_date", "end_date"])

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

    def test_step_model_rejects_an_approver_from_another_organization(self):
        other_organization = Organization.objects.create(
            name="Microsoft",
            slug="microsoft",
        )
        other_manager = User.objects.create_user(
            email="manager@microsoft.com",
            username="microsoft-manager",
            password="test-password",
            role="MANAGER",
            organization=other_organization,
        )
        workflow = WorkflowTemplate.objects.create(
            name="Leave Request",
            organization=self.organization,
        )
        step = WorkflowStep(
            workflow=workflow,
            name="Manager Approval",
            order=1,
            role_required="MANAGER",
            assigned_to=other_manager,
        )

        with self.assertRaises(ValidationError):
            step.full_clean()

    def test_database_rejects_duplicate_step_orders(self):
        workflow = WorkflowTemplate.objects.create(
            name="Leave Request",
            organization=self.organization,
        )
        WorkflowStep.objects.create(
            workflow=workflow,
            name="Manager Approval",
            order=1,
            role_required="MANAGER",
            assigned_to=self.manager,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            WorkflowStep.objects.create(
                workflow=workflow,
                name="Second Manager Approval",
                order=1,
                role_required="MANAGER",
                assigned_to=self.manager,
            )

    def test_submitted_workflow_template_cannot_be_edited_or_deleted(self):
        workflow = WorkflowTemplate.objects.create(
            name="Leave Request",
            organization=self.organization,
        )
        WorkflowInstance.objects.create(workflow=workflow, submitted_by=self.employee)

        update_response = self.client.patch(
            reverse("workflow-detail", kwargs={"pk": workflow.pk}),
            {"name": "Changed Leave Request"},
            format="json",
        )
        delete_response = self.client.delete(
            reverse("workflow-detail", kwargs={"pk": workflow.pk})
        )

        self.assertEqual(update_response.status_code, 400)
        self.assertEqual(delete_response.status_code, 400)
        workflow.refresh_from_db()
        self.assertEqual(workflow.name, "Leave Request")

    def test_admin_can_clone_a_locked_workflow_template(self):
        workflow = WorkflowTemplate.objects.create(
            name="Leave Request",
            description="Original process",
            organization=self.organization,
            request_schema={"required": ["reason"]},
        )
        WorkflowStep.objects.create(
            workflow=workflow,
            name="Manager Approval",
            order=1,
            role_required="MANAGER",
            assigned_to=self.manager,
        )
        WorkflowInstance.objects.create(workflow=workflow, submitted_by=self.employee)

        response = self.client.post(
            reverse("workflow-clone", kwargs={"pk": workflow.pk}),
            {"name": "Leave Request v2"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        clone = WorkflowTemplate.objects.get(pk=response.data["id"])
        self.assertEqual(clone.description, workflow.description)
        self.assertEqual(clone.request_schema, workflow.request_schema)
        cloned_step = clone.steps.get()
        self.assertEqual(cloned_step.name, "Manager Approval")
        self.assertEqual(cloned_step.assigned_to, self.manager)

    def test_submitted_workflow_steps_cannot_be_changed(self):
        workflow = WorkflowTemplate.objects.create(
            name="Leave Request",
            organization=self.organization,
        )
        step = WorkflowStep.objects.create(
            workflow=workflow,
            name="Manager Approval",
            order=1,
            role_required="MANAGER",
            assigned_to=self.manager,
        )
        WorkflowInstance.objects.create(workflow=workflow, submitted_by=self.employee)

        response = self.client.patch(
            reverse("workflow-step-detail", kwargs={"pk": step.pk}),
            {"name": "Updated Approval"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

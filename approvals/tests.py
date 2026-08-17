from django.test import TestCase
from django.urls import reverse
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient

from accounts.models import User
from core.models import Organization
from workflow_instances.models import WorkflowInstance
from workflows.models import WorkflowStep, WorkflowTemplate

from .models import Approval
from .services import (
    WorkflowConfigurationError,
    approve_approval,
    reject_approval,
    start_workflow,
)


class StartWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.organization = Organization.objects.create(
            name="Google",
            slug="google",
        )
        self.submitter = User.objects.create_user(
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
        self.admin = User.objects.create_user(
            email="admin@google.com",
            username="admin",
            password="test-password",
            role="ADMIN",
            organization=self.organization,
        )
        self.workflow = WorkflowTemplate.objects.create(
            name="Leave Request",
            organization=self.organization,
        )

    def create_instance(self, submitted_by=None):
        return WorkflowInstance.objects.create(
            workflow=self.workflow,
            submitted_by=submitted_by or self.submitter,
        )

    def test_start_workflow_creates_first_pending_approval(self):
        first_step = WorkflowStep.objects.create(
            workflow=self.workflow,
            name="Manager Approval",
            order=1,
            role_required="MANAGER",
            assigned_to=self.manager,
        )
        instance = self.create_instance()

        approval = start_workflow(instance)

        instance.refresh_from_db()
        self.assertEqual(approval.status, "PENDING")
        self.assertEqual(approval.workflow_step, first_step)
        self.assertEqual(approval.assigned_to, self.manager)
        self.assertEqual(instance.status, "IN_PROGRESS")
        self.assertEqual(instance.current_step, first_step)
        self.assertEqual(Approval.objects.filter(workflow_instance=instance).count(), 1)

    def test_start_workflow_rejects_a_template_with_no_steps(self):
        with self.assertRaises(WorkflowConfigurationError):
            start_workflow(self.create_instance())

    def test_start_workflow_rejects_an_unassigned_first_step(self):
        WorkflowStep.objects.create(
            workflow=self.workflow,
            name="Manager Approval",
            order=1,
            role_required="MANAGER",
        )

        with self.assertRaises(WorkflowConfigurationError):
            start_workflow(self.create_instance())

    def test_start_workflow_rejects_a_cross_organization_submitter(self):
        other_organization = Organization.objects.create(
            name="Microsoft",
            slug="microsoft",
        )
        other_employee = User.objects.create_user(
            email="employee@microsoft.com",
            username="microsoft-employee",
            password="test-password",
            role="EMPLOYEE",
            organization=other_organization,
        )

        with self.assertRaises(WorkflowConfigurationError):
            start_workflow(self.create_instance(submitted_by=other_employee))

    def test_approve_advances_to_the_next_step(self):
        first_step = WorkflowStep.objects.create(
            workflow=self.workflow,
            name="Manager Approval",
            order=1,
            role_required="MANAGER",
            assigned_to=self.manager,
        )
        second_step = WorkflowStep.objects.create(
            workflow=self.workflow,
            name="HR Approval",
            order=2,
            role_required="ADMIN",
            assigned_to=self.admin,
        )
        instance = self.create_instance()
        first_approval = start_workflow(instance)

        approve_approval(first_approval, self.manager, "Approved by manager.")

        instance.refresh_from_db()
        first_approval.refresh_from_db()
        next_approval = Approval.objects.get(
            workflow_instance=instance,
            workflow_step=second_step,
        )
        self.assertEqual(first_approval.status, "APPROVED")
        self.assertEqual(first_approval.comments, "Approved by manager.")
        self.assertEqual(instance.status, "IN_PROGRESS")
        self.assertEqual(instance.current_step, second_step)
        self.assertEqual(next_approval.status, "PENDING")
        self.assertEqual(next_approval.assigned_to, self.admin)
        self.assertEqual(first_step.order, 1)

    def test_approve_final_step_completes_workflow(self):
        step = WorkflowStep.objects.create(
            workflow=self.workflow,
            name="Manager Approval",
            order=1,
            role_required="MANAGER",
            assigned_to=self.manager,
        )
        instance = self.create_instance()
        approval = start_workflow(instance)

        approve_approval(approval, self.manager)

        instance.refresh_from_db()
        approval.refresh_from_db()
        self.assertEqual(approval.status, "APPROVED")
        self.assertEqual(instance.status, "COMPLETED")
        self.assertEqual(instance.current_step, step)

    def test_reject_stops_the_workflow(self):
        WorkflowStep.objects.create(
            workflow=self.workflow,
            name="Manager Approval",
            order=1,
            role_required="MANAGER",
            assigned_to=self.manager,
        )
        instance = self.create_instance()
        approval = start_workflow(instance)

        reject_approval(approval, self.manager, "Insufficient information.")

        instance.refresh_from_db()
        approval.refresh_from_db()
        self.assertEqual(approval.status, "REJECTED")
        self.assertEqual(approval.comments, "Insufficient information.")
        self.assertEqual(instance.status, "REJECTED")

    def test_only_the_assigned_user_can_approve(self):
        another_manager = User.objects.create_user(
            email="other-manager@google.com",
            username="other-manager",
            password="test-password",
            role="MANAGER",
            organization=self.organization,
        )
        WorkflowStep.objects.create(
            workflow=self.workflow,
            name="Manager Approval",
            order=1,
            role_required="MANAGER",
            assigned_to=self.manager,
        )
        approval = start_workflow(self.create_instance())

        with self.assertRaises(PermissionDenied):
            approve_approval(approval, another_manager)

    def test_assigned_user_can_approve_through_api(self):
        WorkflowStep.objects.create(
            workflow=self.workflow,
            name="Manager Approval",
            order=1,
            role_required="MANAGER",
            assigned_to=self.manager,
        )
        approval = start_workflow(self.create_instance())
        self.client.force_authenticate(self.manager)

        response = self.client.post(
            reverse("approval-approve", kwargs={"pk": approval.pk}),
            {"comments": "Looks good."},
            format="json",
        )

        approval.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(approval.status, "APPROVED")
        self.assertEqual(response.data["workflow_status"], "COMPLETED")

    def test_unassigned_user_cannot_access_an_approval_api(self):
        WorkflowStep.objects.create(
            workflow=self.workflow,
            name="Manager Approval",
            order=1,
            role_required="MANAGER",
            assigned_to=self.manager,
        )
        approval = start_workflow(self.create_instance())
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            reverse("approval-approve", kwargs={"pk": approval.pk}),
            format="json",
        )

        self.assertEqual(response.status_code, 404)

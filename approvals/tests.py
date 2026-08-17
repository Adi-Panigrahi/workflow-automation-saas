from django.test import TestCase

from accounts.models import User
from core.models import Organization
from workflow_instances.models import WorkflowInstance
from workflows.models import WorkflowStep, WorkflowTemplate

from .models import Approval
from .services import WorkflowConfigurationError, start_workflow


class StartWorkflowTests(TestCase):
    def setUp(self):
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

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User
from approvals.services import approve_approval, start_workflow
from core.models import Organization
from workflow_instances.models import WorkflowInstance
from workflows.models import WorkflowStep, WorkflowTemplate

from .models import Notification


class NotificationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.organization = Organization.objects.create(name="Google", slug="google")
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
        self.step = WorkflowStep.objects.create(
            workflow=self.workflow,
            name="Manager Approval",
            order=1,
            role_required="MANAGER",
            assigned_to=self.manager,
        )

    def start_instance(self):
        instance = WorkflowInstance.objects.create(
            workflow=self.workflow,
            submitted_by=self.employee,
        )
        return instance, start_workflow(instance)

    def test_starting_workflow_notifies_first_approver(self):
        instance, approval = self.start_instance()

        notification = Notification.objects.get()
        self.assertEqual(notification.recipient, self.manager)
        self.assertEqual(notification.workflow_instance, instance)
        self.assertEqual(notification.approval, approval)
        self.assertEqual(
            notification.notification_type,
            Notification.TYPE_APPROVAL_REQUESTED,
        )

    def test_completing_workflow_notifies_submitter(self):
        instance, approval = self.start_instance()

        approve_approval(approval, self.manager)

        notification = Notification.objects.get(
            notification_type=Notification.TYPE_WORKFLOW_COMPLETED
        )
        self.assertEqual(notification.recipient, self.employee)
        self.assertEqual(notification.workflow_instance, instance)

    def test_recipient_can_filter_and_mark_their_notifications_read(self):
        self.start_instance()
        self.client.force_authenticate(self.manager)

        list_response = self.client.get(reverse("notification-list"), {"unread": "true"})
        notification_id = list_response.data[0]["id"]
        mark_response = self.client.post(
            reverse("notification-mark-read", kwargs={"pk": notification_id})
        )
        unread_response = self.client.get(reverse("notification-list"), {"unread": "true"})
        self.start_instance()
        mark_all_response = self.client.post(reverse("notification-mark-all-read"))

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(mark_response.status_code, 200)
        self.assertIsNotNone(mark_response.data["read_at"])
        self.assertEqual(unread_response.data, [])
        self.assertEqual(mark_all_response.data["marked_read"], 1)

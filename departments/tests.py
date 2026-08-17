from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User
from core.models import Organization

from .models import Department


class DepartmentApiTests(TestCase):
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

    def test_admin_can_create_a_department_for_their_organization(self):
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            reverse("department-list"),
            {"name": "Engineering"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["organization"], self.organization.id)
        self.assertTrue(
            Department.objects.filter(
                organization=self.organization,
                name="Engineering",
            ).exists()
        )

    def test_admin_cannot_create_duplicate_department_names(self):
        Department.objects.create(name="Engineering", organization=self.organization)
        self.client.force_authenticate(self.admin)

        response = self.client.post(
            reverse("department-list"),
            {"name": "engineering"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

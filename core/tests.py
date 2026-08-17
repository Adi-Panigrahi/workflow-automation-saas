from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import User

from .models import Organization


class OrganizationApiTests(TestCase):
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
        self.employee = User.objects.create_user(
            email="employee@google.com",
            username="employee",
            password="test-password",
            role="EMPLOYEE",
            organization=self.organization,
        )

    def test_unauthenticated_user_cannot_list_organizations(self):
        response = self.client.get(reverse("organizations"))

        self.assertEqual(response.status_code, 401)

    def test_user_can_only_list_their_organization(self):
        self.client.force_authenticate(self.employee)

        response = self.client.get(reverse("organizations"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.organization.id)

    def test_user_cannot_retrieve_another_organization(self):
        self.client.force_authenticate(self.employee)

        response = self.client.get(
            reverse("organization-detail", kwargs={"pk": self.other_organization.pk})
        )

        self.assertEqual(response.status_code, 404)

    def test_non_superuser_cannot_create_an_organization(self):
        self.client.force_authenticate(self.employee)

        response = self.client.post(
            reverse("organizations"),
            {"name": "KPMG", "slug": "kpmg"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

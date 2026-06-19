   
from django.db import models
from core.models import Organization

class Department(models.Model):

    name = models.CharField(
        max_length=100
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="departments"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name
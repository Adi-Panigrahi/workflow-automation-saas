from rest_framework import serializers

from .models import Department


class DepartmentSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Department
        fields = ["id", "name", "organization", "created_at", "updated_at"]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]

    def validate_name(self, value):
        organization = self.context["request"].user.organization
        departments = Department.objects.filter(organization=organization, name__iexact=value)
        if self.instance:
            departments = departments.exclude(pk=self.instance.pk)

        if departments.exists():
            raise serializers.ValidationError(
                "A department with this name already exists in your organization."
            )

        return value

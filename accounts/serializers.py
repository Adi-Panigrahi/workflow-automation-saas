from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "role",
            "organization",
            "department",
        ]


class UserManagementSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(read_only=True)
    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=8,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "role",
            "organization",
            "department",
            "is_active",
            "password",
        ]
        read_only_fields = ["id", "organization"]

    def validate(self, attrs):
        if not self.instance and not attrs.get("password"):
            raise serializers.ValidationError(
                {"password": "A password is required when creating a user."}
            )

        department = attrs.get(
            "department",
            self.instance.department if self.instance else None,
        )
        organization = self.context["request"].user.organization

        if department and department.organization_id != organization.id:
            raise serializers.ValidationError(
                {"department": "The department must belong to your organization."}
            )

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for attribute, value in validated_data.items():
            setattr(instance, attribute, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance

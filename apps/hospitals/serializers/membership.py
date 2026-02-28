from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.hospitals.models import HospitalMembership

User = get_user_model()


class MembershipSerializer(serializers.ModelSerializer):
    """Read representation of a membership — used in staff list views."""

    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_full_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = HospitalMembership
        fields = [
            "id",
            "user",
            "user_email",
            "user_full_name",
            "role",
            "is_active",
            "invited_by",
            "created_at",
        ]
        read_only_fields = ["id", "invited_by", "created_at"]


class AddStaffSerializer(serializers.Serializer):
    """
    Used when a Hospital Admin adds a staff member.
    Takes an email + role, looks up the user, creates the membership.

    Why Serializer and not ModelSerializer?
    - We're not directly creating a membership from form data.
    - We need to look up the user by email first, then create.
    - The service layer handles the actual creation.
    """

    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=HospitalMembership.Role.choices)

    def validate_email(self, value):
        if not User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("No user found with this email. They must register first.")
        return value.lower()


class UpdateMembershipSerializer(serializers.ModelSerializer):
    """Used to change a staff member's role or deactivate them."""

    class Meta:
        model = HospitalMembership
        fields = ["role", "is_active"]
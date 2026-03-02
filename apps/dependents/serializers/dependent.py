from rest_framework import serializers
from apps.dependents.models import Dependent, Guardianship


class DependentSerializer(serializers.ModelSerializer):
    """Full dependent detail — for guardians."""
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Dependent
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "gender",
            "medical_history",
            "allergies",
            "chronic_conditions",
            "emergency_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "full_name", "created_at", "updated_at"]


class DependentReadOnlySerializer(serializers.ModelSerializer):
    """
    Safe read-only view for nurses and admins.
    """
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Dependent
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "gender",
            "medical_history",
            "allergies",
            "chronic_conditions",
            "emergency_notes",
        ]
        read_only_fields = fields


class GuardianshipSerializer(serializers.ModelSerializer):
    """Shows who the guardians of a dependent are."""
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_full_name = serializers.CharField(source="user.full_name", read_only=True)
    dependent_name = serializers.CharField(source="dependent.full_name", read_only=True)

    class Meta:
        model = Guardianship
        fields = [
            "id",
            "user",
            "user_email",
            "user_full_name",
            "dependent",
            "dependent_name",
            "is_active",
            "added_by",
            "created_at",
        ]
        read_only_fields = fields


class AddGuardianSerializer(serializers.Serializer):
    """
    Used when a guardian wants to grant another user access to their dependent.
    Takes the email of the user to add.
    """
    email = serializers.EmailField()

    def validate_email(self, value):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("No user found with this email.")
        return value.lower()
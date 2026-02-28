from rest_framework import serializers
from apps.hospitals.models import Hospital


class HospitalSerializer(serializers.ModelSerializer):
    """Full hospital detail — used by admins."""

    class Meta:
        model = Hospital
        fields = [
            "id",
            "name",
            "registration_number",
            "email",
            "phone",
            "address",
            "city",
            "country",
            "status",
            "logo_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]


class HospitalCreateSerializer(serializers.ModelSerializer):
    """Used when a hospital registers on the platform."""

    class Meta:
        model = Hospital
        fields = [
            "name",
            "registration_number",
            "email",
            "phone",
            "address",
            "city",
            "country",
        ]

    def validate_registration_number(self, value):
        if Hospital.objects.filter(registration_number__iexact=value).exists():
            raise serializers.ValidationError("A hospital with this registration number already exists.")
        return value.upper()  # normalize to uppercase


class HospitalStatusSerializer(serializers.ModelSerializer):
    """
    Used by platform superadmin to approve/suspend hospitals.
    Only exposes the status field for update.
    """

    class Meta:
        model = Hospital
        fields = ["status"]
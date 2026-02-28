"""
Safe read representation of a User.
"""

from rest_framework import serializers
from apps.accounts.models import User


class UserMembershipSerializer(serializers.Serializer):
    """
    Nested serializer showing a user's role in each hospital.
    """
    hospital_id = serializers.UUIDField(source="hospital.id")
    hospital_name = serializers.CharField(source="hospital.name")
    hospital_status = serializers.CharField(source="hospital.status")
    role = serializers.CharField()
    is_active = serializers.BooleanField()


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    # This maps to the @property on the User model

    memberships = serializers.SerializerMethodField()
    # SerializerMethodField calls get_memberships() below

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "is_2fa_enabled",
            "date_joined",
            "memberships",
        ]
        read_only_fields = fields

    def get_memberships(self, user):
        """
        Returns all hospital memberships for this user.
        select_related fetches hospital data in the same query.
        """
        memberships = user.hospital_memberships.select_related("hospital").filter(is_active=True)
        return UserMembershipSerializer(memberships, many=True).data
    
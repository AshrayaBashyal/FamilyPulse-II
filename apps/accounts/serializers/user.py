"""
Safe read representation of a User.
"""

from rest_framework import serializers
from apps.accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    # This maps to the @property on the User model

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
        ]
        read_only_fields = fields
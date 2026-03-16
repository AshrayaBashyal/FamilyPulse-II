"""
Shared helpers used across all analytics views.
"""

from datetime import date
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from apps.hospitals.models import Hospital, HospitalMembership

VALID_GROUP_BY = {"day", "week", "month"}


def parse_date_params(request):
    """
    Parses and validates date_from and date_to query params.
    Returns (date | None, date | None).

    Raises ValidationError (400) if:
    - A date value is provided but not a valid ISO date (YYYY-MM-DD)
    - date_from is after date_to
    """
    def _parse(key):
        val = request.query_params.get(key)
        if not val:
            return None
        try:
            return date.fromisoformat(val)
        except ValueError:
            raise ValidationError({key: f"Invalid date format. Use YYYY-MM-DD."})

    date_from = _parse("date_from")
    date_to = _parse("date_to")

    if date_from and date_to and date_from > date_to:
        raise ValidationError({"date_from": "date_from cannot be after date_to."})

    return date_from, date_to


def parse_group_by(request, default="day") -> str:
    """
    Parses and validates the group_by query param.
    Raises ValidationError (400) if the value is not day/week/month.
    """
    value = request.query_params.get("group_by", default)
    if value not in VALID_GROUP_BY:
        raise ValidationError(
            {"group_by": f"Invalid value '{value}'. Must be one of: {', '.join(sorted(VALID_GROUP_BY))}."}
        )
    return value


def require_hospital_role(user, hospital_id, roles: list):
    """
    Checks the user is an active member of the hospital with one of the given roles.
    Returns (hospital, None) on success.
    Returns (None, Response) on failure — caller returns the response immediately.
    """
    try:
        hospital = Hospital.objects.get(id=hospital_id)
    except Hospital.DoesNotExist:
        return None, Response({"detail": "Hospital not found."}, status=status.HTTP_404_NOT_FOUND)

    has_role = HospitalMembership.objects.filter(
        user=user,
        hospital=hospital,
        role__in=roles,
        is_active=True,
    ).exists()

    if not has_role:
        return None, Response(
            {"detail": "You do not have permission to view this hospital's analytics."},
            status=status.HTTP_403_FORBIDDEN,
        )

    return hospital, None
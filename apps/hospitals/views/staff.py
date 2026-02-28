from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.hospitals.models import Hospital, HospitalMembership
from apps.hospitals.serializers.membership import (
    MembershipSerializer,
    AddStaffSerializer,
    UpdateMembershipSerializer,
)
from apps.hospitals.permissions import IsHospitalAdmin
from apps.hospitals.services import hospital_service


class StaffListAddView(APIView):

    permission_classes = [IsHospitalAdmin]

    @extend_schema(
        responses={200: MembershipSerializer(many=True)},
        summary="List hospital staff",
        tags=["Staff"],
    )
    def get(self, request, hospital_id):
        memberships = HospitalMembership.objects.filter(
            hospital_id=hospital_id,
        ).select_related("user", "invited_by")

        return Response(MembershipSerializer(memberships, many=True).data)


    @extend_schema(
        request=AddStaffSerializer,
        responses={
            201: MembershipSerializer,
            400: OpenApiResponse(description="Validation error"),
        },
        summary="Add a staff member to hospital",
        tags=["Staff"],
    )
    def post(self, request, hospital_id):
        try:
            hospital = Hospital.objects.get(id=hospital_id)
        except Hospital.DoesNotExist:
            return Response({"detail": "Hospital not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AddStaffSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        membership = hospital_service.add_staff_member(
            hospital=hospital,
            email=serializer.validated_data["email"],
            role=serializer.validated_data["role"],
            invited_by=request.user,
        )
        return Response(MembershipSerializer(membership).data, status=status.HTTP_201_CREATED)


class StaffDetailView(APIView):

    permission_classes = [IsHospitalAdmin]

    def get_object(self, hospital_id, membership_id):
        return HospitalMembership.objects.filter(
            id=membership_id,
            hospital_id=hospital_id,
        ).select_related("user").first()

    @extend_schema(
        request=UpdateMembershipSerializer,
        responses={200: MembershipSerializer},
        summary="Update staff member role or status",
        tags=["Staff"],
    )
    def patch(self, request, hospital_id, membership_id):
        membership = self.get_object(hospital_id, membership_id)
        if not membership:
            return Response({"detail": "Membership not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = UpdateMembershipSerializer(membership, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(MembershipSerializer(membership).data)


    @extend_schema(
        responses={204: OpenApiResponse(description="Staff member removed")},
        summary="Remove a staff member",
        tags=["Staff"],
    )
    def delete(self, request, hospital_id, membership_id):
        membership = self.get_object(hospital_id, membership_id)
        if not membership:
            return Response({"detail": "Membership not found."}, status=status.HTTP_404_NOT_FOUND)

        hospital_service.remove_staff_member(membership)
        return Response(status=status.HTTP_204_NO_CONTENT)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.hospitals.models import Hospital
from apps.hospitals.serializers.hospital import (
    HospitalSerializer,
    HospitalCreateSerializer,
    HospitalStatusSerializer,
)
from apps.hospitals.services import hospital_service


class HospitalListCreateView(APIView):

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return []  # AllowAny for GET

    @extend_schema(
        responses={200: HospitalSerializer(many=True)},
        summary="List hospitals (active only for public, all statuses for superadmin)",
        tags=["Hospitals"],
    )
    def get(self, request):
        if request.user.is_authenticated and request.user.is_staff:
            # Superadmin sees everything — pending, active, suspended
            hospitals = Hospital.objects.all()
        else:
            # Everyone else only sees active hospitals
            hospitals = Hospital.objects.filter(status=Hospital.Status.ACTIVE)
        return Response(HospitalSerializer(hospitals, many=True).data)

    @extend_schema(
        request=HospitalCreateSerializer,
        responses={
            201: HospitalSerializer,
            400: OpenApiResponse(description="Validation error"),
        },
        summary="Register a hospital",
        tags=["Hospitals"],
    )
    def post(self, request):
        serializer = HospitalCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        hospital = hospital_service.create_hospital(validated_data=serializer.validated_data, created_by=request.user)
        
        return Response(HospitalSerializer(hospital).data, status=status.HTTP_201_CREATED)


class HospitalDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get_object(self, hospital_id):
        try:
            return Hospital.objects.get(id=hospital_id)
        except Hospital.DoesNotExist:
            return None

    @extend_schema(
        responses={200: HospitalSerializer},
        summary="Get hospital detail",
        tags=["Hospitals"],
    )
    def get(self, request, hospital_id):
        hospital = self.get_object(hospital_id)
        if not hospital:
            return Response({"detail": "Hospital not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(HospitalSerializer(hospital).data)

    @extend_schema(
        request=HospitalSerializer,
        responses={200: HospitalSerializer},
        summary="Update hospital info",
        tags=["Hospitals"],
    )
    def patch(self, request, hospital_id):
        hospital = self.get_object(hospital_id)
        if not hospital:
            return Response({"detail": "Hospital not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = HospitalSerializer(hospital, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(serializer.data)


class HospitalStatusView(APIView):

    permission_classes = [IsAdminUser]

    @extend_schema(
        request=HospitalStatusSerializer,
        responses={200: HospitalSerializer},
        summary="Update hospital status (superadmin)",
        tags=["Hospitals"],
    )
    def patch(self, request, hospital_id):
        try:
            hospital = Hospital.objects.get(id=hospital_id)
        except Hospital.DoesNotExist:
            return Response({"detail": "Hospital not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = HospitalStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        hospital = hospital_service.update_hospital_status(
            hospital, serializer.validated_data["status"]
        )
        return Response(HospitalSerializer(hospital).data)
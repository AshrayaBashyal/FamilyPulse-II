from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.dependents.models import Dependent, Guardianship
from apps.dependents.serializers.dependent import (
    DependentSerializer,
    GuardianshipSerializer,
    AddGuardianSerializer,
)
from apps.dependents.permissions import IsGuardian
from apps.dependents.services import dependent_service


class DependentListCreateView(APIView):

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: DependentSerializer(many=True)},
        summary="List my dependents",
        tags=["Dependents"],
    )
    def get(self, request):
        # Only return dependents this user is actively guarding
        dependent_ids = Guardianship.objects.filter(
            user=request.user,
            is_active=True,
        ).values_list("dependent_id", flat=True)

        dependents = Dependent.objects.filter(id__in=dependent_ids)
        return Response(DependentSerializer(dependents, many=True).data)

    @extend_schema(
        request=DependentSerializer,
        responses={201: DependentSerializer},
        summary="Create a dependent",
        tags=["Dependents"],
    )
    def post(self, request):
        serializer = DependentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        dependent = dependent_service.create_dependent(
            validated_data=serializer.validated_data,
            guardian=request.user,
        )
        return Response(DependentSerializer(dependent).data, status=status.HTTP_201_CREATED)


class DependentDetailView(APIView):
    """
    GET    /api/v1/dependents/<dependent_id>/  — get detail
    PATCH  /api/v1/dependents/<dependent_id>/  — update
    DELETE /api/v1/dependents/<dependent_id>/  — delete
    """

    permission_classes = [IsAuthenticated, IsGuardian]

    def get_object(self, dependent_id):
        try:
            dependent = Dependent.objects.get(id=dependent_id)
            # This triggers has_object_permission on IsGuardian
            self.check_object_permissions(self.request, dependent)
            return dependent
        except Dependent.DoesNotExist:
            return None

    @extend_schema(
        responses={200: DependentSerializer},
        summary="Get dependent detail",
        tags=["Dependents"],
    )
    def get(self, request, dependent_id):
        dependent = self.get_object(dependent_id)
        if not dependent:
            return Response({"detail": "Dependent not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(DependentSerializer(dependent).data)

    @extend_schema(
        request=DependentSerializer,
        responses={200: DependentSerializer},
        summary="Update dependent",
        tags=["Dependents"],
    )
    def patch(self, request, dependent_id):
        dependent = self.get_object(dependent_id)
        if not dependent:
            return Response({"detail": "Dependent not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = DependentSerializer(dependent, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        dependent = dependent_service.update_dependent(dependent, serializer.validated_data)
        return Response(DependentSerializer(dependent).data)

    @extend_schema(
        responses={204: OpenApiResponse(description="Dependent deleted")},
        summary="Delete dependent",
        tags=["Dependents"],
    )
    def delete(self, request, dependent_id):
        dependent = self.get_object(dependent_id)
        if not dependent:
            return Response({"detail": "Dependent not found."}, status=status.HTTP_404_NOT_FOUND)

        dependent.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GuardianListAddView(APIView):

    permission_classes = [IsAuthenticated, IsGuardian]

    def get_dependent(self, dependent_id):
        try:
            dependent = Dependent.objects.get(id=dependent_id)
            self.check_object_permissions(self.request, dependent)
            return dependent
        except Dependent.DoesNotExist:
            return None

    @extend_schema(
        responses={200: GuardianshipSerializer(many=True)},
        summary="List guardians of a dependent",
        tags=["Dependents"],
    )
    def get(self, request, dependent_id):
        dependent = self.get_dependent(dependent_id)
        if not dependent:
            return Response({"detail": "Dependent not found."}, status=status.HTTP_404_NOT_FOUND)

        guardianships = Guardianship.objects.filter(
            dependent=dependent,
            is_active=True,
        ).select_related("user", "added_by")
        return Response(GuardianshipSerializer(guardianships, many=True).data)

    @extend_schema(
        request=AddGuardianSerializer,
        responses={201: GuardianshipSerializer},
        summary="Add a guardian to a dependent",
        tags=["Dependents"],
    )
    def post(self, request, dependent_id):
        dependent = self.get_dependent(dependent_id)
        if not dependent:
            return Response({"detail": "Dependent not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AddGuardianSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        guardianship = dependent_service.add_guardian(
            dependent=dependent,
            email=serializer.validated_data["email"],
            added_by=request.user,
        )
        return Response(GuardianshipSerializer(guardianship).data, status=status.HTTP_201_CREATED)


class GuardianRevokeView(APIView):

    permission_classes = [IsAuthenticated, IsGuardian]

    @extend_schema(
        responses={204: OpenApiResponse(description="Guardianship revoked")},
        summary="Revoke a guardianship",
        tags=["Dependents"],
    )
    def delete(self, request, dependent_id, guardianship_id):
        try:
            dependent = Dependent.objects.get(id=dependent_id)
            self.check_object_permissions(request, dependent)
        except Dependent.DoesNotExist:
            return Response({"detail": "Dependent not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            guardianship = Guardianship.objects.get(
                id=guardianship_id,
                dependent=dependent,
                is_active=True,
            )
        except Guardianship.DoesNotExist:
            return Response({"detail": "Guardianship not found."}, status=status.HTTP_404_NOT_FOUND)

        dependent_service.revoke_guardian(guardianship, requesting_user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
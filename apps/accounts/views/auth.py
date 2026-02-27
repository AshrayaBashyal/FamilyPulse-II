from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.accounts.serializers.register import RegisterSerializer
from apps.accounts.serializers.login import LoginSerializer
from apps.accounts.serializers.user import UserSerializer
from apps.accounts.services import auth_service


class RegisterView(APIView):
    """
    Creates a new user account and returns JWT tokens.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(description="User created, tokens returned"),
            400: OpenApiResponse(description="Validation error"),
        },
        summary="Register a new user",
        tags=["Auth"],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user, tokens = auth_service.register_user(serializer.validated_data)

        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": tokens,
            },
            status=status.HTTP_201_CREATED,
        )


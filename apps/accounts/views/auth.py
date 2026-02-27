from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
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


class LoginView(APIView):
    """
    Authenticates user and returns JWT tokens.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description="Login successful, tokens returned"),
            401: OpenApiResponse(description="Invalid credentials"),
        },
        summary="Login",
        tags=["Auth"],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user, tokens = auth_service.login_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )

        return Response(
            {
                "user": UserSerializer(user).data,
                "tokens": tokens,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    Blacklists the refresh token. Requires authentication.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request={"application/json": {"type": "object", "properties": {"refresh": {"type": "string"}}}},
        responses={204: OpenApiResponse(description="Logged out successfully")},
        summary="Logout",
        tags=["Auth"],
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"refresh": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        auth_service.logout_user(refresh_token)

        return Response(status=status.HTTP_204_NO_CONTENT)


class TokenRefreshView(APIView):
    """
    Returns a new access token given a valid refresh token.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        request={"application/json": {"type": "object", "properties": {"refresh": {"type": "string"}}}},
        responses={200: OpenApiResponse(description="New access token returned")},
        summary="Refresh access token",
        tags=["Auth"],
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"refresh": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tokens = auth_service.refresh_access_token(refresh_token)
        return Response(tokens, status=status.HTTP_200_OK)


class MeView(APIView):
    """
    Returns the currently authenticated user's profile.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserSerializer},
        summary="Get current user",
        tags=["Auth"],
    )
    def get(self, request):
        return Response(UserSerializer(request.user).data)
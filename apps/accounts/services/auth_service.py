from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User    # not used User = get_user_model() due to type hinting error


def register_user(validated_data: dict) -> tuple[User, dict]:
    """
    Creates a new user and returns the user + JWT tokens.
    """
    validated_data.pop("password_confirm", None)
    password = validated_data.pop("password")

    user = User(**validated_data)
    user.set_password(password)
    user.save()

    tokens = _generate_tokens(user)
    return user, tokens


def login_user(email: str, password: str) -> tuple[User, dict]:
    """
    Authenticates a user by email/password and returns tokens.
    """
    user = authenticate(username=email.lower(), password=password)

    if user is None:
        raise AuthenticationFailed("Invalid email or password.")

    if not user.is_active:
        raise AuthenticationFailed("This account has been deactivated.")

    tokens = _generate_tokens(user)
    return user, tokens


def refresh_access_token(refresh_token: str) -> dict:
    """
    Takes a refresh token string, returns a new access and refresh token.
    """
    try:
        token = RefreshToken(refresh_token)
        return {
            "access": str(token.access_token),
            "refresh": str(token)
        }
    except Exception:
        raise ValidationError({"refresh": "Invalid or expired refresh token."})


def logout_user(refresh_token: str) -> None:
    """
    Blacklists the refresh token so it can't be used again.
    """
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except Exception:
        # pass
        raise ValidationError({"detail": "Token is already invalid or expired."})


def _generate_tokens(user: User) -> dict:
    """
    Generates access + refresh JWT tokens for a user.
    """
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
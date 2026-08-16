from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    ListCreateAPIView,
    RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView  # noqa: F401 — re-exported

from .models import Role, User
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    StaffCreateSerializer,
    UserSerializer,
)


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------

class IsCommitteeChairman(BasePermission):
    """Allow access only to users whose role is committee_chairman."""

    message = 'Only the committee chairman can perform this action.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == Role.COMMITTEE_CHAIRMAN
        )


# ---------------------------------------------------------------------------
# Auth views
# ---------------------------------------------------------------------------

class RegisterView(CreateAPIView):
    """Public endpoint for applicant self-registration."""

    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        tokens = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

        return Response(
            {
                'user': UserSerializer(user, context=self.get_serializer_context()).data,
                'tokens': tokens,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Return JWT tokens and user profile on valid credentials."""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        tokens = serializer.validated_data['tokens']

        return Response(
            {
                'tokens': tokens,
                'user': UserSerializer(user, context={'request': request}).data,
            },
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Profile views
# ---------------------------------------------------------------------------

class ProfileView(RetrieveUpdateAPIView):
    """Retrieve or partially update the authenticated user's own profile."""

    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        # Only allow a specific subset of fields to be changed via this endpoint.
        allowed_fields = {'first_name', 'last_name', 'phone'}
        data = {k: v for k, v in request.data.items() if k in allowed_fields}

        serializer = UserSerializer(
            self.get_object(),
            data=data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangePasswordView(UpdateAPIView):
    """Allow an authenticated user to change their own password."""

    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    http_method_names = ['post', 'head', 'options']

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Password updated successfully.'}, status=status.HTTP_200_OK)

    # Map the inherited UpdateAPIView machinery to the POST handler so the
    # router URL pattern (POST /change-password/) works as expected.
    def update(self, request, *args, **kwargs):  # pragma: no cover
        return self.post(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# Staff management views (committee chairman only)
# ---------------------------------------------------------------------------

class StaffListView(ListCreateAPIView):
    """
    GET  — list all non-applicant users.
    POST — create a new staff member.
    Both require committee_chairman role.
    """

    permission_classes = [IsAuthenticated, IsCommitteeChairman]
    pagination_class = None  # staff count is small; client handles search/pagination

    def get_queryset(self):
        return User.objects.exclude(role=Role.APPLICANT).order_by('last_name', 'first_name')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StaffCreateSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = StaffCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserSerializer(user, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )


class StaffDetailView(RetrieveUpdateDestroyAPIView):
    """
    GET    — retrieve a single staff member.
    PATCH  — update a single staff member.
    DELETE — soft-delete (sets is_active=False).
    All require committee_chairman role.
    """

    permission_classes = [IsAuthenticated, IsCommitteeChairman]
    serializer_class = UserSerializer
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        return User.objects.exclude(role=Role.APPLICANT)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class RequestEmailCodeView(APIView):
    """POST /auth/request-verification/ {email} — email a 6-digit code (#2)."""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        import random
        from datetime import timedelta
        from django.utils import timezone
        from accounts.models import EmailVerification, User
        from notifications import mailer

        email = (request.data.get('email') or '').strip().lower()
        if not email:
            return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email__iexact=email).exists():
            return Response({'detail': 'An account with this email already exists.'},
                            status=status.HTTP_400_BAD_REQUEST)
        # light rate-limit: max 1 code per 60s per email
        recent = EmailVerification.objects.filter(
            email__iexact=email, created_at__gt=timezone.now() - timedelta(seconds=60)).exists()
        if recent:
            return Response({'detail': 'A code was just sent. Please wait a minute before retrying.'},
                            status=status.HTTP_429_TOO_MANY_REQUESTS)
        code = f'{random.randint(0, 999999):06d}'
        EmailVerification.objects.create(
            email=email, code=code, expires_at=timezone.now() + timedelta(minutes=15))
        mailer.send_code(
            subject='Your verification code',
            intro='Enter this code to complete your registration on the Ibeju-Lekki Street '
                  'Naming Registration Management System.',
            code=code,
            to=email,
        )
        return Response({'status': 'sent', 'message': 'A verification code has been sent to your email.'})


class PasswordResetRequestView(APIView):
    """POST /auth/password-reset/ {email} — email a 6-digit code to reset a forgotten password."""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        import random
        from datetime import timedelta
        from django.utils import timezone
        from accounts.models import EmailVerification, User
        from notifications import mailer

        email = (request.data.get('email') or '').strip().lower()
        # Always give the same response so we never reveal which emails are registered.
        generic = {'status': 'sent',
                   'message': 'If an account with that email exists, a reset code has been sent.'}
        if not email:
            return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return Response(generic)
        # light rate-limit: max 1 code per 60s per email
        recent = EmailVerification.objects.filter(
            email__iexact=email, created_at__gt=timezone.now() - timedelta(seconds=60)).exists()
        if recent:
            return Response(generic)
        code = f'{random.randint(0, 999999):06d}'
        EmailVerification.objects.create(
            email=email, code=code, expires_at=timezone.now() + timedelta(minutes=15))
        mailer.send_code(
            subject='Your password reset code',
            intro='Enter this code on the Ibeju-Lekki Street Naming Registration Management '
                  'System to set a new password.',
            code=code,
            to=email,
            outro='If you did not request this, you can safely ignore this email — your '
                  'password has not been changed.',
        )
        return Response(generic)


class PasswordResetConfirmView(APIView):
    """POST /auth/password-reset/confirm/ {email, code, new_password} — set a new password."""
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError as DjangoValidationError
        from accounts.models import EmailVerification, User

        email = (request.data.get('email') or '').strip().lower()
        code = (request.data.get('code') or '').strip()
        new_password = request.data.get('new_password') or ''
        if not (email and code and new_password):
            return Response({'detail': 'Email, code and new password are required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not EmailVerification.is_verified(email, code):
            return Response({'detail': 'Invalid or expired reset code.'},
                            status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return Response({'detail': 'Invalid or expired reset code.'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_password(new_password, user)
        except DjangoValidationError as exc:
            return Response({'detail': ' '.join(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save(update_fields=['password'])
        # Consume the code so it can't be reused.
        EmailVerification.objects.filter(
            email__iexact=email, code=code, consumed=False).update(consumed=True)
        return Response({'status': 'reset',
                         'message': 'Your password has been reset. You can now sign in.'})

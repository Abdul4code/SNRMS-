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

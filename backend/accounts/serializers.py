from django.contrib.auth import authenticate
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Role, User


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'full_name',
            'first_name',
            'last_name',
            'phone',
            'role',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'email', 'full_name', 'first_name', 'last_name', 'phone', 'role', 'created_at']


class RegisterSerializer(serializers.ModelSerializer):
    verification_code = serializers.CharField(write_only=True, required=True)
    phone = serializers.CharField(required=True, allow_blank=False)

    def validate(self, attrs):
        from accounts.models import EmailVerification
        email = attrs.get('email', '')
        code = attrs.get('verification_code', '')
        if not EmailVerification.is_verified(email, code):
            raise serializers.ValidationError({'verification_code': 'Invalid or expired verification code.'})
        return attrs
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'phone', 'verification_code']

    def create(self, validated_data):
        from accounts.models import EmailVerification
        code = validated_data.pop('verification_code', None)
        try:
            user = User.objects.create_user(
                email=validated_data['email'],
                password=validated_data['password'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                phone=validated_data['phone'],
                role=Role.APPLICANT,
            )
        except IntegrityError:
            # A concurrent submit (double-click / retry on a slow request) can slip
            # past the uniqueness validator and collide on insert. Return a clean
            # 400 instead of an unhandled 500 HTML page.
            raise serializers.ValidationError(
                {'email': ['An account with this email already exists.']})
        # Consume the verification code so it can't be reused.
        EmailVerification.objects.filter(
            email__iexact=validated_data['email'], code=code, consumed=False,
        ).update(consumed=True)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        # Normalise the email so a stray space or capitalisation doesn't cause a
        # false "invalid credentials" (emails are stored lower-cased).
        email = (attrs.get('email') or '').strip().lower()
        password = attrs.get('password')

        user = authenticate(request=self.context.get('request'), email=email, password=password)

        if not user:
            raise serializers.ValidationError('Invalid email or password.')

        if not user.is_active:
            raise serializers.ValidationError('This account has been deactivated.')

        refresh = RefreshToken.for_user(user)
        tokens = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

        attrs['user'] = user
        attrs['tokens'] = tokens
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class StaffCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'phone', 'role']

    def validate_role(self, value):
        if value == Role.APPLICANT:
            raise serializers.ValidationError(
                'Staff members cannot be assigned the applicant role.'
            )
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data.get('phone', ''),
            role=validated_data['role'],
            is_staff=True,
        )

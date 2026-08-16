from django.urls import path

from .views import (
    ChangePasswordView,
    LoginView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ProfileView,
    RegisterView,
    RequestEmailCodeView,
    StaffDetailView,
    StaffListView,
    TokenRefreshView,
)

app_name = 'accounts'

urlpatterns = [
    # Public auth
    path('request-verification/', RequestEmailCodeView.as_view(), name='request-verification'),
    path('register/', RegisterView.as_view(), name='register'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # Authenticated user — own profile
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),

    # Staff management (committee chairman only)
    path('staff/', StaffListView.as_view(), name='staff-list'),
    path('staff/<uuid:pk>/', StaffDetailView.as_view(), name='staff-detail'),
]

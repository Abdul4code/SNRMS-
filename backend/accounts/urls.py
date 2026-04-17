from django.urls import path

from .views import (
    ChangePasswordView,
    LoginView,
    ProfileView,
    RegisterView,
    StaffDetailView,
    StaffListView,
    TokenRefreshView,
)

app_name = 'accounts'

urlpatterns = [
    # Public auth
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # Authenticated user — own profile
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),

    # Staff management (committee chairman only)
    path('staff/', StaffListView.as_view(), name='staff-list'),
    path('staff/<uuid:pk>/', StaffDetailView.as_view(), name='staff-detail'),
]

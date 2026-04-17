from django.urls import path

from .views import (
    ApplicationPaymentsView,
    ConfirmPaymentView,
    FeeBreakdownView,
    FeeConfigListView,
    FeeConfigUpdateView,
    PaymentDetailView,
    SubmitPaymentView,
)

app_name = 'payments'

urlpatterns = [
    # Payments nested under applications
    path(
        'applications/<uuid:app_id>/payments/',
        ApplicationPaymentsView.as_view(),
        name='application-payments-list',
    ),

    # Single payment resource
    path(
        '<uuid:pk>/',
        PaymentDetailView.as_view(),
        name='payment-detail',
    ),

    # Payment actions
    path(
        '<uuid:pk>/submit/',
        SubmitPaymentView.as_view(),
        name='payment-submit',
    ),
    path(
        '<uuid:pk>/confirm/',
        ConfirmPaymentView.as_view(),
        name='payment-confirm',
    ),

    # Fee breakdown (public)
    path(
        'fees/breakdown/',
        FeeBreakdownView.as_view(),
        name='fee-breakdown',
    ),

    # Fee configuration (finance/chairman)
    path(
        'fees/config/',
        FeeConfigListView.as_view(),
        name='fee-config-list',
    ),
    path(
        'fees/config/<uuid:pk>/',
        FeeConfigUpdateView.as_view(),
        name='fee-config-detail',
    ),
]

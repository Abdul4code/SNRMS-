from django.urls import path

from .views import (
    ApplicationPaymentsView,
    OfficialSignatureView,
    PendingConfirmationView,
    ReceiptDownloadView,
    ReceiptVerifyView,
    InitializePaymentView,
    VerifyPaymentView,
    SimulatePaymentView,
    IbejuPayWebhookView,
    ConfirmPaymentView,
    FeeBreakdownView,
    FeeConfigListView,
    FeeConfigUpdateView,
    PaymentDetailView,
    PaymentStatsView,
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

    # Secure receipts (#13)
    path('signature/', OfficialSignatureView.as_view(), name='official-signature'),
    path('pending-confirmation/', PendingConfirmationView.as_view(), name='payment-pending-confirmation'),
    path('receipts/verify/<str:serial>/', ReceiptVerifyView.as_view(), name='receipt-verify'),
    path('receipts/<str:serial>/download/', ReceiptDownloadView.as_view(), name='receipt-download'),

    # Online payment gateway
    path('<uuid:pk>/initialize/', InitializePaymentView.as_view(), name='payment-initialize'),
    path('<uuid:pk>/simulate/', SimulatePaymentView.as_view(), name='payment-simulate'),
    path('verify/', VerifyPaymentView.as_view(), name='payment-verify'),
    path('ibejupay/webhook/', IbejuPayWebhookView.as_view(), name='ibejupay-webhook'),

    # Payment stats (finance/chairman)
    path(
        'stats/',
        PaymentStatsView.as_view(),
        name='payment-stats',
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

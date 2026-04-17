from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Role
from applications.models import Application
from config.models import FeeConfiguration

from .models import Payment, PaymentStage, PaymentStatus
from .serializers import (
    FeeConfigurationSerializer,
    FeeConfigurationUpdateSerializer,
    PaymentConfirmSerializer,
    PaymentSerializer,
    PaymentSubmitSerializer,
)
from .services import (
    calculate_renewal_fee,
    confirm_renewal_payment,
    confirm_stage_a_payment,
    confirm_stage_c_payment,
    get_stage_a_fee_breakdown,
    get_stage_c_fee_breakdown,
    get_total_fee,
    reject_payment,
)


# ---------------------------------------------------------------------------
# Permission helpers
# ---------------------------------------------------------------------------

def _is_finance_or_chairman(user) -> bool:
    return user.role in (Role.FINANCE, Role.COMMITTEE_CHAIRMAN)


def _is_staff_role(user) -> bool:
    return user.role in (Role.FINANCE, Role.NAMING_COMMITTEE, Role.COMMITTEE_CHAIRMAN)


# ---------------------------------------------------------------------------
# ApplicationPaymentsView
# ---------------------------------------------------------------------------

class ApplicationPaymentsView(generics.ListAPIView):
    """
    GET /api/applications/<app_id>/payments/

    Applicants see payments for their own application only.
    Finance / committee staff see all payments for any application.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        app_id = self.kwargs['app_id']
        user = self.request.user

        if _is_staff_role(user):
            application = get_object_or_404(Application, pk=app_id, is_deleted=False)
        else:
            application = get_object_or_404(
                Application, pk=app_id, applicant=user, is_deleted=False
            )

        return Payment.objects.filter(application=application).select_related(
            'confirmed_by', 'submitted_by'
        )


# ---------------------------------------------------------------------------
# PaymentDetailView
# ---------------------------------------------------------------------------

class PaymentDetailView(generics.RetrieveAPIView):
    """GET /api/payments/<pk>/"""
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_object(self):
        user = self.request.user
        payment = get_object_or_404(
            Payment.objects.select_related('confirmed_by', 'submitted_by', 'application'),
            pk=self.kwargs['pk'],
        )

        # Applicants may only see payments for their own applications
        if not _is_staff_role(user) and payment.application.applicant != user:
            from rest_framework.exceptions import NotFound
            raise NotFound('Payment not found.')

        return payment


# ---------------------------------------------------------------------------
# SubmitPaymentView
# ---------------------------------------------------------------------------

class SubmitPaymentView(APIView):
    """
    POST /api/payments/<pk>/submit/

    Applicant submits payment reference details for a pending payment.
    Validates that the payment belongs to the requesting user's application.
    Updates the payment record and marks status as 'submitted'.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        payment = get_object_or_404(
            Payment.objects.select_related('application'),
            pk=pk,
        )

        # Ownership check
        if payment.application.applicant != request.user:
            return Response(
                {'detail': 'You do not have permission to submit this payment.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Payment must be in pending or rejected state to allow re-submission
        if payment.status not in (PaymentStatus.PENDING, PaymentStatus.REJECTED):
            return Response(
                {
                    'detail': (
                        f'Payment cannot be submitted from its current status '
                        f'"{payment.status}". Only pending or rejected payments can be submitted.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PaymentSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        now = timezone.now()

        payment.payment_reference = data['payment_reference']
        payment.bank_name = data.get('bank_name', payment.bank_name)
        payment.payment_date = data.get('payment_date', payment.payment_date)
        payment.amount_submitted = data['amount_submitted']
        if 'receipt_file' in data and data['receipt_file'] is not None:
            payment.receipt_file = data['receipt_file']

        # Mark as submitted
        payment.status = PaymentStatus.SUBMITTED
        payment.submitted_by = request.user
        payment.submitted_at = now

        payment.save(update_fields=[
            'payment_reference',
            'bank_name',
            'payment_date',
            'amount_submitted',
            'receipt_file',
            'status',
            'submitted_by',
            'submitted_at',
            'updated_at',
        ])

        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# ConfirmPaymentView
# ---------------------------------------------------------------------------

class ConfirmPaymentView(APIView):
    """
    POST /api/payments/<pk>/confirm/

    Finance only. Confirms or rejects a submitted payment.
    Delegates to the correct stage-specific service function.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not _is_finance_or_chairman(request.user):
            return Response(
                {'detail': 'Only finance staff can confirm or reject payments.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        payment = get_object_or_404(
            Payment.objects.select_related('application'),
            pk=pk,
        )

        if payment.status != PaymentStatus.SUBMITTED:
            return Response(
                {
                    'detail': (
                        f'Payment must be in "submitted" status to be confirmed or rejected. '
                        f'Current status: "{payment.status}".'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PaymentConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        decision = data['status']
        remarks = data.get('finance_remarks', '')

        try:
            if decision == PaymentStatus.REJECTED:
                reject_payment(payment, actor=request.user, remarks=remarks)
            else:
                # decision == 'confirmed' — dispatch to the right stage handler
                if payment.stage == PaymentStage.STAGE_A:
                    confirm_stage_a_payment(payment, actor=request.user)
                elif payment.stage == PaymentStage.STAGE_C:
                    confirm_stage_c_payment(payment, actor=request.user)
                elif payment.stage == PaymentStage.RENEWAL:
                    confirm_renewal_payment(payment, actor=request.user)
                else:
                    return Response(
                        {'detail': f'Unknown payment stage: {payment.stage}'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Persist any finance_remarks even on confirmation
                if remarks:
                    payment.finance_remarks = remarks
                    payment.save(update_fields=['finance_remarks'])

        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# FeeBreakdownView
# ---------------------------------------------------------------------------

class FeeBreakdownView(APIView):
    """
    GET /api/fees/breakdown/?stage=stage_a
    GET /api/fees/breakdown/?stage=stage_c&street_type=<uuid>

    Returns the fee breakdown and total for the requested stage.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        stage = request.query_params.get('stage')

        if stage == 'stage_a':
            breakdown = get_stage_a_fee_breakdown()
            total = get_total_fee(breakdown)
            return Response({'stage': stage, 'breakdown': breakdown, 'total': total})

        elif stage == 'stage_c':
            street_type_id = request.query_params.get('street_type')
            if not street_type_id:
                return Response(
                    {'detail': 'street_type query parameter is required for stage_c breakdown.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            breakdown = get_stage_c_fee_breakdown(street_type_id)
            total = get_total_fee(breakdown)
            return Response({'stage': stage, 'breakdown': breakdown, 'total': total})

        elif stage == 'renewal':
            fee = calculate_renewal_fee()
            if fee is None:
                return Response(
                    {'detail': 'No active renewal fee configuration found.'},
                    status=status.HTTP_404_NOT_FOUND,
                )
            breakdown = [fee]
            total = get_total_fee(breakdown)
            return Response({'stage': stage, 'breakdown': breakdown, 'total': total})

        else:
            return Response(
                {
                    'detail': (
                        'stage query parameter is required. '
                        'Valid values: stage_a, stage_c, renewal.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


# ---------------------------------------------------------------------------
# FeeConfigListView
# ---------------------------------------------------------------------------

class FeeConfigListView(generics.ListAPIView):
    """
    GET /api/fees/config/

    Finance / Chairman only. Lists all fee configurations.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = FeeConfigurationSerializer

    def get_queryset(self):
        if not _is_finance_or_chairman(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only finance staff can view fee configurations.')
        return FeeConfiguration.objects.select_related('street_type').order_by('component')


# ---------------------------------------------------------------------------
# FeeConfigUpdateView
# ---------------------------------------------------------------------------

class FeeConfigUpdateView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/fees/config/<pk>/   — retrieve a single fee configuration
    PATCH /api/fees/config/<pk>/   — update amount and/or is_active (Finance only)
    """
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_queryset(self):
        return FeeConfiguration.objects.select_related('street_type').all()

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return FeeConfigurationUpdateSerializer
        return FeeConfigurationSerializer

    def get_object(self):
        if not _is_finance_or_chairman(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only finance staff can access fee configurations.')
        return super().get_object()

    def partial_update(self, request, *args, **kwargs):
        if not _is_finance_or_chairman(request.user):
            return Response(
                {'detail': 'Only finance staff can update fee configurations.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        instance = self.get_object()
        serializer = FeeConfigurationUpdateSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Set updated_by before saving
        instance = serializer.save(updated_by=request.user)

        return Response(
            FeeConfigurationSerializer(instance).data,
            status=status.HTTP_200_OK,
        )

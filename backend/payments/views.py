from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Role
from applications.models import Application, ApplicationStatus
from config.models import FeeConfiguration

from .models import Payment, PaymentStage, PaymentStatus
from .serializers import (
    FeeConfigurationCreateSerializer,
    FeeConfigurationSerializer,
    FeeConfigurationUpdateSerializer,
    PaymentConfirmSerializer,
    PaymentSerializer,
    PaymentSubmitSerializer,
)
from .services import (
    calculate_renewal_fee,
    calculate_revalidation_fee,
    confirm_renewal_payment,
    confirm_revalidation_payment,
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
        # Payments are routed exclusively through the Ibeju Pay gateway. The manual
        # teller/reference path is closed for applicants; staff may still record a
        # payment out-of-band if the council needs to (e.g. a verified bank transfer).
        if getattr(request.user, 'role', None) == 'applicant':
            return Response(
                {'detail': 'Payments must be made online through the payment gateway. '
                           'Please use the "Pay online" option.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
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

        # Transition application status to awaiting confirmation
        application = payment.application
        if application.status == ApplicationStatus.AWAITING_STAGE_A_PAYMENT:
            application.transition_to(
                ApplicationStatus.AWAITING_STAGE_A_PAYMENT_CONFIRMATION,
                actor=request.user,
                remarks='Payment evidence submitted by applicant.',
            )
        elif application.status == ApplicationStatus.AWAITING_STAGE_C_PAYMENT:
            application.transition_to(
                ApplicationStatus.AWAITING_STAGE_C_PAYMENT_CONFIRMATION,
                actor=request.user,
                remarks='Stage C payment evidence submitted by applicant.',
            )
        elif application.status == ApplicationStatus.AWAITING_RENEWAL_PAYMENT:
            application.transition_to(
                ApplicationStatus.AWAITING_RENEWAL_PAYMENT_CONFIRMATION,
                actor=request.user,
                remarks='Renewal payment evidence submitted by applicant.',
            )

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

        try:
            if decision == PaymentStatus.REJECTED:
                # The Council Treasurer does not add remarks — only confirms or declines.
                reject_payment(payment, actor=request.user, remarks='')
            else:
                # decision == 'confirmed' — dispatch to the right stage handler
                if payment.stage == PaymentStage.STAGE_A:
                    confirm_stage_a_payment(payment, actor=request.user)
                elif payment.stage == PaymentStage.STAGE_C:
                    confirm_stage_c_payment(payment, actor=request.user)
                elif payment.stage == PaymentStage.REVALIDATION:
                    confirm_revalidation_payment(payment, actor=request.user)
                elif payment.stage == PaymentStage.RENEWAL:
                    confirm_renewal_payment(payment, actor=request.user)
                else:
                    return Response(
                        {'detail': f'Unknown payment stage: {payment.stage}'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        # Issue the secure receipt now that the Council Treasurer has confirmed (#3/#13).
        if payment.status == PaymentStatus.CONFIRMED:
            try:
                from .receipts import generate_receipt
                generate_receipt(payment)
            except Exception:  # noqa: BLE001 - never break confirmation on receipt error
                import logging
                logging.getLogger(__name__).exception('Receipt generation failed for %s', payment.id)

        return Response(
            PaymentSerializer(payment).data,
            status=status.HTTP_200_OK,
        )


class PendingConfirmationView(APIView):
    """GET /payments/pending-confirmation/ — payments the CT still needs to confirm (#8)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _is_finance_or_chairman(request.user):
            return Response({'detail': 'Finance only.'}, status=status.HTTP_403_FORBIDDEN)
        qs = (Payment.objects.filter(status=PaymentStatus.SUBMITTED)
              .select_related('application', 'application__applicant').order_by('-submitted_at'))
        rows = []
        for p in qs:
            app = p.application
            rows.append({
                'id': str(p.id),
                'reference': p.payment_reference or '',
                'stage': p.stage,
                'amount': float(p.amount_submitted or p.amount_expected),
                'submitted_at': p.submitted_at,
                'street_name': app.proposed_street_name,
                'application_ref': app.reference_number or str(app.id),
                'applicant_name': f'{app.applicant.first_name} {app.applicant.last_name}'.strip() if app.applicant else '',
                'applicant_email': app.applicant.email if app.applicant else '',
            })
        return Response({'count': len(rows), 'results': rows})


# ---------------------------------------------------------------------------
# PaymentStatsView
# ---------------------------------------------------------------------------

class PaymentStatsView(APIView):
    """
    GET /api/payments/stats/

    Finance / Chairman only. Returns confirmed payment totals grouped by stage.
    Response: { stage_a: { count, total }, stage_c: { count, total }, renewal: { count, total } }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _is_finance_or_chairman(request.user):
            return Response(
                {'detail': 'Only finance staff can view payment stats.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        confirmed_qs = Payment.objects.filter(status=PaymentStatus.CONFIRMED)
        result = {}
        for stage_key in (PaymentStage.STAGE_A, PaymentStage.STAGE_C, PaymentStage.RENEWAL):
            qs = confirmed_qs.filter(stage=stage_key)
            count = qs.count()
            total = qs.aggregate(total=Sum('amount_expected'))['total'] or 0
            result[stage_key] = {'count': count, 'total': str(total)}

        return Response(result)


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
            # The final (Stage C) amount is hidden from applicants until the
            # Chairman approves the application and the Stage C payment is raised.
            if getattr(request.user, 'role', None) in (None, 'applicant') or not request.user.is_authenticated:
                return Response(
                    {'detail': 'The Stage C amount becomes available after approval.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            street_type_id = request.query_params.get('street_type')
            if not street_type_id:
                return Response(
                    {'detail': 'street_type query parameter is required for stage_c breakdown.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            breakdown = get_stage_c_fee_breakdown(street_type_id)
            total = get_total_fee(breakdown)
            return Response({'stage': stage, 'breakdown': breakdown, 'total': total})

        elif stage in ('revalidation', 'renewal'):
            # Both are a share of the street-name fee, so they need the street
            # type; it stays optional for backwards compatibility, falling back
            # to any street-type-agnostic row that is still configured.
            street_type_id = request.query_params.get('street_type')
            if stage == 'revalidation':
                fee = calculate_revalidation_fee(street_type_id)
            else:
                fee = calculate_renewal_fee(street_type_id)
            if fee is None:
                return Response(
                    {'detail': f'No active {stage} fee configuration found.'},
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
                        'Valid values: stage_a, stage_c, revalidation, renewal.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


# ---------------------------------------------------------------------------
# FeeConfigListView
# ---------------------------------------------------------------------------

class FeeConfigListView(generics.ListCreateAPIView):
    """
    GET  /api/fees/config/ — list all fee configurations (finance/chairman)
    POST /api/fees/config/ — create a new fee configuration (finance/chairman)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = FeeConfigurationSerializer
    pagination_class = None  # fee types are a small bounded set

    def get_queryset(self):
        if not _is_finance_or_chairman(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only finance staff can view fee configurations.')
        return FeeConfiguration.objects.select_related('street_type').order_by('component')

    def create(self, request, *args, **kwargs):
        if not _is_finance_or_chairman(request.user):
            return Response(
                {'detail': 'Only finance staff can create fee configurations.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = FeeConfigurationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(updated_by=request.user)
        return Response(
            FeeConfigurationSerializer(instance).data,
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# FeeConfigUpdateView
# ---------------------------------------------------------------------------

class FeeConfigUpdateView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/fees/config/<pk>/ — retrieve a single fee configuration
    PATCH  /api/fees/config/<pk>/ — update component, amount, street_type, is_active
    DELETE /api/fees/config/<pk>/ — delete a fee configuration
    """
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

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
        instance = serializer.save(updated_by=request.user)
        return Response(FeeConfigurationSerializer(instance).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        if not _is_finance_or_chairman(request.user):
            return Response(
                {'detail': 'Only finance staff can delete fee configurations.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Online payment gateway (Ibeju Pay) — with demo fallback
# ---------------------------------------------------------------------------
from django.conf import settings as _settings  # noqa: E402
from django.utils.decorators import method_decorator  # noqa: E402
from django.views.decorators.csrf import csrf_exempt  # noqa: E402
from . import gateway  # noqa: E402


class InitializePaymentView(APIView):
    """POST /payments/<pk>/initialize/ — start an online payment for a payment record."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        payment = get_object_or_404(Payment.objects.select_related('application', 'application__applicant'), pk=pk)
        if payment.application.applicant_id != request.user.id:
            return Response({'detail': 'Not your payment.'}, status=status.HTTP_403_FORBIDDEN)
        if payment.status == PaymentStatus.CONFIRMED:
            return Response({'detail': 'This payment is already confirmed.'}, status=status.HTTP_400_BAD_REQUEST)

        if not gateway.is_configured():
            # Demo mode: no keys — front-end will offer a "simulate" action.
            payment.payment_reference = gateway.new_reference(payment)
            payment.save(update_fields=['payment_reference', 'updated_at'])
            return Response({'mode': 'demo', 'reference': payment.payment_reference})

        callback = request.data.get('callback_url') or _settings.PAYMENT_CALLBACK_URL
        try:
            result = gateway.initialize(payment, email=request.user.email, callback_url=callback)
        except Exception as exc:  # noqa: BLE001
            return Response({'detail': f'Gateway error: {exc}'}, status=status.HTTP_502_BAD_GATEWAY)
        return Response({'mode': 'ibejupay', **result})


class VerifyPaymentView(APIView):
    """GET /payments/verify/?reference=... — verify an Ibeju Pay transaction and confirm."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reference = request.query_params.get('reference', '')
        payment = get_object_or_404(Payment.objects.select_related('application'), payment_reference=reference)
        if not gateway.is_configured():
            return Response({'detail': 'Gateway not configured.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = gateway.verify(reference)
        except Exception as exc:  # noqa: BLE001
            return Response({'detail': f'Gateway error: {exc}'}, status=status.HTTP_502_BAD_GATEWAY)
        if not result['success']:
            return Response({'status': 'failed', 'detail': 'Payment not successful.'}, status=status.HTTP_400_BAD_REQUEST)
        gateway.mark_paid(payment, amount=result['amount'])
        return Response({'status': 'confirmed', 'payment': PaymentSerializer(payment).data})


class SimulatePaymentView(APIView):
    """POST /payments/<pk>/simulate/ — demo only: mark an online payment as paid.

    Enabled only when no live gateway is configured (i.e. demo installs), so it
    can never bypass a real gateway in production.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if gateway.is_configured():
            return Response({'detail': 'Simulation disabled when a live gateway is configured.'}, status=status.HTTP_400_BAD_REQUEST)
        payment = get_object_or_404(Payment.objects.select_related('application', 'application__applicant'), pk=pk)
        if payment.application.applicant_id != request.user.id:
            return Response({'detail': 'Not your payment.'}, status=status.HTTP_403_FORBIDDEN)
        if not payment.payment_reference:
            payment.payment_reference = gateway.new_reference(payment)
            payment.save(update_fields=['payment_reference', 'updated_at'])
        gateway.mark_paid(payment)
        return Response({'status': 'confirmed', 'payment': PaymentSerializer(payment).data})


@method_decorator(csrf_exempt, name='dispatch')
class IbejuPayWebhookView(APIView):
    """POST /payments/ibejupay/webhook/ — Ibeju Pay calls this on payment events."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        signature = request.META.get('HTTP_X_IBEJUPAY_SIGNATURE', '')
        if not gateway.is_configured() or not gateway.valid_signature(request.body, signature):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        event = request.data or {}
        if event.get('event') == 'charge.success':
            reference = event.get('data', {}).get('reference', '')
            try:
                payment = Payment.objects.select_related('application').get(payment_reference=reference)
                gateway.mark_paid(payment, amount=(event['data'].get('amount', 0) / 100))
            except Payment.DoesNotExist:
                pass
        return Response({'status': 'ok'})


# ---------------------------------------------------------------------------
# Secure receipts (#13)
# ---------------------------------------------------------------------------
from django.http import FileResponse, Http404  # noqa: E402
from .models import OfficialSignature, Receipt  # noqa: E402
from .receipts import generate_receipt, verify_code  # noqa: E402


def _is_finance_or_chairman(user):
    return getattr(user, 'role', None) in ('finance', 'committee_chairman')


class OfficialSignatureView(APIView):
    """GET/POST /payments/signature/ — the CT uploads their e-signature once."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sig = OfficialSignature.current()
        if not sig:
            return Response({'uploaded': False})
        return Response({'uploaded': True, 'signatory_name': sig.signatory_name,
                         'signatory_title': sig.signatory_title, 'uploaded_at': sig.uploaded_at})

    def post(self, request):
        if not _is_finance_or_chairman(request.user):
            return Response({'detail': 'Only the Council Treasurer can upload the signature.'},
                            status=status.HTTP_403_FORBIDDEN)
        image = request.FILES.get('image')
        if not image:
            return Response({'detail': 'A signature image is required.'}, status=status.HTTP_400_BAD_REQUEST)
        sig = OfficialSignature.current() or OfficialSignature()
        sig.image = image
        sig.signatory_name = request.data.get('signatory_name', sig.signatory_name or 'Council Treasurer')
        sig.signatory_title = request.data.get('signatory_title', sig.signatory_title or 'Council Treasurer, Ibeju-Lekki LGA')
        sig.uploaded_by = request.user
        sig.save()
        return Response({'status': 'saved', 'signatory_name': sig.signatory_name})


class ReceiptDownloadView(APIView):
    """GET /payments/receipts/<serial>/download/ — the receipt PDF (owner or staff)."""
    permission_classes = [IsAuthenticated]

    def get(self, request, serial):
        receipt = get_object_or_404(Receipt, serial=serial)
        user = request.user
        is_owner = receipt.application.applicant_id == user.id
        if not (is_owner or _is_finance_or_chairman(user) or getattr(user, 'role', None) == 'naming_committee'):
            return Response({'detail': 'Not permitted.'}, status=status.HTTP_403_FORBIDDEN)
        # The applicant can only download once the CT has confirmed the payment (#3).
        if is_owner and receipt.payment.status != PaymentStatus.CONFIRMED:
            return Response(
                {'detail': 'The receipt will be available once the Council Treasurer confirms your payment.'},
                status=status.HTTP_403_FORBIDDEN)
        if not receipt.pdf:
            generate_receipt(receipt.payment)
            receipt.refresh_from_db()
        return FileResponse(receipt.pdf.open('rb'), content_type='application/pdf',
                            as_attachment=True, filename=f'{serial}.pdf')


class ReceiptVerifyView(APIView):
    """GET /payments/receipts/verify/<serial>/?code=... — PUBLIC authenticity check."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, serial):
        receipt = Receipt.objects.filter(serial=serial).select_related('application').first()
        if not receipt:
            return Response({'valid': False, 'reason': 'No receipt with this serial number.'},
                            status=status.HTTP_404_NOT_FOUND)
        code = request.query_params.get('code', '')
        ok = verify_code(receipt.serial, receipt.amount, receipt.reference, receipt.payer_name, code) \
            or code == receipt.security_code
        if not ok:
            return Response({'valid': False, 'reason': 'Security code does not match — this receipt is not authentic.'})
        return Response({
            'valid': True,
            'serial': receipt.serial,
            'payer_name': receipt.payer_name,
            'amount': f'{float(receipt.amount):,.2f}',
            'street_name': receipt.application.proposed_street_name,
            'stage': receipt.stage,
            'reference': receipt.reference,
            'issued_at': receipt.issued_at,
            'message': 'This is an authentic receipt issued by Ibeju-Lekki LGA.',
        })

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Role
from notifications.models import NotificationType

from .models import Application, ApplicationStatus, StatusHistory
from .street_locks import lock_state, street_holder
from .serializers import (
    ApplicationCreateSerializer,
    ApplicationDetailSerializer,
    ApplicationListSerializer,
    ApplicationUpdateSerializer,
    StatusHistorySerializer,
)
from .services import (
    check_street_name_duplicate,
    issue_certificate,
    notify_applicant,
    submit_application,
    submit_payment_reference,
)


# ---------------------------------------------------------------------------
# Permission helpers
# ---------------------------------------------------------------------------

def _is_staff_role(user) -> bool:
    """Return True for any non-applicant role (finance, committee, chairman)."""
    return user.role in (
        Role.FINANCE,
        Role.NAMING_COMMITTEE,
        Role.COMMITTEE_CHAIRMAN,
    )


def _get_application_or_404(pk, user):
    """
    Return the Application for pk, enforcing ownership / staff visibility
    and filtering out soft-deleted records.
    """
    qs = Application.objects.filter(is_deleted=False)
    application = get_object_or_404(qs, pk=pk)

    if _is_staff_role(user):
        return application

    # Applicants may only see their own applications
    if application.applicant != user:
        return None  # Caller will return 404

    return application


# ---------------------------------------------------------------------------
# ApplicationListCreateView
# ---------------------------------------------------------------------------

def _auto_expire_certificates():
    """
    Transition any certificate_issued applications whose expiry date has passed.
    Called on every list request — cheap because it only writes when rows are due.
    """
    import datetime as _dt
    from notifications.models import NotificationType as _NT
    today = _dt.date.today()
    due = Application.objects.filter(
        status=ApplicationStatus.CERTIFICATE_ISSUED,
        expires_at__lte=today,
        is_deleted=False,
    )
    for app in due:
        try:
            app.transition_to(ApplicationStatus.EXPIRED, actor=None, remarks='')
            notify_applicant(
                app,
                notification_type=_NT.APPLICATION_STATUS_CHANGE,
                title='Certificate Expired',
                message=(
                    f'Your street naming certificate for application {app.reference_number} '
                    f'expired on {app.expires_at.strftime("%d %B %Y")}. '
                    'Please renew to keep your registration active.'
                ),
            )
        except ValueError:
            pass


def street_under_consideration(lat, lng, exclude_id=None):
    """The application holding this street, or None if it is free.

    A hold lapses when its owner stops moving — unpaid after three days, or
    undecided a month after payment — so this returns None for a street whose
    previous applicant has run out of time. See applications/street_locks.py.
    """
    return street_holder(lat, lng, exclude_id)


class StreetAvailabilityView(APIView):
    """GET /api/applications/street-availability/?lat=&lng= — can this street be
    registered, or is another applicant already holding it?"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            lat = float(request.query_params.get('lat'))
            lng = float(request.query_params.get('lng'))
        except (TypeError, ValueError):
            return Response({'available': True})
        holder = street_holder(lat, lng)
        if holder:
            state = lock_state(holder)
            if state['kind'] == 'settled':
                reason = 'This street has already been registered.'
            elif state['kind'] == 'unpaid':
                reason = ('Another applicant is applying for this street. If they do not pay '
                          'within 3 days of applying, it opens again.')
            else:
                reason = ('Another applicant has paid for this street and it is awaiting a '
                          'decision. It opens again one month after their payment if no '
                          'decision has been made.')
            return Response({
                'available': False,
                'reason': reason,
                'opens_at': state['expires_at'],
            })
        return Response({'available': True})


class ApplicationListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/applications/        — list applications
    POST /api/applications/        — create a new application (applicants only)
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Application.objects.filter(is_deleted=False).select_related(
            'applicant', 'street_type'
        )

        if not _is_staff_role(user):
            qs = qs.filter(applicant=user)
        else:
            # Staff never need to see draft or withdrawn applications
            qs = qs.exclude(status__in=[
                ApplicationStatus.DRAFT,
                ApplicationStatus.WITHDRAWN,
            ])

        status_filter = self.request.query_params.get('status')
        if status_filter:
            statuses = [s.strip() for s in status_filter.split(',') if s.strip()]
            if len(statuses) == 1:
                qs = qs.filter(status=statuses[0])
            elif statuses:
                qs = qs.filter(status__in=statuses)

        return qs

    def list(self, request, *args, **kwargs):
        if request.method == 'GET':
            _auto_expire_certificates()
        return super().list(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ApplicationCreateSerializer
        return ApplicationListSerializer

    def create(self, request, *args, **kwargs):
        if request.user.role != Role.APPLICANT:
            return Response(
                {'detail': 'Only applicants can create applications.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        # Hold a street for whoever is actively pursuing it. The hold lapses if they
        # do not pay, or if a month passes after payment with no decision, and then
        # anyone may apply again. Legacy (validate-existing) applications are for
        # already-named streets, so they skip this.
        is_legacy = str(request.data.get('is_legacy', '')).lower() in ('true', '1')
        if not is_legacy:
            try:
                lat = float(request.data.get('latitude'))
                lng = float(request.data.get('longitude'))
            except (TypeError, ValueError):
                lat = lng = None
            holder = street_holder(lat, lng) if (lat is not None and lng is not None) else None
            if holder:
                state = lock_state(holder)
                if state['kind'] == 'settled':
                    detail = 'This street has already been registered.'
                elif state['kind'] == 'unpaid':
                    detail = ('Another applicant is applying for this street. If they do not '
                              'pay within 3 days of applying, it opens again.')
                else:
                    detail = ('Another applicant has paid for this street and it is awaiting a '
                              'decision. It opens again one month after their payment if no '
                              'decision has been made.')
                return Response({'detail': detail, 'opens_at': state['expires_at']},
                                status=status.HTTP_400_BAD_REQUEST)
        response = super().create(request, *args, **kwargs)
        # Validate-existing-registration flow: check the picked location against the
        # registry and flag the Street Naming Committee if it doesn't line up (#validate).
        try:
            if str(request.data.get('is_legacy', '')).lower() in ('true', '1') and response.status_code == 201:
                self._validate_legacy_location(request, response.data)
        except Exception:  # noqa: BLE001
            pass
        return response

    def _validate_legacy_location(self, request, data):
        import math
        from config.models import BuildingSurvey
        from accounts.models import User, Role as _Role
        from notifications.models import Notification, NotificationType
        app_id = data.get('id')
        application = Application.objects.filter(pk=app_id).first()
        if not application or application.latitude is None or application.longitude is None:
            return
        lat, lng = float(application.latitude), float(application.longitude)

        def _m(la, lo):
            return math.hypot((la - lat) * 111000, (lo - lng) * 111000 * math.cos(math.radians(lat)))

        # nearest NAMED survey point to the submitted location
        UNNAMED = {'', 'none', 'na', 'n/a', 'nil', 'null', 'no', 'nan', '-'}
        best, best_name = 1e9, ''
        for b in BuildingSurvey.objects.exclude(latitude=None).exclude(longitude=None):
            raw = (b.existing_street_name or '').strip()
            if raw.lower() in UNNAMED:
                continue
            d = _m(float(b.latitude), float(b.longitude))
            if d < best:
                best, best_name = d, raw

        def _norm(x):
            return ' '.join((x or '').strip().lower().split())

        selected = _norm(application.proposed_street_name)
        note = None
        if best > 60 or not best_name:
            note = (f'Validation flag: the street "{application.proposed_street_name}" selected by '
                    f'{application.applicant.full_name or application.applicant.email} for validation '
                    f'does not match any initially named street. Probably part of the old record.')
        elif _norm(best_name) != selected:
            note = (f'Validation flag: the name "{application.proposed_street_name}" the applicant wishes to '
                    f'validate does not match the name already in the database at that location '
                    f'("{best_name}").')
        if note:
            for u in User.objects.filter(role=_Role.NAMING_COMMITTEE, is_active=True):
                Notification.objects.create(
                    recipient=u,
                    notification_type=NotificationType.APPLICATION_STATUS_CHANGE,
                    title='Street validation needs review',
                    message=note,
                    application=application,
                )


# ---------------------------------------------------------------------------
# ApplicationDetailView
# ---------------------------------------------------------------------------

class ApplicationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/applications/<pk>/   — retrieve detail
    PATCH  /api/applications/<pk>/   — update (draft only, applicant owns it)
    DELETE /api/applications/<pk>/   — soft delete (draft only, applicant owns it)
    """
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_object(self):
        application = _get_application_or_404(self.kwargs['pk'], self.request.user)
        if application is None:
            from rest_framework.exceptions import NotFound
            raise NotFound('Application not found.')
        return application

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return ApplicationUpdateSerializer
        return ApplicationDetailSerializer

    def partial_update(self, request, *args, **kwargs):
        application = self.get_object()

        if request.user.role != Role.APPLICANT or application.applicant != request.user:
            return Response(
                {'detail': 'Only the owning applicant can update an application.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if application.status != ApplicationStatus.DRAFT:
            return Response(
                {'detail': 'Application can only be edited while in draft status.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(application, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ApplicationDetailSerializer(application, context={'request': request}).data)

    def destroy(self, request, *args, **kwargs):
        application = self.get_object()

        if request.user.role != Role.APPLICANT or application.applicant != request.user:
            return Response(
                {'detail': 'Only the owning applicant can delete an application.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if application.status != ApplicationStatus.DRAFT:
            return Response(
                {'detail': 'Only draft applications can be deleted.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        application.is_deleted = True
        application.save(update_fields=['is_deleted', 'updated_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# ApplicationSubmitView
# ---------------------------------------------------------------------------

class ApplicationSubmitView(APIView):
    """POST /api/applications/<pk>/submit/ — applicant submits a draft."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != Role.APPLICANT:
            return Response(
                {'detail': 'Only applicants can submit applications.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        application = _get_application_or_404(pk, request.user)
        if application is None:
            return Response({'detail': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)

        if application.applicant != request.user:
            return Response(
                {'detail': 'You do not own this application.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if application.status != ApplicationStatus.DRAFT:
            return Response(
                {'detail': f'Cannot submit an application with status "{application.status}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            submit_application(application, actor=request.user)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            ApplicationDetailSerializer(application, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# ApplicationWithdrawView
# ---------------------------------------------------------------------------

class ApplicationWithdrawView(APIView):
    """POST /api/applications/<pk>/withdraw/ — applicant withdraws a draft or submitted application."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != Role.APPLICANT:
            return Response(
                {'detail': 'Only applicants can withdraw applications.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        application = _get_application_or_404(pk, request.user)
        if application is None:
            return Response({'detail': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)

        if application.applicant != request.user:
            return Response(
                {'detail': 'You do not own this application.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        withdrawable_statuses = [ApplicationStatus.DRAFT, ApplicationStatus.SUBMITTED]
        if application.status not in withdrawable_statuses:
            return Response(
                {
                    'detail': (
                        f'Cannot withdraw an application with status "{application.status}". '
                        'Only draft or submitted applications can be withdrawn.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        remarks = request.data.get('remarks', 'Withdrawn by applicant.')
        try:
            application.transition_to(
                ApplicationStatus.WITHDRAWN,
                actor=request.user,
                remarks=remarks,
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        notify_applicant(
            application,
            notification_type=NotificationType.APPLICATION_STATUS_CHANGE,
            title='Application Withdrawn',
            message=(
                f'Your application {application.reference_number} has been withdrawn.'
            ),
        )

        return Response(
            ApplicationDetailSerializer(application, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# CommitteeReviewView
# ---------------------------------------------------------------------------

class CommitteeReviewView(APIView):
    """
    POST /api/applications/<pk>/committee-review/
    Body: { "decision": "approved"|"rejected", "remarks": "..." }
    Naming committee only. If approved, auto-transitions to awaiting_chairman_approval.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != Role.NAMING_COMMITTEE:
            return Response(
                {'detail': 'Only naming committee members can perform committee review.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        application = get_object_or_404(Application, pk=pk, is_deleted=False)

        if application.status != ApplicationStatus.UNDER_NAMING_COMMITTEE_REVIEW:
            return Response(
                {
                    'detail': (
                        f'Application must be in "under_naming_committee_review" status '
                        f'to perform a committee review. Current status: "{application.status}".'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        decision = request.data.get('decision')
        remarks = request.data.get('remarks', '')

        if decision not in ('approved', 'rejected'):
            return Response(
                {'detail': '"decision" must be either "approved" or "rejected".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if decision == 'approved':
            # All documents must be verified before the committee can approve
            from documents.models import Document
            unverified = Document.objects.filter(
                application=application,
                is_deleted=False,
                is_verified=False,
            ).exists()
            if unverified:
                return Response(
                    {'detail': 'All documents must be verified before approving the application.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            if decision == 'approved':
                # Record committee approval
                application.committee_remarks = remarks
                application.save(update_fields=['committee_remarks', 'updated_at'])
                application.transition_to(
                    ApplicationStatus.APPROVED_BY_COMMITTEE,
                    actor=request.user,
                    remarks=remarks,
                )
                # Auto-advance to awaiting chairman approval
                application.transition_to(
                    ApplicationStatus.AWAITING_CHAIRMAN_APPROVAL,
                    actor=request.user,
                    remarks='',
                )
                notify_applicant(
                    application,
                    notification_type=NotificationType.APPLICATION_APPROVED,
                    title='Application Approved by Committee',
                    message=(
                        f'Your application {application.reference_number} has been approved '
                        'by the naming committee and is now awaiting chairman approval.'
                    ),
                )
            else:
                application.committee_remarks = remarks
                application.save(update_fields=['committee_remarks', 'updated_at'])
                application.transition_to(
                    ApplicationStatus.REJECTED_BY_COMMITTEE,
                    actor=request.user,
                    remarks=remarks,
                )
                from applications.services import release_signboard_number
                release_signboard_number(application)
                notify_applicant(
                    application,
                    notification_type=NotificationType.APPLICATION_REJECTED,
                    title='Application Rejected by Committee',
                    message=(
                        f'Your application {application.reference_number} has been rejected '
                        f'by the naming committee. Remarks: {remarks}'
                    ),
                )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            ApplicationDetailSerializer(application, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# ChairmanApprovalView
# ---------------------------------------------------------------------------

class ChairmanApprovalView(APIView):
    """
    POST /api/applications/<pk>/chairman-approval/
    Body: { "decision": "approved"|"rejected", "remarks": "..." }
    Committee chairman only.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != Role.COMMITTEE_CHAIRMAN:
            return Response(
                {'detail': 'Only the committee chairman can perform chairman approval.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        application = get_object_or_404(Application, pk=pk, is_deleted=False)

        if application.status != ApplicationStatus.AWAITING_CHAIRMAN_APPROVAL:
            return Response(
                {
                    'detail': (
                        f'Application must be in "awaiting_chairman_approval" status. '
                        f'Current status: "{application.status}".'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        decision = request.data.get('decision')
        remarks = request.data.get('remarks', '')

        if decision not in ('approved', 'rejected'):
            return Response(
                {'detail': '"decision" must be either "approved" or "rejected".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            application.chairman_remarks = remarks
            application.save(update_fields=['chairman_remarks', 'updated_at'])

            if decision == 'approved':
                application.transition_to(
                    ApplicationStatus.APPROVED_BY_CHAIRMAN,
                    actor=request.user,
                    remarks=remarks,
                )

                # Auto-issue the next signboard/pole number on approval (recycled pool).
                from applications.services import allocate_signboard_number
                allocate_signboard_number(application)

                from decimal import Decimal as _Decimal
                from payments.models import Payment as _Payment, PaymentStage as _PS, PaymentStatus as _PStatus

                if application.is_legacy:
                    # Legacy: the street is already named, so Stage C is skipped
                    # and a revalidation fee is charged instead — a share of the
                    # street-name fee rather than the full schedule.
                    application.transition_to(
                        ApplicationStatus.AWAITING_RENEWAL_PAYMENT,
                        actor=request.user,
                        remarks='',
                    )
                    from payments.services import calculate_revalidation_fee
                    _reval_fee = calculate_revalidation_fee(application.street_type_id)
                    _Payment.objects.create(
                        application=application,
                        stage=_PS.REVALIDATION,
                        status=_PStatus.PENDING,
                        amount_expected=_reval_fee['amount'] if _reval_fee else _Decimal('0.00'),
                    )
                    notify_applicant(
                        application,
                        notification_type=NotificationType.APPLICATION_APPROVED,
                        title='Application Approved by Chairman',
                        message=(
                            f'Your application {application.reference_number} has been approved '
                            'by the chairman. As a legacy registration, please proceed with the '
                            'revalidation payment to complete your digital registration.'
                        ),
                    )
                else:
                    # Standard flow: advance to Stage C payment
                    application.transition_to(
                        ApplicationStatus.AWAITING_STAGE_C_PAYMENT,
                        actor=request.user,
                        remarks='',
                    )
                    from payments.services import get_stage_c_fee_breakdown, get_total_fee
                    _breakdown = get_stage_c_fee_breakdown(application.street_type_id)
                    _amount = get_total_fee(_breakdown) if _breakdown else _Decimal('0.00')
                    if application.is_royalty_exempt:
                        _amount = _Decimal('0.00')
                    _stage_c = _Payment.objects.create(
                        application=application,
                        stage=_PS.STAGE_C,
                        status=_PStatus.PENDING,
                        amount_expected=_amount,
                    )
                    if application.is_royalty_exempt:
                        # Royalty pays only the application fee — Stage C is waived and
                        # the certificate is issued without payment.
                        try:
                            from payments.services import confirm_stage_c_payment
                            from applications.services import issue_certificate
                            _stage_c.amount_submitted = _Decimal('0.00')
                            _stage_c.save(update_fields=['amount_submitted'])
                            application.transition_to(
                                ApplicationStatus.AWAITING_STAGE_C_PAYMENT_CONFIRMATION,
                                actor=request.user, remarks='')
                            confirm_stage_c_payment(_stage_c, actor=request.user)
                            application.refresh_from_db()
                            issue_certificate(application, actor=request.user)
                        except Exception:
                            import logging
                            logging.getLogger(__name__).exception('Royalty-exempt certificate issuance failed')
                    notify_applicant(
                        application,
                        notification_type=NotificationType.APPLICATION_APPROVED,
                        title='Application Approved by Chairman',
                        message=(
                            f'Your application {application.reference_number} has been approved '
                            'by the chairman. Please proceed with Stage C payment.'
                        ),
                    )
            else:
                application.transition_to(
                    ApplicationStatus.REJECTED_BY_CHAIRMAN,
                    actor=request.user,
                    remarks=remarks,
                )
                from applications.services import release_signboard_number
                release_signboard_number(application)
                notify_applicant(
                    application,
                    notification_type=NotificationType.APPLICATION_REJECTED,
                    title='Application Rejected by Chairman',
                    message=(
                        f'Your application {application.reference_number} has been rejected '
                        f'by the chairman. Remarks: {remarks}'
                    ),
                )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            ApplicationDetailSerializer(application, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# CertificateIssueView
# ---------------------------------------------------------------------------

class CertificateIssueView(APIView):
    """POST /api/applications/<pk>/issue-certificate/ — LG chairman only.

    Certificate generation is the chairman's responsibility; the naming
    committee only reviews and forwards its recommendation.
    """
    permission_classes = [IsAuthenticated]
    parser_classes_override = None  # accept multipart

    def post(self, request, pk):
        if request.user.role != Role.COMMITTEE_CHAIRMAN:
            return Response(
                {'detail': 'Only the Local Government Chairman can generate certificates.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        application = get_object_or_404(Application, pk=pk, is_deleted=False)

        if application.status != ApplicationStatus.STAGE_C_CONFIRMED:
            return Response(
                {
                    'detail': (
                        f'Application must be in "stage_c_confirmed" status to issue a certificate. '
                        f'Current status: "{application.status}".'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        certificate_file = request.FILES.get('certificate_file')

        expires_at = None
        expires_at_str = request.data.get('expires_at')
        if expires_at_str:
            import datetime as _dt
            try:
                expires_at = _dt.date.fromisoformat(expires_at_str)
            except ValueError:
                return Response(
                    {'detail': 'Invalid expires_at format. Use YYYY-MM-DD.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            issue_certificate(application, actor=request.user, expires_at=expires_at)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if certificate_file:
            application.certificate_file = certificate_file
            application.save(update_fields=['certificate_file', 'updated_at'])

        # The committee chairman decides whether the applicant may download it now.
        release = str(request.data.get('release', 'false')).lower() in ('1', 'true', 'yes', 'on')
        application.certificate_released = release
        application.save(update_fields=['certificate_released', 'updated_at'])

        if release:
            notify_applicant(
                application,
                notification_type=NotificationType.CERTIFICATE_ISSUED,
                title='Certificate Issued',
                message=(
                    f'Your street naming certificate for application {application.reference_number} '
                    'has been issued and is available to download from your application page.'
                ),
            )

        return Response(
            ApplicationDetailSerializer(application, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )


class CertificateReleaseView(APIView):
    """POST /api/applications/<pk>/certificate-release/ {released: bool} — the
    committee or LG chairman controls whether the applicant may download the
    certificate. The certificate itself always stays in the database.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if getattr(request.user, 'role', None) != 'committee_chairman':
            return Response({'detail': 'Only the LG Chairman can send certificates to the applicant.'},
                            status=status.HTTP_403_FORBIDDEN)
        application = get_object_or_404(Application, pk=pk, is_deleted=False)
        if not application.certificate_file:
            return Response({'detail': 'No certificate has been generated yet.'},
                            status=status.HTTP_400_BAD_REQUEST)
        released = str(request.data.get('released', 'true')).lower() in ('1', 'true', 'yes', 'on')
        application.certificate_released = released
        application.save(update_fields=['certificate_released', 'updated_at'])
        if released:
            notify_applicant(
                application,
                notification_type=NotificationType.CERTIFICATE_ISSUED,
                title='Certificate Available',
                message=(f'Your street naming certificate for application {application.reference_number} '
                         'is now available to download from your application page.'),
            )
        return Response({'certificate_released': application.certificate_released})


# ---------------------------------------------------------------------------
# ApplicationCompletionView
# ---------------------------------------------------------------------------

class ApplicationCompletionView(APIView):
    """
    PATCH /api/applications/<pk>/completion/
    Naming committee toggles google_map_uploaded and/or signpost_installed.
    Body: { "google_map_uploaded": true, "signpost_installed": true }
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if request.user.role != Role.NAMING_COMMITTEE:
            return Response(
                {'detail': 'Only naming committee members can update completion status.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        application = get_object_or_404(Application, pk=pk, is_deleted=False)

        if application.status != ApplicationStatus.CERTIFICATE_ISSUED:
            return Response(
                {'detail': 'Completion status can only be updated after certificate is issued.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        update_fields = ['updated_at']
        notifications = []

        google_map = request.data.get('google_map_uploaded')
        if google_map is not None and bool(google_map) != application.google_map_uploaded:
            application.google_map_uploaded = bool(google_map)
            update_fields.append('google_map_uploaded')
            if application.google_map_uploaded:
                notifications.append(('Google Map Uploaded', 'The Google Map for your street has been uploaded.'))

        signpost = request.data.get('signpost_installed')
        if signpost is not None and bool(signpost) != application.signpost_installed:
            application.signpost_installed = bool(signpost)
            update_fields.append('signpost_installed')
            if application.signpost_installed:
                notifications.append(('Sign Post Installed', 'The sign post for your street has been installed.'))

        application.save(update_fields=update_fields)

        for title, message in notifications:
            notify_applicant(
                application,
                notification_type=NotificationType.APPLICATION_STATUS_CHANGE,
                title=title,
                message=f'Application {application.reference_number}: {message}',
            )

        return Response(
            ApplicationDetailSerializer(application, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# RequestPaymentView
# ---------------------------------------------------------------------------

class RequestPaymentView(APIView):
    """
    POST /api/applications/<pk>/request-payment/

    Applicant finalises document upload and requests Stage A payment.
    If still draft:  draft → submitted → awaiting_stage_a_payment (+ creates Payment record).
    If submitted:    submitted → awaiting_stage_a_payment (+ creates Payment record).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != Role.APPLICANT:
            return Response(
                {'detail': 'Only applicants can request payment.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        application = _get_application_or_404(pk, request.user)
        if application is None:
            return Response({'detail': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)

        if application.applicant != request.user:
            return Response({'detail': 'You do not own this application.'}, status=status.HTTP_403_FORBIDDEN)

        if application.status not in (ApplicationStatus.DRAFT, ApplicationStatus.SUBMITTED):
            return Response(
                {'detail': f'Cannot request payment for an application with status "{application.status}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if application.status == ApplicationStatus.DRAFT:
                submit_application(application, actor=request.user)
            submit_payment_reference(application, actor=request.user)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            ApplicationDetailSerializer(application, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# DocumentResubmitView
# ---------------------------------------------------------------------------

class DocumentResubmitView(APIView):
    """
    POST /api/applications/<pk>/resubmit-documents/
    Applicant signals they have re-uploaded rejected documents.
    Transitions: awaiting_document_resubmission → under_naming_committee_review.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != Role.APPLICANT:
            return Response(
                {'detail': 'Only applicants can resubmit documents.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        application = _get_application_or_404(pk, request.user)
        if application is None:
            return Response({'detail': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)

        if application.applicant != request.user:
            return Response({'detail': 'You do not own this application.'}, status=status.HTTP_403_FORBIDDEN)

        if application.status != ApplicationStatus.AWAITING_DOCUMENT_RESUBMISSION:
            return Response(
                {'detail': 'Application is not awaiting document resubmission.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            application.transition_to(
                ApplicationStatus.UNDER_NAMING_COMMITTEE_REVIEW,
                actor=request.user,
                remarks='',
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        notify_applicant(
            application,
            notification_type=NotificationType.APPLICATION_STATUS_CHANGE,
            title='Documents Resubmitted',
            message=(
                f'Your documents for application {application.reference_number} '
                'have been resubmitted. The naming committee will review them shortly.'
            ),
        )

        return Response(
            ApplicationDetailSerializer(application, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# ApplicationRenewView
# ---------------------------------------------------------------------------

class ApplicationRenewView(APIView):
    """
    POST /api/applications/<pk>/renew/
    Applicant initiates renewal for a certificate_issued, expired, or renewed application.
    Transitions: → renewal_submitted → awaiting_renewal_payment + creates Payment record.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != Role.APPLICANT:
            return Response(
                {'detail': 'Only applicants can renew applications.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        application = _get_application_or_404(pk, request.user)
        if application is None:
            return Response({'detail': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)

        if application.applicant != request.user:
            return Response({'detail': 'You do not own this application.'}, status=status.HTTP_403_FORBIDDEN)

        renewable_statuses = [
            ApplicationStatus.CERTIFICATE_ISSUED,
            ApplicationStatus.EXPIRED,
            ApplicationStatus.RENEWED,
        ]
        if application.status not in renewable_statuses:
            return Response(
                {'detail': f'Cannot renew an application with status "{application.status}".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            application.transition_to(
                ApplicationStatus.RENEWAL_SUBMITTED,
                actor=request.user,
                remarks='',
            )
            application.transition_to(
                ApplicationStatus.AWAITING_RENEWAL_PAYMENT,
                actor=request.user,
                remarks='',
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        from decimal import Decimal as _Decimal
        from payments.models import Payment as _Payment, PaymentStage as _PS, PaymentStatus as _PStatus
        from payments.services import calculate_renewal_fee
        renewal_fee = calculate_renewal_fee(application.street_type_id)
        amount = renewal_fee['amount'] if renewal_fee else _Decimal('0.00')
        _Payment.objects.create(
            application=application,
            stage=_PS.RENEWAL,
            status=_PStatus.PENDING,
            amount_expected=amount,
        )

        notify_applicant(
            application,
            notification_type=NotificationType.APPLICATION_STATUS_CHANGE,
            title='Renewal Initiated',
            message=(
                f'Your renewal for application {application.reference_number} has been initiated. '
                'Please proceed to pay the renewal fee.'
            ),
        )

        return Response(
            ApplicationDetailSerializer(application, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# ApplicationStatusHistoryView
# ---------------------------------------------------------------------------

class ApplicationStatusHistoryView(generics.ListAPIView):
    """GET /api/applications/<pk>/history/ — returns all status history entries."""
    permission_classes = [IsAuthenticated]
    serializer_class = StatusHistorySerializer

    def get_queryset(self):
        pk = self.kwargs['pk']
        application = _get_application_or_404(pk, self.request.user)
        if application is None:
            from rest_framework.exceptions import NotFound
            raise NotFound('Application not found.')
        return StatusHistory.objects.filter(application=application).select_related('changed_by')


class DuplicateCheckView(APIView):
    """POST /applications/check-duplicate/ — check a proposed street name for duplicates."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .duplicate import check_duplicate
        name = (request.data.get('name') or '').strip()
        if not name:
            return Response({'detail': 'name is required.'}, status=status.HTTP_400_BAD_REQUEST)
        report = check_duplicate(
            name=name,
            locality=request.data.get('locality'),
            latitude=request.data.get('latitude'),
            longitude=request.data.get('longitude'),
        )
        return Response(report)


class AdminApplicationRegistryView(APIView):
    """GET /applications/registry/ — full applicant database for admins.

    Returns every application with applicant name, email, phone, locality,
    status, fees paid and payment references. Staff only.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        role = getattr(request.user, 'role', None)
        if role not in ('finance', 'naming_committee', 'committee_chairman'):
            return Response({'detail': 'Not available.'}, status=status.HTTP_403_FORBIDDEN)

        from payments.models import Payment, PaymentStatus
        qs = (Application.objects.select_related('applicant', 'street_type')
              .prefetch_related('payments').order_by('-created_at'))
        search = request.query_params.get('search', '').strip()
        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(proposed_street_name__icontains=search)
                | Q(applicant__email__icontains=search)
                | Q(applicant__first_name__icontains=search)
                | Q(applicant__last_name__icontains=search)
                | Q(reference_number__icontains=search)
            )
        rows = []
        for a in qs[:1000]:
            pays = list(a.payments.all())
            confirmed = [p for p in pays if p.status == PaymentStatus.CONFIRMED]
            rows.append({
                'id': str(a.id),
                'reference_number': a.reference_number or '',
                'proposed_street_name': a.proposed_street_name,
                'street_type': a.street_type.name if a.street_type else '',
                'status': a.status,
                'ward': a.get_ward_display(),
                'locality': a.locality or '',
                'applicant_name': f'{a.applicant.first_name} {a.applicant.last_name}'.strip() if a.applicant else '',
                'applicant_email': a.applicant.email if a.applicant else '',
                'applicant_phone': getattr(a.applicant, 'phone', '') if a.applicant else '',
                'created_at': a.created_at,
                'expires_at': a.expires_at,
                'total_paid': sum(float(p.amount_submitted or 0) for p in confirmed),
                'payment_refs': [
                    {'stage': p.stage, 'reference': p.payment_reference or '', 'status': p.status}
                    for p in pays
                ],
            })
        return Response({'count': len(rows), 'results': rows})


class RoyaltyExemptionView(APIView):
    """POST /applications/<pk>/royalty-exemption/ — Chairman only (#meeting).

    Grants/revokes royalty exemption. When exempt, the applicant pays ONLY the
    application fee; the Stage C (certificate) fee is waived.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if getattr(request.user, 'role', None) != 'committee_chairman':
            return Response({'detail': 'Only the Local Government Chairman can grant royalty exemption.'},
                            status=status.HTTP_403_FORBIDDEN)
        application = get_object_or_404(Application, pk=pk)
        application.is_royalty_exempt = bool(request.data.get('exempt', True))
        application.save(update_fields=['is_royalty_exempt', 'updated_at'])
        return Response({'is_royalty_exempt': application.is_royalty_exempt})


class SignboardPoleView(APIView):
    """PATCH /applications/<pk>/signboard/ — staff record signboard & pole numbers."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if getattr(request.user, 'role', None) not in ('finance', 'naming_committee', 'committee_chairman'):
            return Response({'detail': 'Staff only.'}, status=status.HTTP_403_FORBIDDEN)
        application = get_object_or_404(Application, pk=pk)
        application.signboard_number = request.data.get('signboard_number', application.signboard_number)
        application.pole_number = request.data.get('pole_number', application.pole_number)
        application.save(update_fields=['signboard_number', 'pole_number', 'updated_at'])
        return Response({'signboard_number': application.signboard_number,
                         'pole_number': application.pole_number})


class ChairmanAuditView(APIView):
    """GET /applications/audit/?from=YYYY-MM-DD&to=YYYY-MM-DD — LG Chairman audit (#7).

    Returns application counts and payment totals (by category) within a period.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if getattr(request.user, 'role', None) != 'committee_chairman':
            return Response({'detail': 'Local Government Chairman only.'}, status=status.HTTP_403_FORBIDDEN)
        import datetime as _dt
        from django.utils import timezone
        from django.db.models import Count, Sum
        from payments.models import Payment, PaymentStatus

        def parse(d, default):
            try:
                return _dt.datetime.strptime(d, '%Y-%m-%d').date()
            except (TypeError, ValueError):
                return default
        today = timezone.localdate()
        d_from = parse(request.query_params.get('from'), today.replace(day=1))
        d_to = parse(request.query_params.get('to'), today)
        start = timezone.make_aware(_dt.datetime.combine(d_from, _dt.time.min))
        end = timezone.make_aware(_dt.datetime.combine(d_to, _dt.time.max))

        # The Chairman can look at one kind of work at a time: new street names,
        # validations of existing streets, or renewals.
        from .revenue import (CATEGORIES, CATEGORY_LABELS, applications_in_category,
                              revenue_breakdown, revenue_by_stage)
        category = request.query_params.get('category') or ''
        category = category if category in CATEGORIES else ''

        apps = Application.objects.filter(created_at__range=(start, end), is_deleted=False)
        if category:
            apps = applications_in_category(apps, category)
        by_status = {row['status']: row['n'] for row in apps.values('status').annotate(n=Count('id'))}

        # Certificates ISSUED within the period (by the actual issuance date, not by
        # when the application was created) — anything issued outside the dates is ignored.
        from applications.models import StatusHistory
        issued_q = StatusHistory.objects.filter(
            to_status='certificate_issued', created_at__range=(start, end),
            application__is_deleted=False,
        )
        if category:
            issued_q = issued_q.filter(
                application__in=applications_in_category(
                    Application.objects.filter(is_deleted=False), category))
        certificates_issued = issued_q.values('application').distinct().count()

        breakdown = revenue_breakdown(start, end, category or None)

        return Response({
            'from': d_from, 'to': d_to,
            'category': category,
            'category_label': CATEGORY_LABELS.get(category, 'All categories'),
            'category_options': [{'value': c, 'label': CATEGORY_LABELS[c]} for c in CATEGORIES],
            'total_applications': apps.count(),
            'applications_by_status': by_status,
            'certificates_issued': certificates_issued,
            'revenue_by_category': breakdown['categories'],
            'payments_by_fee': revenue_by_stage(start, end),
            'total_revenue': breakdown['total'],
            'payments_confirmed_count': breakdown['count'],
        })


class ChairmanAuditReportView(APIView):
    """GET /applications/audit/report/?from=&to= — downloadable PDF audit report (#7)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if getattr(request.user, 'role', None) != 'committee_chairman':
            return Response({'detail': 'Local Government Chairman only.'}, status=status.HTTP_403_FORBIDDEN)
        import datetime as _dt, io, os
        from django.utils import timezone
        from django.http import FileResponse
        from django.db.models import Count, Sum
        from django.conf import settings
        from payments.models import Payment, PaymentStatus
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas

        def parse(d, default):
            try:
                return _dt.datetime.strptime(d, '%Y-%m-%d').date()
            except (TypeError, ValueError):
                return default
        today = timezone.localdate()
        d_from = parse(request.query_params.get('from'), today.replace(day=1))
        d_to = parse(request.query_params.get('to'), today)
        start = timezone.make_aware(_dt.datetime.combine(d_from, _dt.time.min))
        end = timezone.make_aware(_dt.datetime.combine(d_to, _dt.time.max))

        from .revenue import (CATEGORIES, CATEGORY_LABELS, applications_in_category,
                              revenue_breakdown)
        category = request.query_params.get('category') or ''
        category = category if category in CATEGORIES else ''

        apps = Application.objects.filter(created_at__range=(start, end), is_deleted=False)
        if category:
            apps = applications_in_category(apps, category)
        from applications.models import StatusHistory
        issued_q = StatusHistory.objects.filter(
            to_status='certificate_issued', created_at__range=(start, end),
            application__is_deleted=False,
        )
        if category:
            issued_q = issued_q.filter(application__in=applications_in_category(
                Application.objects.filter(is_deleted=False), category))
        certs_issued = issued_q.values('application').distinct().count()
        breakdown = revenue_breakdown(start, end, category or None)
        grand = breakdown['total']
        by_status = {row['status']: row['n'] for row in apps.values('status').annotate(n=Count('id'))}

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w, h = A4
        green = colors.HexColor('#1F7A4D'); dark = colors.HexColor('#0f172a'); grey = colors.HexColor('#64748b')
        logo = os.path.join(settings.BASE_DIR, 'config', 'data', 'lga_logo.png')
        if os.path.exists(logo):
            c.drawImage(logo, 22 * mm, h - 40 * mm, width=22 * mm, height=22 * mm, preserveAspectRatio=True, mask='auto')
        c.setFillColor(dark); c.setFont('Helvetica-Bold', 15)
        c.drawString(48 * mm, h - 24 * mm, 'IBEJU-LEKKI LOCAL GOVERNMENT AREA')
        c.setFillColor(green); c.setFont('Helvetica-Bold', 11)
        c.drawString(48 * mm, h - 30 * mm, 'Street Naming — Audit & Revenue Report')
        c.setFillColor(grey); c.setFont('Helvetica', 9)
        c.drawString(48 * mm, h - 35 * mm, f'Period: {d_from.strftime("%d %b %Y")} to {d_to.strftime("%d %b %Y")}')
        c.drawString(48 * mm, h - 39.5 * mm,
                     f'Category: {CATEGORY_LABELS.get(category, "All categories")}')
        c.setStrokeColor(green); c.setLineWidth(1.5); c.line(22 * mm, h - 44 * mm, w - 22 * mm, h - 44 * mm)

        y = h - 58 * mm
        def row(label, value, bold=False):
            nonlocal y
            c.setFillColor(grey); c.setFont('Helvetica', 10); c.drawString(26 * mm, y, label)
            c.setFillColor(dark); c.setFont('Helvetica-Bold' if bold else 'Helvetica', 10)
            c.drawRightString(w - 26 * mm, y, str(value)); y -= 8 * mm

        c.setFillColor(dark); c.setFont('Helvetica-Bold', 12); c.drawString(24 * mm, y, 'Summary'); y -= 9 * mm
        row('Total applications', apps.count())
        row('Certificates issued', certs_issued)
        row('Payments confirmed', breakdown['count'])
        row('Total revenue', f'NGN {grand:,.2f}', bold=True)
        y -= 4 * mm
        # What each kind of work brought in, and which fee inside it. With no
        # category chosen this is the whole answer to "where did the money come
        # from"; with one chosen it is that category on its own.
        c.setFillColor(dark); c.setFont('Helvetica-Bold', 12)
        c.drawString(24 * mm, y, 'Revenue by category'); y -= 9 * mm
        for cat, bucket in breakdown['categories'].items():
            row(f"{bucket['label']} ({bucket['count']})", f"NGN {bucket['total']:,.2f}", bold=True)
            for fee in bucket['fees'].values():
                c.setFillColor(grey); c.setFont('Helvetica', 9)
                c.drawString(32 * mm, y, f"— {fee['label']} ({fee['count']})")
                c.drawRightString(w - 26 * mm, y, f"NGN {fee['total']:,.2f}")
                y -= 6.5 * mm
            y -= 2 * mm
        y -= 4 * mm
        c.setFillColor(dark); c.setFont('Helvetica-Bold', 12); c.drawString(24 * mm, y, 'Applications by status'); y -= 9 * mm
        for stat, n in by_status.items():
            row(stat.replace('_', ' ').title(), n)

        c.setFillColor(grey); c.setFont('Helvetica', 8)
        c.drawString(24 * mm, 16 * mm, f'Generated {timezone.now().strftime("%d %b %Y %H:%M")} · Ibeju-Lekki LGA SNRMS')
        c.showPage(); c.save(); buf.seek(0)
        return FileResponse(buf, as_attachment=True,
                            filename=f'audit_{d_from}_{d_to}.pdf', content_type='application/pdf')


class ApplicationRepositoryView(APIView):
    """GET /applications/<pk>/repository/ — the complete document repository for an
    application, stored against the applicant. Aggregates everything submitted AND
    generated (uploaded documents, issued correspondence, receipts, the certificate
    and any legacy certificate) so it can be downloaded and re-downloaded anytime.
    Accessible to staff and to the owning applicant.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        application = get_object_or_404(Application, pk=pk)
        user = request.user
        is_staff_role = getattr(user, 'role', None) in ('finance', 'naming_committee', 'committee_chairman') or user.is_staff
        if not is_staff_role and application.applicant_id != user.id:
            return Response({'detail': 'Not permitted.'}, status=status.HTTP_403_FORBIDDEN)

        from snrms.media_access import signed_media_url

        def _url(f):
            # Short-lived signed link; public /media is closed in production.
            return signed_media_url(f, request)

        items = []
        # 1) Documents uploaded by the applicant, and 2) issued by the Council
        from documents.models import Document
        for d in Document.objects.filter(application=application, is_deleted=False).order_by('created_at'):
            issued = getattr(d, 'direction', 'submission') == 'issued'
            items.append({
                'category': 'Issued by Council' if issued else 'Submitted by applicant',
                'title': d.title or d.get_document_type_display(),
                'kind': d.document_type,
                'filename': d.original_filename or '',
                'download_url': _url(d.file),
                'date': d.created_at,
                'verified': d.is_verified,
            })
        # 3) The naming certificate — committee/LG chairman can always download;
        #    the applicant sees it only once the chairman releases it.
        if getattr(application, 'certificate_file', None):
            if is_staff_role or application.certificate_released:
                items.append({
                    'category': 'Certificate',
                    'title': 'Street Naming Certificate',
                    'kind': 'certificate',
                    'filename': '',
                    'download_url': _url(application.certificate_file),
                    'date': application.certificate_issued_at or application.updated_at,
                    'verified': True,
                    'released': application.certificate_released,
                })
        # 4) Legacy certificate submitted for validation
        if getattr(application, 'legacy_certificate', None):
            items.append({
                'category': 'Submitted by applicant',
                'title': 'Existing certificate (for validation)',
                'kind': 'legacy_certificate',
                'filename': '',
                'download_url': _url(application.legacy_certificate),
                'date': application.created_at,
                'verified': True,
            })
        # 5) Payment receipts (generated)
        from payments.models import Receipt
        for r in application.receipts.all().order_by('issued_at'):
            items.append({
                'category': 'Receipt',
                'title': f'Payment Receipt — {r.serial}',
                'kind': f'receipt_{r.stage}',
                'filename': f'{r.serial}.pdf',
                'download_url': _url(r.pdf),
                'serial': r.serial,
                'amount': float(r.amount or 0),
                'date': r.issued_at,
                'verified': True,
            })

        applicant = application.applicant
        return Response({
            'application': {
                'id': str(application.id),
                'reference_number': application.reference_number or '',
                'proposed_street_name': application.proposed_street_name,
                'status': application.status,
            },
            'applicant': {
                'name': (applicant.full_name if applicant else '') or (applicant.email if applicant else ''),
                'email': applicant.email if applicant else '',
            },
            'count': len(items),
            'items': items,
        })

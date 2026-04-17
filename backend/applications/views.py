from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Role
from notifications.models import NotificationType

from .models import Application, ApplicationStatus, StatusHistory
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
            qs = qs.filter(status=status_filter)

        return qs

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
        return super().create(request, *args, **kwargs)


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
                    remarks='Auto-forwarded to chairman after committee approval.',
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
                # Auto-advance: chairman approval → awaiting Stage C payment
                application.transition_to(
                    ApplicationStatus.AWAITING_STAGE_C_PAYMENT,
                    actor=request.user,
                    remarks='Auto-forwarded to Stage C payment after chairman approval.',
                )
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
    """POST /api/applications/<pk>/issue-certificate/ — finance only."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != Role.FINANCE:
            return Response(
                {'detail': 'Only finance staff can issue certificates.'},
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

        try:
            issue_certificate(application, actor=request.user)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

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

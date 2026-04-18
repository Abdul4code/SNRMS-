from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from applications.models import Application, ApplicationStatus
from accounts.models import Role

from .models import Document
from .serializers import DocumentSerializer, DocumentUploadSerializer


def _get_active_document_or_404(pk):
    try:
        return Document.objects.get(pk=pk, is_deleted=False)
    except Document.DoesNotExist:
        raise NotFound('Document not found.')


def _is_staff_role(user):
    return user.role in (
        Role.FINANCE,
        Role.NAMING_COMMITTEE,
        Role.COMMITTEE_CHAIRMAN,
    ) or user.is_staff


class DocumentListView(ListAPIView):
    """GET /documents/?application=<uuid>"""

    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        application_id = self.request.query_params.get('application')
        if not application_id:
            raise ValidationError({'application': 'This query parameter is required.'})

        try:
            application = Application.objects.get(pk=application_id)
        except Application.DoesNotExist:
            raise NotFound('Application not found.')

        user = self.request.user
        if not _is_staff_role(user) and application.applicant != user:
            raise PermissionDenied('You do not have permission to view these documents.')

        return Document.objects.filter(application=application, is_deleted=False)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class DocumentUploadView(CreateAPIView):
    """POST /documents/"""

    serializer_class = DocumentUploadSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        application_id = serializer.validated_data.get('application_id')

        try:
            application = Application.objects.get(pk=application_id)
        except Application.DoesNotExist:
            raise NotFound('Application not found.')

        user = self.request.user

        # Only the applicant who owns the application may upload
        if application.applicant != user:
            raise PermissionDenied(
                'You can only upload documents for your own applications.'
            )

        # Application must be in a status that allows document upload
        allowed_statuses = (
            ApplicationStatus.DRAFT,
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.AWAITING_DOCUMENT_RESUBMISSION,
        )
        if application.status not in allowed_statuses:
            raise ValidationError(
                'Documents can only be uploaded for applications in "draft", "submitted", or "awaiting document resubmission" status.'
            )

        # Soft-delete any existing rejected document of the same type so it no
        # longer appears in either the applicant or staff view.
        document_type = serializer.validated_data.get('document_type')
        Document.objects.filter(
            application=application,
            document_type=document_type,
            is_rejected=True,
            is_deleted=False,
        ).update(is_deleted=True)

        serializer.save()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        document = serializer.instance
        output = DocumentSerializer(document, context={'request': request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class DocumentDetailView(RetrieveDestroyAPIView):
    """GET /documents/<pk>/  and  DELETE /documents/<pk>/"""

    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        document = _get_active_document_or_404(self.kwargs['pk'])
        user = self.request.user
        if not _is_staff_role(user) and document.uploaded_by != user:
            raise PermissionDenied('You do not have permission to access this document.')
        return document

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_destroy(self, instance):
        # Soft delete — never remove from storage
        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])


class DocumentVerifyView(APIView):
    """POST /documents/<pk>/verify/"""

    permission_classes = [IsAuthenticated]

    VERIFY_ROLES = (
        Role.FINANCE,
        Role.NAMING_COMMITTEE,
        Role.COMMITTEE_CHAIRMAN,
    )

    def post(self, request, pk):
        user = request.user
        if user.role not in self.VERIFY_ROLES and not user.is_staff:
            raise PermissionDenied(
                'Only finance, committee, or chairman users may verify documents.'
            )

        document = _get_active_document_or_404(pk)

        is_verified = request.data.get('is_verified')
        verification_note = request.data.get('verification_note', '')

        if is_verified is None:
            raise ValidationError({'is_verified': 'This field is required.'})

        if not isinstance(is_verified, bool):
            # Accept string representations from form/JSON payloads
            if str(is_verified).lower() == 'true':
                is_verified = True
            elif str(is_verified).lower() == 'false':
                is_verified = False
            else:
                raise ValidationError({'is_verified': 'Must be a boolean value.'})

        document.is_verified = is_verified
        document.is_rejected = False
        document.verification_note = verification_note
        document.save(update_fields=['is_verified', 'is_rejected', 'verification_note'])

        serializer = DocumentSerializer(document, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class DocumentRejectView(APIView):
    """POST /documents/<pk>/reject/"""

    permission_classes = [IsAuthenticated]

    REJECT_ROLES = (
        Role.NAMING_COMMITTEE,
        Role.COMMITTEE_CHAIRMAN,
    )

    def post(self, request, pk):
        user = request.user
        if user.role not in self.REJECT_ROLES and not user.is_staff:
            raise PermissionDenied(
                'Only naming committee members or the chairman may reject documents.'
            )

        document = _get_active_document_or_404(pk)
        rejection_note = request.data.get('rejection_note', '').strip()

        if not rejection_note:
            raise ValidationError({'rejection_note': 'A rejection reason is required.'})

        document.is_rejected = True
        document.is_verified = False
        document.verification_note = rejection_note
        document.save(update_fields=['is_rejected', 'is_verified', 'verification_note'])

        application = document.application
        if application.status == ApplicationStatus.UNDER_NAMING_COMMITTEE_REVIEW:
            application.transition_to(
                ApplicationStatus.AWAITING_DOCUMENT_RESUBMISSION,
                actor=user,
                remarks=f'Document "{document.get_document_type_display()}" rejected: {rejection_note}',
            )

        serializer = DocumentSerializer(document, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

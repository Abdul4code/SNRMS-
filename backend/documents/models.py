import uuid
import os
from django.db import models
from django.conf import settings


class DocumentType(models.TextChoices):
    NIN_VERIFICATION_SLIP = 'nin_verification_slip', 'NIN Verification Slip'
    PASSPORT_PHOTOGRAPH = 'passport_photograph', 'Passport Photograph'
    ROYAL_FATHERS_RECOGNITION_LETTER = 'royal_fathers_recognition_letter', 'Royal Fathers Recognition Letter'
    SURVEY_PROPERTY_DOCUMENT = 'survey_property_document', 'Survey Property Document'
    CDA_RECOMMENDATION_LETTER = 'cda_recommendation_letter', 'CDA / Landlord Association Recommendation Letter'
    ADMIN_CORRESPONDENCE = 'admin_correspondence', 'Correspondence / Letter from the Council'


def document_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    return f'documents/{instance.application_id}/{instance.document_type}/{uuid.uuid4()}{ext}'


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.ForeignKey(
        'applications.Application', on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(max_length=50, choices=DocumentType.choices)
    file = models.FileField(upload_to=document_upload_path)
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text='Size in bytes')
    mime_type = models.CharField(max_length=100)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    is_verified = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    verification_note = models.TextField(blank=True)
    direction = models.CharField(max_length=20, default='submission',
                                 choices=[('submission', 'Applicant submission'),
                                          ('issued', 'Issued to applicant by Council')])
    title = models.CharField(max_length=200, blank=True, help_text='Label for Council-issued documents')
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.document_type} for {self.application_id}'

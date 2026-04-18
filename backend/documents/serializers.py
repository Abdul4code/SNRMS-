from rest_framework import serializers

from .models import Document

ALLOWED_MIME_TYPES = {
    'application/pdf',
    'image/jpeg',
    'image/png',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB in bytes


class DocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id',
            'application',
            'document_type',
            'file_url',
            'original_filename',
            'file_size',
            'mime_type',
            'uploaded_by',
            'is_verified',
            'is_rejected',
            'verification_note',
            'is_deleted',
            'created_at',
        ]
        read_only_fields = fields

    def get_file_url(self, instance):
        if not instance.file:
            return None
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(instance.file.url)
        return instance.file.url


class DocumentUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True)
    document_type = serializers.ChoiceField(
        choices=Document._meta.get_field('document_type').choices,
        required=True,
    )
    application_id = serializers.UUIDField(write_only=True, required=True)

    class Meta:
        model = Document
        fields = ['file', 'document_type', 'application_id']

    def validate_file(self, file):
        if file.size > MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f'File size must not exceed 10 MB. Uploaded file is '
                f'{file.size / (1024 * 1024):.2f} MB.'
            )
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise serializers.ValidationError(
                f'Unsupported file type "{file.content_type}". '
                f'Allowed types: PDF, JPEG, PNG, DOC, DOCX.'
            )
        return file

    def create(self, validated_data):
        file = validated_data['file']
        request = self.context['request']

        document = Document.objects.create(
            application_id=validated_data['application_id'],
            document_type=validated_data['document_type'],
            file=file,
            original_filename=file.name,
            file_size=file.size,
            mime_type=file.content_type,
            uploaded_by=request.user,
        )
        return document

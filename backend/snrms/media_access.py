"""Signed, expiring URLs for protected media (uploaded documents, certificates,
receipts).

Public /media serving is disabled in production so sensitive PII (NIN slips,
passports) is never reachable by URL alone. Instead, authenticated endpoints
(serializers, the application repository) hand out short-lived *signed* links
via `signed_media_url()`. `serve_signed_media()` validates the signature and
expiry, then streams the file. This mirrors how S3 presigned URLs work: only a
user who was authorised at generation time receives a working link, and the link
stops working after MAX_AGE.
"""
import os

from django.core import signing
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404

SALT = 'snrms.media.v1'
MAX_AGE_SECONDS = 60 * 60 * 2  # 2 hours


def signed_media_url(file, request):
    """Return an absolute, signed, expiring URL for a FileField value (or None)."""
    if not file:
        return None
    token = signing.dumps(file.name, salt=SALT)
    path = f'/media-download/?t={token}'
    return request.build_absolute_uri(path) if request is not None else path


def serve_signed_media(request):
    """Validate the signed token and stream the file. Public route, but useless
    without a valid, unexpired signature (which only authorised endpoints mint)."""
    token = request.GET.get('t', '')
    try:
        name = signing.loads(token, salt=SALT, max_age=MAX_AGE_SECONDS)
    except signing.SignatureExpired:
        raise Http404('This download link has expired. Reload the page for a fresh link.')
    except signing.BadSignature:
        raise Http404('Invalid download link.')

    if not default_storage.exists(name):
        raise Http404('File not found.')

    filename = os.path.basename(name)
    return FileResponse(
        default_storage.open(name, 'rb'),
        as_attachment=False,
        filename=filename,
    )

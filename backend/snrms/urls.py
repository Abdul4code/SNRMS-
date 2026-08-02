from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from .media_access import serve_signed_media

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/applications/', include('applications.urls')),
    path('api/documents/', include('documents.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/config/', include('config.urls')),
    path('api/audit/', include('audit.urls')),
    # Protected media: only reachable with a valid, unexpired signed token that
    # authenticated endpoints mint. Public /media is intentionally NOT served in
    # production, so uploaded PII cannot be fetched by URL alone.
    path('media-download/', serve_signed_media, name='media-download'),
]

# Raw /media is served only in local development (DEBUG=True) for convenience.
# In production it is closed; files are reached exclusively via signed links.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

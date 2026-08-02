from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve as serve_media

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/applications/', include('applications.urls')),
    path('api/documents/', include('documents.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/config/', include('config.urls')),
    path('api/audit/', include('audit.urls')),
]

# Serve uploaded media (documents, receipts, certificates) from the mounted
# volume. Django's static() helper only works when DEBUG=True; on Fly the app
# runs with DEBUG=False and there is no separate file server, so we serve media
# through this view in all environments.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve_media, {'document_root': settings.MEDIA_ROOT}),
]

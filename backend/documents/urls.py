from django.urls import path

from .views import (
    DocumentDetailView,
    DocumentListView,
    DocumentUploadView,
    DocumentVerifyView,
)

urlpatterns = [
    path('', DocumentListView.as_view(), name='document-list'),
    path('upload/', DocumentUploadView.as_view(), name='document-upload'),
    path('<uuid:pk>/', DocumentDetailView.as_view(), name='document-detail'),
    path('<uuid:pk>/verify/', DocumentVerifyView.as_view(), name='document-verify'),
]

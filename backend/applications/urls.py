from django.urls import path

from .views import (
    ApplicationDetailView,
    ApplicationListCreateView,
    ApplicationStatusHistoryView,
    ApplicationSubmitView,
    ApplicationWithdrawView,
    CertificateIssueView,
    ChairmanApprovalView,
    CommitteeReviewView,
)

app_name = 'applications'

urlpatterns = [
    # Collection
    path('', ApplicationListCreateView.as_view(), name='application-list-create'),

    # Single resource
    path('<uuid:pk>/', ApplicationDetailView.as_view(), name='application-detail'),

    # Status transitions — applicant actions
    path('<uuid:pk>/submit/', ApplicationSubmitView.as_view(), name='application-submit'),
    path('<uuid:pk>/withdraw/', ApplicationWithdrawView.as_view(), name='application-withdraw'),

    # Status transitions — staff actions
    path('<uuid:pk>/committee-review/', CommitteeReviewView.as_view(), name='application-committee-review'),
    path('<uuid:pk>/chairman-approval/', ChairmanApprovalView.as_view(), name='application-chairman-approval'),
    path('<uuid:pk>/issue-certificate/', CertificateIssueView.as_view(), name='application-issue-certificate'),

    # History
    path('<uuid:pk>/history/', ApplicationStatusHistoryView.as_view(), name='application-history'),
]

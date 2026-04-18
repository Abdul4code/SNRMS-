from django.urls import path

from .views import (
    ApplicationCompletionView,
    ApplicationDetailView,
    ApplicationListCreateView,
    ApplicationRenewView,
    ApplicationStatusHistoryView,
    ApplicationSubmitView,
    ApplicationWithdrawView,
    CertificateIssueView,
    ChairmanApprovalView,
    CommitteeReviewView,
    DocumentResubmitView,
    RequestPaymentView,
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

    # Applicant payment request (documents done → awaiting Stage A payment)
    path('<uuid:pk>/request-payment/', RequestPaymentView.as_view(), name='application-request-payment'),

    # Applicant resubmits documents after rejection
    path('<uuid:pk>/resubmit-documents/', DocumentResubmitView.as_view(), name='application-resubmit-documents'),

    # Applicant renews a certificate
    path('<uuid:pk>/renew/', ApplicationRenewView.as_view(), name='application-renew'),

    # Naming committee completion status (map uploaded / signpost installed)
    path('<uuid:pk>/completion/', ApplicationCompletionView.as_view(), name='application-completion'),

    # History
    path('<uuid:pk>/history/', ApplicationStatusHistoryView.as_view(), name='application-history'),
]

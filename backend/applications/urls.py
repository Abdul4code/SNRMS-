from applications.committee_views import (
    CommitteeMembersView, VerifyMemberView, MemberProfileView, CommitteeQuorumReviewView,
    SubmitMemberCommentView, ForwardRecommendationView, MarkSubmissionsViewedView,
)
from django.urls import path

from .views import (
    RoyaltyExemptionView,
    ChairmanAuditView,
    ChairmanAuditReportView,
    ApplicationRepositoryView,
    CertificateReleaseView,
    SignboardPoleView,
    DuplicateCheckView,
    AdminApplicationRegistryView,
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
    StreetAvailabilityView,
)

app_name = 'applications'

urlpatterns = [
    # Collection
    path('', ApplicationListCreateView.as_view(), name='application-list-create'),
    path('street-availability/', StreetAvailabilityView.as_view(), name='application-street-availability'),
    path('check-duplicate/', DuplicateCheckView.as_view(), name='application-check-duplicate'),
    path('committee/members/', CommitteeMembersView.as_view(), name='committee-members'),
    path('committee/verify-member/', VerifyMemberView.as_view(), name='committee-verify-member'),
    path('committee/profile/', MemberProfileView.as_view(), name='committee-profile'),
    path('committee/<uuid:pk>/review/', CommitteeQuorumReviewView.as_view(), name='committee-review'),
    path('committee/<uuid:pk>/comment/', SubmitMemberCommentView.as_view(), name='committee-comment'),
    path('committee/<uuid:pk>/mark-viewed/', MarkSubmissionsViewedView.as_view(), name='committee-mark-viewed'),
    path('committee/<uuid:pk>/forward/', ForwardRecommendationView.as_view(), name='committee-forward'),

    path('registry/', AdminApplicationRegistryView.as_view(), name='application-registry'),
    path('audit/', ChairmanAuditView.as_view(), name='application-audit'),
    path('audit/report/', ChairmanAuditReportView.as_view(), name='application-audit-report'),
    path('<uuid:pk>/repository/', ApplicationRepositoryView.as_view(), name='application-repository'),
    path('<uuid:pk>/certificate-release/', CertificateReleaseView.as_view(), name='certificate-release'),
    path('<uuid:pk>/royalty-exemption/', RoyaltyExemptionView.as_view(), name='application-royalty-exemption'),
    path('<uuid:pk>/signboard/', SignboardPoleView.as_view(), name='application-signboard'),

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

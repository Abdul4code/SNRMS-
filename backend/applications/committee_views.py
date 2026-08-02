"""Street Naming Committee — second-tier member workflow.

Flow:
  * The committee shares one login. A member then verifies as member 1-7 with a PIN
    (second tier), receiving a short-lived signed token.
  * Each member writes ONE private, signed comment to the LG Chairman per application.
    Members cannot see each other's comments; the committee chairman (member 1) can.
  * Quorum = the committee chairman PLUS at least 3 other members must have commented.
  * Only after quorum can the committee chairman forward the recommendation, adding a
    general comment to the applicant and an overall recommendation to the LG Chairman.
"""
from django.core import signing
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import (
    Application, ApplicationStatus, CommitteeMember, CommitteeMemberComment, CommitteeReview,
    CommitteeSubmissionReview,
)

TOKEN_SALT = 'committee-2fa'
TOKEN_MAX_AGE = 8 * 3600          # 8 hours
QUORUM_OTHERS = 3                  # chairman + 3 others


def _is_committee(user):
    return getattr(user, 'role', None) in ('naming_committee', 'committee_chairman')


def _member_from_token(request):
    token = (request.headers.get('X-Committee-Member')
             or request.data.get('member_token')
             or request.query_params.get('member_token'))
    if not token:
        return None
    try:
        data = signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)
    except signing.BadSignature:
        return None
    return CommitteeMember.objects.filter(pk=data.get('m'), is_active=True).first()


def _quorum_met(application):
    # The committee chairman's overall section activates only once at least 3 OTHER
    # (non-chairman) members have submitted their individual comments (#10a).
    nums = set(CommitteeMemberComment.objects.filter(application=application)
               .values_list('member__number', flat=True))
    return len([n for n in nums if n != 1]) >= QUORUM_OTHERS


class CommitteeMembersView(APIView):
    """GET /committee/members/ — list members for the second-tier picker (no PINs)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _is_committee(request.user):
            return Response({'detail': 'Committee only.'}, status=status.HTTP_403_FORBIDDEN)
        members = CommitteeMember.objects.filter(is_active=True)
        return Response([
            {'number': m.number, 'name': m.name, 'is_chairman': m.is_chairman}
            for m in members
        ])


class VerifyMemberView(APIView):
    """POST /committee/verify-member/ {number, pin} -> signed member token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not _is_committee(request.user):
            return Response({'detail': 'Committee only.'}, status=status.HTTP_403_FORBIDDEN)
        member = CommitteeMember.objects.filter(number=request.data.get('number'), is_active=True).first()
        if not member or not member.check_pin(str(request.data.get('pin', ''))):
            return Response({'detail': 'Invalid member number or PIN.'}, status=status.HTTP_401_UNAUTHORIZED)
        token = signing.dumps({'m': member.pk}, salt=TOKEN_SALT)
        return Response({
            'token': token,
            'member': {'number': member.number, 'name': member.name, 'is_chairman': member.is_chairman},
        })


class CommitteeQuorumReviewView(APIView):
    """GET /committee/applications/<pk>/review/ — review state for the current member."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        user = request.user
        is_committee = _is_committee(user)
        is_lg_chairman = getattr(user, 'role', None) == 'committee_chairman'
        if not is_committee and not is_lg_chairman:
            return Response({'detail': 'Not permitted.'}, status=status.HTTP_403_FORBIDDEN)
        application = get_object_or_404(Application, pk=pk)
        member = _member_from_token(request)
        comments = list(CommitteeMemberComment.objects.filter(application=application)
                        .select_related('member'))
        responded = {c.member.number for c in comments}
        members = CommitteeMember.objects.filter(is_active=True)

        # Who can see the *content* of individual comments?
        #  - the committee chairman (member 1, via token)
        #  - the LG Chairman (role committee_chairman) — comments are addressed to them
        can_see_all = (member and member.is_chairman) or is_lg_chairman

        def comment_row(c, full):
            row = {
                'member_number': c.member.number, 'member_name': c.member.name,
                'recommendation': c.recommendation, 'created_at': c.created_at,
            }
            if full:
                row['comment'] = c.comment
                row['signature'] = c.signature
            return row

        my_comment = None
        my_viewed = False
        if member:
            mine = next((c for c in comments if c.member_id == member.pk), None)
            if mine:
                my_comment = comment_row(mine, True)
            my_viewed = CommitteeSubmissionReview.objects.filter(
                application=application, member=member).exists()

        others_responded = len([n for n in responded if n != 1])
        review = getattr(application, 'committee_review', None)

        # Summary of members' decisions — for the committee chairman and LG Chairman.
        decision_summary = None
        if can_see_all:
            from collections import Counter as _C
            tally = _C(c.recommendation for c in comments)
            decision_summary = {
                'recommend': tally.get('recommend', 0),
                'reject': tally.get('reject', 0),
                'abstain': tally.get('abstain', 0),
                'total': len(comments),
                'members': [
                    {'member_number': c.member.number, 'member_name': c.member.name,
                     'recommendation': c.recommendation}
                    for c in comments
                ],
            }

        # Applicant's uploaded document for a validate/legacy application lives on the
        # application itself (not as a Document record), so surface it here too.
        legacy_certificate = None
        try:
            if application.legacy_certificate:
                legacy_certificate = application.legacy_certificate.url
        except Exception:  # noqa: BLE001
            legacy_certificate = None

        return Response({
            'application_status': application.status,
            'is_legacy': application.is_legacy,
            'legacy_certificate': legacy_certificate,
            'members': [
                {'number': m.number, 'name': m.name, 'is_chairman': m.is_chairman,
                 'responded': m.number in responded}
                for m in members
            ],
            'responded_count': len(responded),
            'others_responded': others_responded,
            'quorum_met': _quorum_met(application),
            'my_comment': my_comment,
            'my_viewed': my_viewed,
            'decision_summary': decision_summary,
            'all_comments': [comment_row(c, True) for c in comments] if can_see_all else None,
            'consolidated': ({
                'general_comment_to_applicant': review.general_comment_to_applicant,
                'overall_recommendation': review.overall_recommendation,
                'decision': review.decision,
                'forwarded_at': review.forwarded_at,
            } if review else None),
        })


class SubmitMemberCommentView(APIView):
    """POST /committee/applications/<pk>/comment/ — the current member's signed comment."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not _is_committee(request.user):
            return Response({'detail': 'Committee only.'}, status=status.HTTP_403_FORBIDDEN)
        member = _member_from_token(request)
        if not member:
            return Response({'detail': 'Please verify as a committee member first.'},
                            status=status.HTTP_401_UNAUTHORIZED)
        application = get_object_or_404(Application, pk=pk)
        # #11 — a member must have viewed the applicant's submissions before commenting.
        if not CommitteeSubmissionReview.objects.filter(application=application, member=member).exists():
            return Response(
                {'detail': 'You must open and review the applicant\'s submissions before commenting.'},
                status=status.HTTP_400_BAD_REQUEST)
        comment = (request.data.get('comment') or '').strip()
        signature = (request.data.get('signature') or '').strip()
        if not comment or not signature:
            return Response({'detail': 'Comment and signature are required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        rec = request.data.get('recommendation', 'recommend')
        obj, _ = CommitteeMemberComment.objects.update_or_create(
            application=application, member=member,
            defaults={'comment': comment, 'signature': signature, 'recommendation': rec},
        )
        return Response({'status': 'saved', 'quorum_met': _quorum_met(application)})


class MarkSubmissionsViewedView(APIView):
    """POST /committee/applications/<pk>/mark-viewed/ — member confirms they've seen submissions (#11)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not _is_committee(request.user):
            return Response({'detail': 'Committee only.'}, status=status.HTTP_403_FORBIDDEN)
        member = _member_from_token(request)
        if not member:
            return Response({'detail': 'Verify as a committee member first.'},
                            status=status.HTTP_401_UNAUTHORIZED)
        application = get_object_or_404(Application, pk=pk)
        CommitteeSubmissionReview.objects.get_or_create(application=application, member=member)
        return Response({'status': 'viewed'})


class ForwardRecommendationView(APIView):
    """POST /committee/applications/<pk>/forward/ — committee chairman forwards to LG Chairman."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        member = _member_from_token(request)
        if not member or not member.is_chairman:
            return Response({'detail': 'Only the committee chairman (member 1) can forward.'},
                            status=status.HTTP_403_FORBIDDEN)
        application = get_object_or_404(Application, pk=pk)
        if not _quorum_met(application):
            return Response(
                {'detail': 'Quorum not met — the committee chairman and at least 3 other '
                           'members must comment before forwarding.'},
                status=status.HTTP_400_BAD_REQUEST)
        general = (request.data.get('general_comment_to_applicant') or '').strip()
        overall = (request.data.get('overall_recommendation') or '').strip()
        decision = request.data.get('decision', 'recommend')
        review, _ = CommitteeReview.objects.update_or_create(
            application=application,
            defaults={'general_comment_to_applicant': general,
                      'overall_recommendation': overall,
                      'decision': decision, 'forwarded_at': timezone.now()},
        )
        # Advance the workflow, mirroring the existing committee-review transitions.
        try:
            if decision == 'recommend':
                application.transition_to(ApplicationStatus.APPROVED_BY_COMMITTEE,
                                          actor=request.user, remarks=overall[:200])
                application.transition_to(ApplicationStatus.AWAITING_CHAIRMAN_APPROVAL,
                                          actor=request.user,
                                          remarks='Forwarded to chairman after committee quorum.')
            else:
                application.transition_to(ApplicationStatus.REJECTED_BY_COMMITTEE,
                                          actor=request.user, remarks=overall[:200])
        except Exception:
            application.status = (ApplicationStatus.AWAITING_CHAIRMAN_APPROVAL
                                  if decision == 'recommend' else ApplicationStatus.REJECTED_BY_COMMITTEE)
            application.save(update_fields=['status'])
        # Notify applicant with the committee chairman's general comment.
        try:
            from notifications.emails import notify
            from notifications.models import NotificationType
            if general and application.applicant:
                notify(application.applicant,
                       'Update on your street naming application',
                       general, notification_type=NotificationType.APPLICATION_STATUS_CHANGE,
                       application=application)
        except Exception:
            pass
        return Response({'status': 'forwarded', 'forwarded_at': review.forwarded_at})

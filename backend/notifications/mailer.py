"""One place every outgoing email goes through.

Delivery is whatever EMAIL_BACKEND is configured as (SendGrid in production,
console in development) — this module only adds the bits every call site needs:
a consistent subject prefix, and a logged failure instead of a silent one.

Callers must never let a mail failure break the surrounding workflow, so
``send`` swallows exceptions and returns False rather than raising.
"""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)

SUBJECT_PREFIX = '[Ibeju-Lekki SNRMS] '


def send(subject, message, to, html_message=None, prefix=True):
    """Send one email. Returns True if the backend accepted it.

    ``fail_silently`` is deliberately not used: we want the exception so it can
    be logged with the provider's error body, which is the only way to debug a
    rejected SendGrid key or an unverified sender address.
    """
    recipients = [to] if isinstance(to, str) else [addr for addr in to if addr]
    if not recipients:
        return False

    full_subject = f'{SUBJECT_PREFIX}{subject}' if prefix else subject
    mail = EmailMultiAlternatives(
        subject=full_subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
    )
    if html_message:
        mail.attach_alternative(html_message, 'text/html')

    try:
        mail.send(fail_silently=False)
    except Exception:  # noqa: BLE001 - email must never break the workflow
        logger.exception('Email send failed: subject=%r to=%s', full_subject, recipients)
        return False

    logger.info('Email sent: subject=%r to=%s', full_subject, recipients)
    return True


def send_code(subject, intro, code, to, outro=''):
    """Send one of the 6-digit code emails (registration + password reset).

    Both flows want the same shape, so the wording lives here and the views just
    supply the subject line and the surrounding sentences.
    """
    lines = [intro, '', f'Your code is {code}. It expires in 15 minutes.', '']
    if outro:
        lines.append(outro)
    text = '\n'.join(lines)

    html = f"""\
<div style="font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
            max-width:520px;margin:0 auto;padding:24px;color:#0f172a">
  <p style="font-size:12px;letter-spacing:.08em;text-transform:uppercase;
            color:#047857;font-weight:700;margin:0 0 16px">
    Ibeju-Lekki Local Government Area
  </p>
  <p style="font-size:15px;line-height:1.6;margin:0 0 20px">{intro}</p>
  <p style="font-size:32px;font-weight:700;letter-spacing:.18em;
            background:#ecfdf5;border-radius:10px;padding:16px 0;
            text-align:center;margin:0 0 20px">{code}</p>
  <p style="font-size:14px;color:#475569;margin:0 0 8px">
    This code expires in 15 minutes.
  </p>
  {f'<p style="font-size:13px;color:#64748b;margin:16px 0 0">{outro}</p>' if outro else ''}
  <hr style="border:0;border-top:1px solid #e2e8f0;margin:24px 0">
  <p style="font-size:12px;color:#94a3b8;margin:0">
    Street Naming Registration &amp; Management System
  </p>
</div>"""
    return send(subject, text, to, html_message=html)

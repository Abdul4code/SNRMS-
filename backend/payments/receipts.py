"""Generate tamper-evident payment receipts (LGA logo + CT signature + QR verify).

Anti-forgery design:
  * Every receipt has a unique serial and a HMAC-SHA256 security code derived from
    the immutable receipt facts (serial, amount, reference, payer) and the server
    SECRET_KEY. The code cannot be produced without the secret.
  * A QR code encodes the public verification URL (serial + code). Scanning it hits
    the server, which recomputes the code and returns the ORIGINAL figures — so any
    alteration on a printed copy (e.g. a changed amount) is immediately exposed.
  * The CT signature lives only on the server and is embedded into verified PDFs; it
    is never served as a standalone file, so it can't be lifted to fake a receipt.
"""
import hashlib
import hmac
import io
import os

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone


def _security_code(serial, amount, reference, payer):
    msg = f'{serial}|{amount}|{reference}|{payer}'.encode()
    return hmac.new(settings.SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()[:16]


def verify_code(serial, amount, reference, payer, code):
    return hmac.compare_digest(_security_code(serial, amount, reference, payer), code or '')


def _next_serial():
    from .models import Receipt
    year = timezone.now().year
    n = Receipt.objects.filter(serial__startswith=f'ILL-RCP-{year}-').count() + 1
    return f'ILL-RCP-{year}-{n:06d}'


def generate_receipt(payment):
    """Create (or return existing) a Receipt with a rendered secure PDF."""
    from .models import Receipt, OfficialSignature
    existing = Receipt.objects.filter(payment=payment).first()
    if existing and existing.pdf:
        return existing

    application = payment.application
    applicant = application.applicant
    payer = f'{applicant.first_name} {applicant.last_name}'.strip() if applicant else 'Applicant'
    amount = payment.amount_submitted or payment.amount_expected
    reference = payment.payment_reference or ''
    serial = existing.serial if existing else _next_serial()
    code = _security_code(serial, amount, reference, payer)

    receipt = existing or Receipt(payment=payment, application=application)
    receipt.serial = serial
    receipt.payer_name = payer
    receipt.amount = amount
    receipt.stage = payment.stage
    receipt.reference = reference
    receipt.security_code = code
    receipt.save()

    pdf_bytes = _render_pdf(receipt, OfficialSignature.current())
    receipt.pdf.save(f'{serial}.pdf', ContentFile(pdf_bytes), save=True)
    return receipt


def _render_pdf(receipt, signature):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    import qrcode

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    green = colors.HexColor('#1F7A4D')
    dark = colors.HexColor('#0f172a')
    grey = colors.HexColor('#64748b')

    # Faint repeating watermark (security background).
    c.saveState()
    c.setFont('Helvetica-Bold', 26)
    c.setFillColor(colors.HexColor('#EEF3F0'))
    for yy in range(60, int(h), 120):
        for xx in range(-40, int(w), 220):
            c.drawString(xx, yy, 'IBEJU-LEKKI LGA')
    c.restoreState()

    # Logo
    logo = os.path.join(settings.BASE_DIR, 'config', 'data', 'lga_logo.png')
    if os.path.exists(logo):
        c.drawImage(logo, 22 * mm, h - 42 * mm, width=26 * mm, height=26 * mm,
                    preserveAspectRatio=True, mask='auto')
    # Header
    c.setFillColor(dark)
    c.setFont('Helvetica-Bold', 15)
    c.drawString(54 * mm, h - 25 * mm, 'IBEJU-LEKKI LOCAL GOVERNMENT AREA')
    c.setFillColor(green)
    c.setFont('Helvetica-Bold', 11)
    c.drawString(54 * mm, h - 31 * mm, 'Official Payment Receipt')
    c.setFillColor(grey)
    c.setFont('Helvetica', 8.5)
    c.drawString(54 * mm, h - 36 * mm, 'Street Naming & Registration Management System (SNRMS)')

    c.setStrokeColor(green); c.setLineWidth(1.5)
    c.line(22 * mm, h - 46 * mm, w - 22 * mm, h - 46 * mm)

    # Serial + date (top right)
    c.setFillColor(dark); c.setFont('Helvetica-Bold', 10)
    c.drawRightString(w - 22 * mm, h - 25 * mm, receipt.serial)
    c.setFillColor(grey); c.setFont('Helvetica', 8.5)
    c.drawRightString(w - 22 * mm, h - 30 * mm, receipt.issued_at.strftime('%d %B %Y, %H:%M'))

    STAGE_LABELS = {'stage_a': 'Application Fee (Stage A)', 'stage_c': 'Certificate Fee (Stage C)',
                    'renewal': 'Renewal Fee'}
    rows = [
        ('Received from', receipt.payer_name),
        ('Street name', receipt.application.proposed_street_name),
        ('Application ref.', receipt.application.reference_number or str(receipt.application.id)),
        ('Payment for', STAGE_LABELS.get(receipt.stage, receipt.stage)),
        ('Payment reference', receipt.reference or '—'),
    ]
    y = h - 60 * mm
    c.setFont('Helvetica', 10)
    for label, val in rows:
        c.setFillColor(grey); c.drawString(24 * mm, y, f'{label}:')
        c.setFillColor(dark); c.setFont('Helvetica-Bold', 10)
        c.drawString(70 * mm, y, str(val)[:70])
        c.setFont('Helvetica', 10)
        y -= 9 * mm

    # Amount box
    y -= 4 * mm
    c.setFillColor(colors.HexColor('#F0FAF5'))
    c.roundRect(24 * mm, y - 8 * mm, w - 48 * mm, 16 * mm, 3 * mm, fill=1, stroke=0)
    c.setFillColor(grey); c.setFont('Helvetica', 9)
    c.drawString(28 * mm, y + 2 * mm, 'AMOUNT PAID')
    c.setFillColor(green); c.setFont('Helvetica-Bold', 18)
    c.drawRightString(w - 28 * mm, y - 1 * mm, f'NGN {float(receipt.amount):,.2f}')

    # QR verification code
    verify_url = f"{getattr(settings, 'RECEIPT_VERIFY_URL', 'http://localhost:5173/verify-receipt')}/{receipt.serial}?code={receipt.security_code}"
    qr = qrcode.make(verify_url)
    qbuf = io.BytesIO(); qr.save(qbuf, format='PNG'); qbuf.seek(0)
    from reportlab.lib.utils import ImageReader
    c.drawImage(ImageReader(qbuf), 24 * mm, 30 * mm, width=30 * mm, height=30 * mm)
    c.setFillColor(grey); c.setFont('Helvetica', 7.5)
    c.drawString(24 * mm, 27 * mm, 'Scan to verify authenticity')
    c.setFont('Helvetica-Bold', 7.5); c.setFillColor(dark)
    c.drawString(24 * mm, 23 * mm, f'Security code: {receipt.security_code}')

    # CT signature (embedded) + name
    sig_y = 34 * mm
    if signature and signature.image and os.path.exists(signature.image.path):
        try:
            c.drawImage(signature.image.path, w - 74 * mm, sig_y + 6 * mm, width=40 * mm, height=16 * mm,
                        preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    c.setStrokeColor(dark); c.setLineWidth(0.5)
    c.line(w - 74 * mm, sig_y + 4 * mm, w - 26 * mm, sig_y + 4 * mm)
    c.setFillColor(dark); c.setFont('Helvetica-Bold', 9)
    name = signature.signatory_name if signature else 'Council Treasurer'
    title = signature.signatory_title if signature else 'Council Treasurer, Ibeju-Lekki LGA'
    c.drawCentredString(w - 50 * mm, sig_y, name)
    c.setFillColor(grey); c.setFont('Helvetica', 7.5)
    c.drawCentredString(w - 50 * mm, sig_y - 4 * mm, title)

    # Footer
    c.setFillColor(grey); c.setFont('Helvetica', 7)
    c.drawCentredString(w / 2, 14 * mm,
                        'This receipt is electronically generated and secured. Verify it at the URL in the QR code. '
                        'Any alteration voids it.')
    c.showPage(); c.save()
    return buf.getvalue()

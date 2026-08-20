"""Auto-generated Street Naming Certificate PDF."""
import io
import os
from django.conf import settings
from django.core.files.base import ContentFile


def generate_certificate_pdf(application):
    """Render a professional certificate PDF and store it on application.certificate_file.

    Returns the application. Safe to call repeatedly (regenerates the file).
    """
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    w, h = landscape(A4)
    c = canvas.Canvas(buf, pagesize=landscape(A4))

    # Everything is drawn inside this box. Text is shrunk (and wrapped, where it is
    # a sentence) to stay within it, so a long street name, a long locality or a
    # wide date can never run over the border the way "VALID UNTIL" used to.
    margin = 28 * mm
    content_l, content_r = margin, w - margin
    content_w = content_r - content_l

    def fitted(text, font, size, max_w, min_size=6):
        """Largest size at or below `size` that keeps `text` inside `max_w`."""
        while size > min_size and c.stringWidth(str(text), font, size) > max_w:
            size -= 0.25
        return size

    def centred(text, y, font, size, colour, max_w=None):
        max_w = content_w if max_w is None else max_w
        c.setFillColor(colour)
        c.setFont(font, fitted(text, font, size, max_w))
        c.drawCentredString(w / 2, y, str(text))

    green = colors.HexColor('#1F7A4D')
    dark = colors.HexColor('#0f172a')
    grey = colors.HexColor('#64748b')
    gold = colors.HexColor('#B7791F')

    # Border
    c.setStrokeColor(green); c.setLineWidth(3)
    c.rect(12 * mm, 12 * mm, w - 24 * mm, h - 24 * mm)
    c.setStrokeColor(gold); c.setLineWidth(1)
    c.rect(15 * mm, 15 * mm, w - 30 * mm, h - 30 * mm)

    # Logo
    logo = os.path.join(settings.BASE_DIR, 'config', 'data', 'lga_logo.png')
    if os.path.exists(logo):
        c.drawImage(logo, w / 2 - 15 * mm, h - 52 * mm, width=30 * mm, height=30 * mm,
                    preserveAspectRatio=True, mask='auto')

    centred('IBEJU-LEKKI LOCAL GOVERNMENT AREA', h - 62 * mm, 'Helvetica-Bold', 20, dark)
    centred('CERTIFICATE OF STREET NAME REGISTRATION', h - 70 * mm, 'Helvetica-Bold', 14, green)
    centred('This is to certify that the street known and addressed as',
            h - 84 * mm, 'Helvetica', 11, grey)

    st = application.street_type.name if application.street_type else 'Street'
    name = application.proposed_street_name
    if st and st.lower() not in name.lower():
        name = f'{name} {st}'
    centred(name, h - 98 * mm, 'Helvetica-BoldOblique', 24, gold)

    ward = application.get_ward_display() if hasattr(application, 'get_ward_display') else (application.ward or '')
    locality = application.locality or ''
    where = ', '.join([x for x in [locality, ward] if x])
    holder = ''
    if application.applicant:
        holder = application.applicant.full_name or application.applicant.email
    # One sentence, wrapped rather than shrunk — a long locality should push onto a
    # second line instead of turning the whole line into small print.
    from reportlab.lib.utils import simpleSplit
    sentence = (f'situate at {where}, has been duly registered in the official street '
                f'register in the name of {holder}.')
    lines = simpleSplit(sentence, 'Helvetica', 12, content_w)
    y_line = h - 110 * mm
    for line in lines[:3]:
        centred(line, y_line, 'Helvetica', 12, dark)
        y_line -= 8 * mm

    # Details row — five evenly spaced columns across the content box. The last one
    # is right-aligned to the right margin, which is what keeps "VALID UNTIL" (the
    # widest label, hard against the edge) inside the border.
    y = 55 * mm
    issued = application.certificate_issued_at.strftime('%d %b %Y') if application.certificate_issued_at else '—'
    expires = application.expires_at.strftime('%d %b %Y') if application.expires_at else '—'
    details = [
        ('CERTIFICATE NO.', application.certificate_number),
        ('SIGNBOARD NO.', application.signboard_number),
        ('POLE NO.', application.pole_number),
        ('ISSUED', issued),
        ('VALID UNTIL', expires),
    ]
    col_w = content_w / len(details)
    for i, (label, value) in enumerate(details):
        value = str(value or '—')
        last = i == len(details) - 1
        label_size = fitted(label, 'Helvetica', 8, col_w)
        value_size = fitted(value, 'Helvetica-Bold', 10, col_w)
        if last:
            # Anchor the final column on the right margin.
            c.setFillColor(grey); c.setFont('Helvetica', label_size)
            c.drawRightString(content_r, y + 5 * mm, label)
            c.setFillColor(dark); c.setFont('Helvetica-Bold', value_size)
            c.drawRightString(content_r, y, value)
        else:
            x = content_l + i * col_w
            c.setFillColor(grey); c.setFont('Helvetica', label_size)
            c.drawString(x, y + 5 * mm, label)
            c.setFillColor(dark); c.setFont('Helvetica-Bold', value_size)
            c.drawString(x, y, value)

    # Chairman's uploaded e-signature, embedded above the signature line.
    try:
        from payments.models import OfficialSignature
        sig = OfficialSignature.current()
        if sig and sig.image and os.path.exists(sig.image.path):
            c.drawImage(sig.image.path, w - 85 * mm, 33 * mm, width=40 * mm, height=16 * mm,
                        preserveAspectRatio=True, mask='auto')
    except Exception:
        pass

    # Signature line
    c.setStrokeColor(dark); c.setLineWidth(0.7)
    c.line(w - 95 * mm, 32 * mm, w - 35 * mm, 32 * mm)
    c.setFillColor(grey); c.setFont('Helvetica', 9)
    c.drawCentredString(w - 65 * mm, 27 * mm, 'Chairman, Ibeju-Lekki Local Government')

    centred('This certificate is issued by Ibeju-Lekki LGA and remains the property of the Council.',
            18 * mm, 'Helvetica-Oblique', 7, grey)

    c.showPage(); c.save(); buf.seek(0)
    fname = f'certificate_{application.certificate_number or application.id}.pdf'
    application.certificate_file.save(fname, ContentFile(buf.read()), save=True)
    return application

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

    c.setFillColor(dark); c.setFont('Helvetica-Bold', 20)
    c.drawCentredString(w / 2, h - 62 * mm, 'IBEJU-LEKKI LOCAL GOVERNMENT AREA')
    c.setFillColor(green); c.setFont('Helvetica-Bold', 14)
    c.drawCentredString(w / 2, h - 70 * mm, 'CERTIFICATE OF STREET NAME REGISTRATION')

    c.setFillColor(grey); c.setFont('Helvetica', 11)
    c.drawCentredString(w / 2, h - 84 * mm, 'This is to certify that the street known and addressed as')

    st = application.street_type.name if application.street_type else 'Street'
    name = application.proposed_street_name
    if st and st.lower() not in name.lower():
        name = f'{name} {st}'
    c.setFillColor(gold); c.setFont('Helvetica-BoldOblique', 24)
    c.drawCentredString(w / 2, h - 98 * mm, name)

    ward = application.get_ward_display() if hasattr(application, 'get_ward_display') else (application.ward or '')
    locality = application.locality or ''
    where = ', '.join([x for x in [locality, ward] if x])
    c.setFillColor(dark); c.setFont('Helvetica', 12)
    c.drawCentredString(w / 2, h - 110 * mm,
                        f'situate at {where}, has been duly registered in the official street register')
    holder = ''
    if application.applicant:
        holder = application.applicant.full_name or application.applicant.email
    c.drawCentredString(w / 2, h - 118 * mm, f'in the name of {holder}.')

    # Details row
    y = 55 * mm
    c.setFillColor(grey); c.setFont('Helvetica', 9)
    c.setFillColor(dark); c.setFont('Helvetica-Bold', 10)
    left = 35 * mm
    def field(label, value, x):
        c.setFillColor(grey); c.setFont('Helvetica', 8); c.drawString(x, y + 5 * mm, label)
        c.setFillColor(dark); c.setFont('Helvetica-Bold', 10); c.drawString(x, y, str(value or '—'))
    field('CERTIFICATE NO.', application.certificate_number, left)
    field('SIGNBOARD NO.', application.signboard_number, left + 70 * mm)
    field('POLE NO.', application.pole_number, left + 130 * mm)
    issued = application.certificate_issued_at.strftime('%d %b %Y') if application.certificate_issued_at else '—'
    expires = application.expires_at.strftime('%d %b %Y') if application.expires_at else '—'
    field('ISSUED', issued, left + 180 * mm)
    field('VALID UNTIL', expires, left + 235 * mm)

    # Signature line
    c.setStrokeColor(dark); c.setLineWidth(0.7)
    c.line(w - 95 * mm, 32 * mm, w - 35 * mm, 32 * mm)
    c.setFillColor(grey); c.setFont('Helvetica', 9)
    c.drawCentredString(w - 65 * mm, 27 * mm, 'Chairman, Street Naming Committee')

    c.setFillColor(grey); c.setFont('Helvetica-Oblique', 7)
    c.drawCentredString(w / 2, 18 * mm,
                        'This certificate is issued by Ibeju-Lekki LGA and remains the property of the Council.')

    c.showPage(); c.save(); buf.seek(0)
    fname = f'certificate_{application.certificate_number or application.id}.pdf'
    application.certificate_file.save(fname, ContentFile(buf.read()), save=True)
    return application

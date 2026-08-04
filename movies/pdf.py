import io
import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_ticket_pdf(bookings):
    if not isinstance(bookings, (list, tuple)):
        bookings = [bookings]

    primary = bookings[0]
    seat_numbers = ", ".join([b.seat.seat_number for b in bookings])
    num_seats = len(bookings)
    total_price = primary.movie.price * num_seats

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    show_date_str = primary.show_date.strftime('%A, %B %d, %Y') if primary.show_date else primary.theater.time.strftime('%A, %B %d, %Y')
    show_time_str = primary.show_time or primary.theater.time.strftime('%I:%M %p')
    showtime_display = f"{show_date_str} at {show_time_str}"

    qr_data = (
        f"BOOKING ID: {primary.booking_id}\n"
        f"MOVIE: {primary.movie.name}\n"
        f"THEATER: {primary.theater.name} ({primary.theater.city})\n"
        f"SCREEN: {primary.theater.screen}\n"
        f"SHOWTIME: {showtime_display}\n"
        f"SEATS: {seat_numbers} ({num_seats} Tickets)\n"
        f"TOTAL PAID: Rs.{total_price}\n"
        f"PAYMENT REF: {primary.payment_reference}\n"
        f"STATUS: VERIFIED"
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#1E3A8A", back_color="white")
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)

    styles = getSampleStyleSheet()
    
    brand_style = ParagraphStyle(
        'BrandStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1E3A8A'),
        alignment=0
    )

    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#2563EB'),
        alignment=0
    )

    movie_title_style = ParagraphStyle(
        'MovieTitleStyle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#111827')
    )

    label_style = ParagraphStyle(
        'LabelStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#6B7280')
    )

    val_style = ParagraphStyle(
        'ValStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#111827')
    )

    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#9CA3AF'),
        alignment=1
    )

    elements = []

    header_table_data = [
        [
            Paragraph("BookMySeat", brand_style),
            Paragraph(f"OFFICIAL E-TICKET<br/><font size=8 color='#6B7280'>CONFIRMED BOOKING ({num_seats} TICKET{'S' if num_seats>1 else ''})</font>", ParagraphStyle('HRight', parent=subtitle_style, alignment=2))
        ]
    ]
    header_table = Table(header_table_data, colWidths=[270, 270])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2563EB'), spaceAfter=15))

    details_table_data = [
        [
            Paragraph("Booking ID:", label_style),
            Paragraph(f"<b>{primary.booking_id}</b>", val_style),
            Paragraph("Booked By:", label_style),
            Paragraph(f"{primary.user.username} ({primary.user.email})", val_style),
        ],
        [
            Paragraph("Payment Ref:", label_style),
            Paragraph(f"{primary.payment_reference}", val_style),
            Paragraph("Booking Date:", label_style),
            Paragraph(f"{primary.booked_at.strftime('%b %d, %Y %I:%M %p')}", val_style),
        ]
    ]
    details_table = Table(details_table_data, colWidths=[80, 180, 80, 200])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EFF6FF')),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#BFDBFE')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DBEAFE')),
    ]))
    elements.append(details_table)
    elements.append(Spacer(1, 15))

    movie_info = [
        [Paragraph(f"{primary.movie.name}", movie_title_style)],
        [Paragraph(f"Genre: {primary.movie.get_genre_display()} | Language: {primary.movie.get_language_display()} | Rating: ★ {primary.movie.rating}", val_style)],
        [Spacer(1, 10)],
        [Paragraph("THEATER & SHOW DETAILS", label_style)],
        [Paragraph(f"<b>Theater:</b> {primary.theater.name}, {primary.theater.get_city_display()}", val_style)],
        [Paragraph(f"<b>Screen:</b> {primary.theater.screen}", val_style)],
        [Paragraph(f"<b>Showtime:</b> {showtime_display}", val_style)],
        [Paragraph(f"<b>Booked Seats:</b> <font color='#2563EB' size=12><b>{seat_numbers}</b></font> ({num_seats} Seat{'s' if num_seats>1 else ''})", val_style)],
        [Paragraph(f"<b>Total Price:</b> ₹{total_price} <font size=8 color='#6B7280'>(₹{primary.movie.price} x {num_seats})</font>", val_style)],
    ]

    movie_table = Table(movie_info, colWidths=[360])
    movie_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 2),
    ]))

    qr_image = Image(qr_buffer, width=150, height=150)

    ticket_card_data = [
        [movie_table, qr_image]
    ]
    ticket_card = Table(ticket_card_data, colWidths=[370, 170])
    ticket_card.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FAFAFA')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
        ('PADDING', (0, 0), (-1, -1), 12),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
    ]))
    elements.append(ticket_card)

    elements.append(Spacer(1, 25))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E5E7EB'), spaceAfter=10))

    elements.append(Paragraph(
        "Important Instructions:<br/>"
        "1. Please display this e-ticket and the QR code on your mobile device at the theater entrance.<br/>"
        "2. Rights of admission reserved by theater management. Tickets are non-refundable and non-transferable.<br/>"
        "3. Enjoy your movie! Thank you for choosing BookMySeat.",
        footer_style
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

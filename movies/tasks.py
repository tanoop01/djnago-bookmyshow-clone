from celery import shared_task
from django.core.mail import EmailMessage
from django.conf import settings
from .models import Booking
from .pdf import generate_ticket_pdf


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def send_ticket_email_task(self, booking_ids):
    if not isinstance(booking_ids, (list, tuple)):
        booking_ids = [booking_ids]

    bookings = list(
        Booking.objects.filter(id__in=booking_ids)
        .select_related('user', 'movie', 'theater', 'seat')
        .order_by('id')
    )
    if not bookings:
        return False

    primary = bookings[0]
    recipient_email = primary.user.email
    if not recipient_email:
        return False

    seat_numbers = ", ".join([b.seat.seat_number for b in bookings])
    num_seats = len(bookings)
    total_price = primary.movie.price * num_seats

    pdf_content = generate_ticket_pdf(bookings)

    show_date_str = primary.show_date.strftime('%A, %B %d, %Y') if primary.show_date else primary.theater.time.strftime('%A, %B %d, %Y')
    show_time_str = primary.show_time or primary.theater.time.strftime('%I:%M %p')
    showtime_display = f"{show_date_str} at {show_time_str}"

    ticket_text = f"{num_seats} Ticket{'s' if num_seats > 1 else ''}"
    subject = f"Booking Confirmed! {ticket_text} for {primary.movie.name} ({primary.booking_id})"
    body = (
        f"Hi {primary.user.username},\n\n"
        f"Your booking for '{primary.movie.name}' is confirmed!\n\n"
        f"Booking ID: {primary.booking_id}\n"
        f"Movie: {primary.movie.name}\n"
        f"Theater: {primary.theater.name} ({primary.theater.get_city_display()})\n"
        f"Screen: {primary.theater.screen}\n"
        f"Showtime: {showtime_display}\n"
        f"Booked Seats: {seat_numbers} ({ticket_text})\n"
        f"Total Paid: Rs.{total_price}\n"
        f"Payment Ref: {primary.payment_reference}\n\n"
        f"Your consolidated PDF e-ticket with QR code verification is attached to this email.\n\n"
        f"Thank you for choosing BookMySeat!"
    )

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bookmyseat.com'),
        to=[recipient_email]
    )
    email.attach(f"Ticket_{primary.booking_id}.pdf", pdf_content, 'application/pdf')
    email.send(fail_silently=False)
    return True

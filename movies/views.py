import csv
import threading
import uuid
import hmac
import hashlib
import json
from datetime import time as dt_time, datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Count, Q, Avg, Sum, F, FloatField, ExpressionWrapper, Value
from django.db.models.functions import ExtractHour, TruncDay, Coalesce
from django.core.paginator import Paginator
from django.utils import timezone
from django.conf import settings

import razorpay

from .models import Movie, MoviePoster, Theater, Seat, Booking, Payment, Review, MovieView, Event, EventBooking
from .utils import get_recommendations
from .pdf import generate_ticket_pdf
from .tasks import send_ticket_email_task


SORT_CHOICES = [
    ('popularity', 'Most Popular'),
    ('newest',     'Newest First'),
    ('rating',     'Highest Rated'),
    ('price_asc',  'Price: Low to High'),
    ('price_desc', 'Price: High to Low'),
]

TIMING_RANGES = {
    'morning':   (dt_time(6,  0), dt_time(11, 59)),
    'afternoon': (dt_time(12, 0), dt_time(16, 59)),
    'evening':   (dt_time(17, 0), dt_time(20, 59)),
    'night':     (dt_time(21, 0), dt_time(23, 59)),
}


def get_razorpay_client():
    key_id = getattr(settings, 'RAZORPAY_KEY_ID', '')
    key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
    if key_id and key_secret and not key_id.startswith('rzp_test_bookmyseat'):
        try:
            return razorpay.Client(auth=(key_id, key_secret))
        except Exception as e:
            print("Razorpay client init error:", e)
            return None
    return None


def check_review_eligibility(user, movie):
    if not user.is_authenticated:
        return False, False, None, "Please log in to submit a review."

    user_bookings = Booking.objects.filter(user=user, movie=movie, status='CONFIRMED').select_related('theater')
    if not user_bookings.exists():
        return False, False, None, "You must have a confirmed ticket booking for this movie to write a review."

    now = timezone.now()
    duration = timedelta(minutes=movie.duration_mins or 120)

    watched_booking = None
    upcoming_booking = None
    earliest_end_time = None

    for booking in user_bookings:
        show_d = booking.show_date or booking.theater.time.date()
        show_t = None
        if booking.show_time:
            try:
                show_t = datetime.strptime(booking.show_time, '%I:%M %p').time()
            except ValueError:
                pass
        if not show_t:
            show_t = booking.theater.time.time()

        show_start = datetime.combine(show_d, show_t)
        if timezone.is_naive(show_start):
            show_start = timezone.make_aware(show_start)

        show_end = show_start + duration

        if now >= show_end:
            watched_booking = booking
            break
        else:
            if earliest_end_time is None or show_end < earliest_end_time:
                earliest_end_time = show_end
                upcoming_booking = booking

    if watched_booking:
        return True, True, watched_booking, "You are eligible to review this movie."
    else:
        end_time_str = earliest_end_time.strftime("%b %d, %Y at %I:%M %p") if earliest_end_time else "the show ends"
        msg = f"You have booked a ticket! You will be able to submit your review after your show completes at {end_time_str}."
        return True, False, upcoming_booking, msg


def async_email_dispatch(booking_ids):
    def _worker():
        try:
            send_ticket_email_task(booking_ids)
        except Exception as e:
            print("Background email error:", e)
    threading.Thread(target=_worker, daemon=True).start()


def set_city(request):
    try:
        if request.method == 'POST':
            city = request.POST.get('city', '').lower()
            if city:
                request.session['user_city'] = city
        elif request.method == 'GET':
            city = request.GET.get('city', '').lower()
            if city:
                request.session['user_city'] = city
    except Exception:
        pass
    next_url = request.META.get('HTTP_REFERER', '/')
    return redirect(next_url)


def movie_list(request):
    queryset = Movie.objects.all()

    user_city = request.session.get('user_city')
    search_query = request.GET.get('search', '').strip()
    genre        = request.GET.get('genre', '')
    language     = request.GET.get('language', '')
    city         = request.GET.get('city', user_city or '')
    theater_id   = request.GET.get('theater', '')
    min_rating   = request.GET.get('min_rating', '')
    release_from = request.GET.get('release_from', '')
    release_to   = request.GET.get('release_to', '')
    show_timing  = request.GET.get('show_timing', '')
    sort_by      = request.GET.get('sort', 'popularity')

    needs_distinct = False
    active_filters = {}

    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) |
            Q(cast__icontains=search_query) |
            Q(description__icontains=search_query)
        )
        active_filters['search'] = search_query

    if genre:
        queryset = queryset.filter(genre=genre)
        active_filters['genre'] = dict(Movie.GENRE_CHOICES).get(genre, genre)

    if language:
        queryset = queryset.filter(language=language)
        active_filters['language'] = dict(Movie.LANGUAGE_CHOICES).get(language, language)

    if city:
        queryset = queryset.filter(theaters__city=city)
        needs_distinct = True
        active_filters['city'] = dict(Theater.CITY_CHOICES).get(city, city)

    if theater_id:
        try:
            t_obj = Theater.objects.get(id=theater_id)
            queryset = queryset.filter(theaters=t_obj)
            needs_distinct = True
            active_filters['theater'] = t_obj.name
        except Theater.DoesNotExist:
            pass

    if min_rating:
        try:
            rating_val = float(min_rating)
            if rating_val > 0:
                queryset = queryset.filter(rating__gte=rating_val)
                active_filters['min_rating'] = f'{min_rating}★ & above'
        except ValueError:
            pass

    if release_from:
        queryset = queryset.filter(release_date__gte=release_from)
        active_filters['release_from'] = f'From {release_from}'

    if release_to:
        queryset = queryset.filter(release_date__lte=release_to)
        active_filters['release_to'] = f'Until {release_to}'

    if show_timing and show_timing in TIMING_RANGES:
        start_t, end_t = TIMING_RANGES[show_timing]
        queryset = queryset.filter(theaters__time__time__range=(start_t, end_t))
        needs_distinct = True
        active_filters['show_timing'] = show_timing.capitalize()

    if needs_distinct:
        queryset = queryset.distinct()

    if sort_by == 'newest':
        queryset = queryset.order_by('-release_date')
    elif sort_by == 'rating':
        queryset = queryset.order_by('-rating')
    elif sort_by == 'price_asc':
        queryset = queryset.order_by('price')
    elif sort_by == 'price_desc':
        queryset = queryset.order_by('-price')
    else:
        queryset = queryset.annotate(
            booking_count=Count('booking', filter=Q(booking__status='CONFIRMED'), distinct=True)
        ).order_by('-booking_count', '-rating')

    movie_count = queryset.count()

    paginator   = Paginator(queryset, 9)
    page_number = request.GET.get('page', 1)
    page_obj    = paginator.get_page(page_number)
    page_range  = paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1)

    query_params = request.GET.copy()
    query_params.pop('page', None)

    context = {
        'movies':           page_obj,
        'movie_count':      movie_count,
        'page_obj':         page_obj,
        'page_range':       page_range,
        'genre_choices':    Movie.GENRE_CHOICES,
        'language_choices': Movie.LANGUAGE_CHOICES,
        'city_choices':     Theater.CITY_CHOICES,
        'theaters_qs':      Theater.objects.values('id', 'name').distinct(),
        'recommendations':  get_recommendations(request),
        'active_filters':   active_filters,
        'search_query':     search_query,
        'selected_genre':   genre,
        'selected_language': language,
        'selected_city':    city,
        'selected_theater': theater_id,
        'selected_sort':    sort_by,
        'min_rating':       min_rating,
        'release_from':     release_from,
        'release_to':       release_to,
        'show_timing':      show_timing,
        'sort_choices':     SORT_CHOICES,
        'query_params':     query_params.urlencode(),
    }
    return render(request, 'movies/movie_list.html', context)


def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    posters = movie.posters.all()

    has_booked, can_review, target_booking, review_msg = check_review_eligibility(request.user, movie)
    user_review = None
    try:
        if request.user.is_authenticated:
            user_review = Review.objects.filter(user=request.user, movie=movie).first()
            MovieView.objects.create(user=request.user, movie=movie)
        else:
            s_key = getattr(request.session, 'session_key', None)
            if s_key:
                MovieView.objects.create(session_key=s_key, movie=movie)
    except Exception:
        pass

    reviews = movie.reviews.filter(is_reported=False).order_by('-created_at')
    total_reviews = reviews.count()

    similar_movies = (
        Movie.objects.filter(Q(genre=movie.genre) | Q(language=movie.language))
        .exclude(id=movie.id)
        .distinct()[:4]
    )

    trending_movies = get_recommendations(request, limit=4)
    recent_movies = Movie.objects.exclude(id=movie.id).order_by('-release_date')[:4]

    context = {
        'movie': movie,
        'posters': posters,
        'has_booked': has_booked,
        'can_review': can_review,
        'target_booking': target_booking,
        'review_msg': review_msg,
        'user_review': user_review,
        'reviews': reviews,
        'total_reviews': total_reviews,
        'similar_movies': similar_movies,
        'trending_movies': trending_movies,
        'recent_movies': recent_movies,
    }
    return render(request, 'movies/movie_detail.html', context)


@login_required(login_url='/login/')
def add_or_edit_review(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    has_booked, can_review, target_booking, review_msg = check_review_eligibility(request.user, movie)

    if not can_review:
        messages.warning(request, review_msg)
        return redirect('movie_detail', movie_id=movie.id)

    if request.method == 'POST':
        rating_val = int(request.POST.get('rating', 10))
        comment = request.POST.get('comment', '').strip()

        if comment:
            review, created = Review.objects.update_or_create(
                user=request.user,
                movie=movie,
                defaults={
                    'rating': max(1, min(10, rating_val)),
                    'comment': comment,
                    'is_verified_viewer': True,
                    'is_reported': False,
                }
            )
            messages.success(request, "Your review has been submitted successfully!" if created else "Your review has been updated.")

    return redirect('movie_detail', movie_id=movie.id)


@login_required(login_url='/login/')
def report_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.method == 'POST':
        reason = request.POST.get('reason', 'Inappropriate content reported by user').strip()
        review.is_reported = True
        review.report_reason = reason
        review.save()
        messages.warning(request, "Review has been reported to administrators for moderation.")
    return redirect('movie_detail', movie_id=review.movie.id)


def theater_list(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    user_city = request.session.get('user_city')

    theaters = Theater.objects.filter(movie=movie)
    if user_city:
        city_theaters = theaters.filter(city=user_city)
        if city_theaters.exists():
            theaters = city_theaters

    today = timezone.now().date()
    selected_date_str = request.GET.get('date', today.strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = today

    date_tabs = []
    for i in range(5):
        d = today + timedelta(days=i)
        date_tabs.append({
            'date_str': d.strftime('%Y-%m-%d'),
            'day_name': 'TODAY' if i == 0 else d.strftime('%a').upper(),
            'date_num': d.strftime('%d'),
            'month_name': d.strftime('%b').upper(),
            'is_selected': d == selected_date
        })

    try:
        if request.user.is_authenticated:
            MovieView.objects.create(user=request.user, movie=movie)
        else:
            s_key = getattr(request.session, 'session_key', None)
            if s_key:
                MovieView.objects.create(session_key=s_key, movie=movie)
    except Exception:
        pass

    context = {
        'movie': movie,
        'theaters': theaters,
        'date_tabs': date_tabs,
        'selected_date': selected_date_str,
        'user_city': user_city,
        'city_choices': Theater.CITY_CHOICES,
    }
    return render(request, 'movies/theater_list.html', context)


# ==========================================
# NON-MOVIE EVENTS & CONCERTS VIEWS
# ==========================================

def event_list(request):
    queryset = Event.objects.all()

    category = request.GET.get('category', '')
    user_city = request.session.get('user_city')
    city = request.GET.get('city', user_city or '')
    search = request.GET.get('search', '').strip()

    if category and category in dict(Event.CATEGORY_CHOICES):
        queryset = queryset.filter(category=category)

    if city:
        city_qs = queryset.filter(city=city)
        if city_qs.exists():
            queryset = city_qs

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(venue_name__icontains=search) |
            Q(organizer__icontains=search) |
            Q(description__icontains=search)
        )

    paginator = Paginator(queryset, 9)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    category_title = dict(Event.CATEGORY_CHOICES).get(category, 'Live Events, Plays & Concerts')

    context = {
        'events': page_obj,
        'selected_category': category,
        'selected_city': city,
        'search_query': search,
        'category_choices': Event.CATEGORY_CHOICES,
        'city_choices': Theater.CITY_CHOICES,
        'category_title': category_title,
    }
    return render(request, 'movies/event_list.html', context)


def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    similar_events = Event.objects.filter(category=event.category).exclude(id=event.id)[:3]

    context = {
        'event': event,
        'similar_events': similar_events,
    }
    return render(request, 'movies/event_detail.html', context)


@login_required(login_url='/login/')
def book_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        try:
            ticket_count = int(request.POST.get('ticket_count', 1))
            ticket_count = max(1, min(10, ticket_count))
        except ValueError:
            ticket_count = 1

        total_price = event.price * ticket_count
        booking_ref = f"EVT-{uuid.uuid4().hex[:10].upper()}"

        event_booking = EventBooking.objects.create(
            user=request.user,
            event=event,
            ticket_count=ticket_count,
            payment_reference=booking_ref,
            status='PENDING',
            total_amount=total_price
        )

        razorpay_client = get_razorpay_client()
        razorpay_order_id = None

        if razorpay_client:
            try:
                order_data = {
                    'amount': int(total_price * 100),
                    'currency': 'INR',
                    'receipt': booking_ref,
                    'notes': {'user_id': request.user.id, 'event': event.name}
                }
                rzp_order = razorpay_client.order.create(data=order_data)
                razorpay_order_id = rzp_order['id']
            except Exception as e:
                print("Razorpay API Event Order Error:", e)

        if not razorpay_order_id:
            razorpay_order_id = f"order_test_{uuid.uuid4().hex[:12]}"

        payment = Payment.objects.create(
            user=request.user,
            booking_group_id=booking_ref,
            razorpay_order_id=razorpay_order_id,
            amount=total_price,
            currency='INR',
            status='CREATED'
        )

        return redirect('payment_checkout', payment_id=payment.id)

    return redirect('event_detail', event_id=event.id)


def live_seat_availability(request, theater_id):
    theaters = get_object_or_404(Theater, id=theater_id)
    seats = Seat.objects.filter(theater=theaters)

    user = request.user if request.user.is_authenticated else None
    seat_data = []

    for seat in seats:
        status = seat.status_for_user(user)
        is_mine = bool(user and seat.reserved_by == user and seat.is_reservation_active())
        seat_data.append({
            'id': seat.id,
            'number': seat.seat_number,
            'status': status,
            'is_mine': is_mine,
        })

    return JsonResponse({'seats': seat_data})


@login_required(login_url='/login/')
def book_seats(request, theater_id):
    theaters = get_object_or_404(Theater, id=theater_id)
    seats    = Seat.objects.filter(theater=theaters)

    selected_date_str = request.GET.get('date') or request.POST.get('show_date') or timezone.now().strftime('%Y-%m-%d')
    try:
        show_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        show_date = theaters.time.date()

    show_time_str = theaters.time.strftime('%I:%M %p')

    if request.method == 'POST':
        selected_seats = request.POST.getlist('seats')
        error_seats    = []

        if not selected_seats:
            return render(request, 'movies/seat_selection.html', {
                'theaters': theaters,
                'seats': seats,
                'show_date': show_date,
                'show_time': show_time_str,
                'error': 'Please select at least one seat before booking.',
            })

        booking_group_id = f"GRP-{uuid.uuid4().hex[:10].upper()}"
        num_seats = len(selected_seats)
        total_price = theaters.movie.price * num_seats

        created_bookings = []
        now = timezone.now()

        try:
            # Atomic transaction with row locking for race-condition protection
            with transaction.atomic():
                target_seats = Seat.objects.select_for_update().filter(id__in=selected_seats, theater=theaters)
                
                for seat in target_seats:
                    if seat.is_locked_for_user(request.user):
                        error_seats.append(seat.seat_number)
                        continue

                if not error_seats:
                    for seat in target_seats:
                        seat.reserved_by = request.user
                        seat.reserved_at = now
                        seat.save(update_fields=['reserved_by', 'reserved_at'])

                        booking = Booking.objects.create(
                            user=request.user,
                            seat=seat,
                            movie=theaters.movie,
                            theater=theaters,
                            show_date=show_date,
                            show_time=show_time_str,
                            status='PENDING',
                            total_amount=total_price,
                            payment_reference=booking_group_id
                        )
                        created_bookings.append(booking)

            if error_seats:
                error_message = f"The following seats are already reserved or booked by another user: {', '.join(error_seats)}"
                return render(request, 'movies/seat_selection.html', {
                    'theaters': theaters,
                    'seats': seats,
                    'show_date': show_date,
                    'show_time': show_time_str,
                    'error': error_message,
                })

            razorpay_client = get_razorpay_client()
            razorpay_order_id = None

            if razorpay_client:
                try:
                    order_data = {
                        'amount': int(total_price * 100),
                        'currency': 'INR',
                        'receipt': booking_group_id,
                        'notes': {'user_id': request.user.id, 'movie': theaters.movie.name}
                    }
                    rzp_order = razorpay_client.order.create(data=order_data)
                    razorpay_order_id = rzp_order['id']
                except Exception as e:
                    print("Razorpay API Order Error:", e)

            if not razorpay_order_id:
                razorpay_order_id = f"order_test_{uuid.uuid4().hex[:12]}"

            payment = Payment.objects.create(
                user=request.user,
                booking_group_id=booking_group_id,
                razorpay_order_id=razorpay_order_id,
                amount=total_price,
                currency='INR',
                status='CREATED'
            )

            return redirect('payment_checkout', payment_id=payment.id)
        except Exception:
            return render(request, 'movies/seat_selection.html', {
                'theaters': theaters,
                'seats': seats,
                'show_date': show_date,
                'show_time': show_time_str,
                'error': 'Seat reservations are disabled in read-only preview mode. Connect a PostgreSQL database for live bookings.',
            })

    return render(request, 'movies/seat_selection.html', {
        'theaters': theaters,
        'seats': seats,
        'show_date': show_date,
        'show_time': show_time_str,
    })


@login_required(login_url='/login/')
def cancel_or_modify_reservation(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)

    try:
        if payment.booking_group_id.startswith('EVT-'):
            evt_booking = EventBooking.objects.filter(payment_reference=payment.booking_group_id).first()
            if evt_booking:
                evt_booking.status = 'CANCELLED'
                evt_booking.save()
            payment.status = 'CANCELLED'
            payment.save()
            messages.info(request, "Your event booking transaction was cancelled.")
            return redirect('event_list')

        bookings = Booking.objects.filter(payment_reference=payment.booking_group_id)
        theater_id = None
        with transaction.atomic():
            payment.status = 'CANCELLED'
            payment.failure_reason = 'User cancelled or modified seat selection.'
            payment.save()

            for b in bookings:
                theater_id = b.theater.id
                b.status = 'CANCELLED'
                b.save()
                b.seat.release_reservation()

        messages.info(request, "Your temporary seat reservation was released. You can modify your selection below.")
        if theater_id:
            return redirect('book_seats', theater_id=theater_id)
    except Exception:
        messages.warning(request, "Database is in read-only preview mode.")
    return redirect('movie_list')


@login_required(login_url='/login/')
def payment_checkout(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)

    if payment.status == 'SUCCESS':
        messages.info(request, "This payment has already been verified successfully.")
        return redirect('profile')

    is_event = payment.booking_group_id.startswith('EVT-')

    if is_event:
        event_booking = get_object_or_404(EventBooking, payment_reference=payment.booking_group_id)
        razorpay_key_id = getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_bookmyseat123')
        is_real_key = bool(razorpay_key_id and not razorpay_key_id.startswith('rzp_test_bookmyseat'))

        context = {
            'payment': payment,
            'is_event': True,
            'event_booking': event_booking,
            'event': event_booking.event,
            'num_seats': event_booking.ticket_count,
            'razorpay_key_id': razorpay_key_id,
            'amount_in_paise': int(payment.amount * 100),
            'is_real_key': is_real_key,
            'remaining_seconds': 300,
        }
        return render(request, 'movies/payment_checkout.html', context)

    bookings = Booking.objects.filter(payment_reference=payment.booking_group_id)

    if not bookings.exists():
        messages.error(request, "No pending bookings found for this payment.")
        return redirect('profile')

    primary_booking = bookings.first()

    # Check 2-minute timer expiry
    elapsed = (timezone.now() - payment.created_at).total_seconds()
    remaining_seconds = max(0, int(120 - elapsed))

    if remaining_seconds <= 0 and payment.status == 'CREATED':
        try:
            with transaction.atomic():
                payment.status = 'FAILED'
                payment.failure_reason = '2-minute seat reservation timer expired.'
                payment.save()

                for b in bookings:
                    b.status = 'FAILED'
                    b.save()
                    b.seat.release_reservation()
        except Exception:
            pass

        messages.warning(request, "Your 2-minute seat reservation timer expired. The seats have been automatically released.")
        return redirect('book_seats', theater_id=primary_booking.theater.id)

    razorpay_key_id = getattr(settings, 'RAZORPAY_KEY_ID', 'rzp_test_bookmyseat123')
    is_real_key = bool(razorpay_key_id and not razorpay_key_id.startswith('rzp_test_bookmyseat'))

    context = {
        'payment': payment,
        'is_event': False,
        'bookings': bookings,
        'primary_booking': primary_booking,
        'seat_numbers': ", ".join([b.seat.seat_number for b in bookings]),
        'num_seats': bookings.count(),
        'razorpay_key_id': razorpay_key_id,
        'amount_in_paise': int(payment.amount * 100),
        'is_real_key': is_real_key,
        'remaining_seconds': remaining_seconds,
    }
    return render(request, 'movies/payment_checkout.html', context)


@login_required(login_url='/login/')
def payment_verify(request):
    if request.method == 'POST':
        payment_id_param = request.POST.get('payment_db_id')
        rzp_payment_id   = request.POST.get('razorpay_payment_id')
        rzp_order_id     = request.POST.get('razorpay_order_id')
        rzp_signature    = request.POST.get('razorpay_signature')
        action           = request.POST.get('action', 'verify')

        payment = get_object_or_404(Payment, id=payment_id_param, user=request.user)

        # Duplicate payment protection (Idempotency)
        if payment.status == 'SUCCESS':
            messages.info(request, "Payment was already completed successfully.")
            return redirect('profile')

        is_event = payment.booking_group_id.startswith('EVT-')

        key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '')
        razorpay_client = get_razorpay_client()
        is_signature_valid = False

        if action == 'success':
            if razorpay_client and rzp_order_id and rzp_payment_id and rzp_signature:
                try:
                    razorpay_client.utility.verify_payment_signature({
                        'razorpay_order_id': rzp_order_id,
                        'razorpay_payment_id': rzp_payment_id,
                        'razorpay_signature': rzp_signature
                    })
                    is_signature_valid = True
                except Exception as e:
                    print("Razorpay Signature Verification Error:", e)
                    is_signature_valid = False
            elif rzp_order_id and rzp_order_id.startswith('order_test_'):
                is_signature_valid = True
                if not rzp_payment_id:
                    rzp_payment_id = f"pay_test_{uuid.uuid4().hex[:12]}"
                if not rzp_signature:
                    rzp_signature = f"sig_test_{uuid.uuid4().hex[:16]}"
            elif key_secret and rzp_order_id and rzp_payment_id and rzp_signature:
                try:
                    generated_signature = hmac.new(
                        key_secret.encode('utf-8'),
                        f"{rzp_order_id}|{rzp_payment_id}".encode('utf-8'),
                        hashlib.sha256
                    ).hexdigest()
                    if generated_signature == rzp_signature:
                        is_signature_valid = True
                except Exception:
                    pass

        if is_signature_valid:
            with transaction.atomic():
                payment.status = 'SUCCESS'
                payment.razorpay_payment_id = rzp_payment_id
                payment.razorpay_signature = rzp_signature
                payment.save()

                if is_event:
                    evt_booking = EventBooking.objects.filter(payment_reference=payment.booking_group_id).first()
                    if evt_booking:
                        evt_booking.status = 'CONFIRMED'
                        evt_booking.save()
                    messages.success(request, f"Payment successful! Event booking confirmed for {evt_booking.event.name}.")
                    return redirect('profile')

                bookings = Booking.objects.filter(payment_reference=payment.booking_group_id)
                booking_ids = []
                for booking in bookings:
                    booking.status = 'CONFIRMED'
                    booking.save()
                    booking.seat.is_booked = True
                    booking.seat.reserved_at = None
                    booking.seat.reserved_by = None
                    booking.seat.save()
                    booking_ids.append(booking.id)

            async_email_dispatch(booking_ids)
            messages.success(request, f"Payment successful! Booking confirmed for {bookings.count()} seat(s). Ticket sent to your email.")
            return redirect('profile')

        else:
            reason = request.POST.get('failure_reason', 'Payment verification failed or transaction was cancelled by user.')
            with transaction.atomic():
                payment.status = 'CANCELLED' if action == 'cancelled' else 'FAILED'
                payment.failure_reason = reason
                payment.save()

                if is_event:
                    evt_booking = EventBooking.objects.filter(payment_reference=payment.booking_group_id).first()
                    if evt_booking:
                        evt_booking.status = 'CANCELLED' if action == 'cancelled' else 'FAILED'
                        evt_booking.save()
                else:
                    bookings = Booking.objects.filter(payment_reference=payment.booking_group_id)
                    for booking in bookings:
                        booking.status = 'CANCELLED' if action == 'cancelled' else 'FAILED'
                        booking.save()
                        booking.seat.release_reservation()

            context = {
                'payment': payment,
                'failure_reason': reason,
            }
            return render(request, 'movies/payment_failed.html', context)

    return redirect('profile')


@login_required(login_url='/login/')
def payment_retry(request, payment_id):
    old_payment = get_object_or_404(Payment, id=payment_id, user=request.user)

    if old_payment.booking_group_id.startswith('EVT-'):
        old_evt_booking = EventBooking.objects.filter(payment_reference=old_payment.booking_group_id).first()
        if not old_evt_booking:
            messages.error(request, "No event booking found for payment retry.")
            return redirect('profile')

        new_group_id = f"EVT-{uuid.uuid4().hex[:10].upper()}"
        old_evt_booking.status = 'PENDING'
        old_evt_booking.payment_reference = new_group_id
        old_evt_booking.save()

        new_payment = Payment.objects.create(
            user=request.user,
            booking_group_id=new_group_id,
            razorpay_order_id=f"order_test_{uuid.uuid4().hex[:12]}",
            amount=old_payment.amount,
            currency='INR',
            status='CREATED'
        )
        return redirect('payment_checkout', payment_id=new_payment.id)

    old_bookings = Booking.objects.filter(payment_reference=old_payment.booking_group_id)

    if not old_bookings.exists():
        messages.error(request, "No bookings found for payment retry.")
        return redirect('profile')

    theater = old_bookings.first().theater

    error_seats = []
    now = timezone.now()
    with transaction.atomic():
        for b in old_bookings:
            if b.seat.is_locked_for_user(request.user):
                error_seats.append(b.seat.seat_number)

    if error_seats:
        messages.error(request, f"Some of your previously selected seats ({', '.join(error_seats)}) are no longer available. Please select new seats.")
        return redirect('book_seats', theater_id=theater.id)

    new_group_id = f"GRP-{uuid.uuid4().hex[:10].upper()}"
    total_price = old_payment.amount

    try:
        with transaction.atomic():
            for b in old_bookings:
                b.status = 'PENDING'
                b.payment_reference = new_group_id
                b.save()
                b.seat.reserved_by = request.user
                b.seat.reserved_at = now
                b.seat.save()

        razorpay_client = get_razorpay_client()
        razorpay_order_id = None

        if razorpay_client:
            try:
                order_data = {
                    'amount': int(total_price * 100),
                    'currency': 'INR',
                    'receipt': new_group_id,
                }
                rzp_order = razorpay_client.order.create(data=order_data)
                razorpay_order_id = rzp_order['id']
            except Exception as e:
                print("Razorpay order retry creation error:", e)

        if not razorpay_order_id:
            razorpay_order_id = f"order_test_{uuid.uuid4().hex[:12]}"

        new_payment = Payment.objects.create(
            user=request.user,
            booking_group_id=new_group_id,
            razorpay_order_id=razorpay_order_id,
            amount=total_price,
            currency='INR',
            status='CREATED'
        )

        messages.info(request, "Created new payment session for your booking retry. You have 2 minutes to complete payment.")
        return redirect('payment_checkout', payment_id=new_payment.id)
    except Exception:
        messages.warning(request, "Payment retry is disabled on read-only preview mode.")
        return redirect('profile')


@csrf_exempt
def payment_webhook(request):
    if request.method == 'POST':
        webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')
        received_sig = request.META.get('HTTP_X_RAZORPAY_SIGNATURE', '')
        payload = request.body.decode('utf-8')

        if webhook_secret:
            expected_sig = hmac.new(
                webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(expected_sig, received_sig):
                return HttpResponse(status=400)

        try:
            event_data = json.loads(payload)
            event = event_data.get('event')
            entity = event_data.get('payload', {}).get('payment', {}).get('entity', {})
            order_id = entity.get('order_id')

            if order_id:
                payment = Payment.objects.filter(razorpay_order_id=order_id).first()
                if payment and payment.status != 'SUCCESS':
                    if payment.booking_group_id.startswith('EVT-'):
                        evt_b = EventBooking.objects.filter(payment_reference=payment.booking_group_id).first()
                        if event in ['payment.authorized', 'order.paid']:
                            payment.status = 'SUCCESS'
                            payment.razorpay_payment_id = entity.get('id')
                            payment.save()
                            if evt_b:
                                evt_b.status = 'CONFIRMED'
                                evt_b.save()
                        elif event in ['payment.failed']:
                            payment.status = 'FAILED'
                            payment.save()
                            if evt_b:
                                evt_b.status = 'FAILED'
                                evt_b.save()
                    else:
                        bookings = Booking.objects.filter(payment_reference=payment.booking_group_id)
                        if event in ['payment.authorized', 'order.paid']:
                            payment.status = 'SUCCESS'
                            payment.razorpay_payment_id = entity.get('id')
                            payment.save()

                            booking_ids = []
                            for b in bookings:
                                b.status = 'CONFIRMED'
                                b.save()
                                b.seat.is_booked = True
                                b.seat.reserved_at = None
                                b.seat.reserved_by = None
                                b.seat.save()
                                booking_ids.append(b.id)
                            async_email_dispatch(booking_ids)

                        elif event in ['payment.failed']:
                            payment.status = 'FAILED'
                            payment.failure_reason = entity.get('error_description', 'Payment failed via webhook')
                            payment.save()
                            for b in bookings:
                                b.status = 'FAILED'
                                b.save()
                                b.seat.release_reservation()

        except Exception as e:
            print("Webhook process error:", e)

        return HttpResponse(status=200)

    return HttpResponse(status=405)


@login_required(login_url='/login/')
def download_ticket(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if booking.user != request.user and not request.user.is_staff:
        return redirect('profile')

    if booking.status != 'CONFIRMED':
        messages.error(request, "Ticket is only available for confirmed bookings.")
        return redirect('profile')

    pdf_bytes = generate_ticket_pdf(booking)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Ticket_{booking.booking_id}.pdf"'
    return response


@login_required(login_url='/login/')
def download_event_ticket(request, booking_id):
    evt_booking = get_object_or_404(EventBooking, id=booking_id)
    if evt_booking.user != request.user and not request.user.is_staff:
        return redirect('profile')

    if evt_booking.status != 'CONFIRMED':
        messages.error(request, "Event ticket is only available for confirmed bookings.")
        return redirect('profile')

    # Create ticket PDF for EventBooking
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    import io
    import qrcode

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    p.setFont("Helvetica-Bold", 20)
    p.setFillColorRGB(0.1, 0.2, 0.5)
    p.drawString(50, 750, "BOOKMYSEAT EVENT TICKET")
    
    p.setFont("Helvetica", 12)
    p.setFillColorRGB(0, 0, 0)
    p.drawString(50, 710, f"Booking Ref: {evt_booking.booking_id}")
    p.drawString(50, 690, f"Event Name: {evt_booking.event.name}")
    p.drawString(50, 670, f"Category: {evt_booking.event.get_category_display()}")
    p.drawString(50, 650, f"Venue: {evt_booking.event.venue_name}, {evt_booking.event.get_city_display()}")
    p.drawString(50, 630, f"Date & Time: {evt_booking.event.event_date.strftime('%b %d, %Y at %I:%M %p')}")
    p.drawString(50, 610, f"Ticket Quantity: {evt_booking.ticket_count} Ticket(s)")
    p.drawString(50, 590, f"Total Amount Paid: Rs.{evt_booking.total_amount}")
    p.drawString(50, 570, f"Booked By: {evt_booking.user.username} ({evt_booking.user.email})")

    # Generate QR Code in memory
    from reportlab.lib.utils import ImageReader
    qr_data = f"EVENT BOOKING ID: {evt_booking.booking_id} | EVENT: {evt_booking.event.name} | PASSES: {evt_booking.ticket_count} | STATUS: CONFIRMED"
    qr_img = qrcode.make(qr_data)
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)

    p.drawImage(ImageReader(qr_buffer), 400, 580, width=150, height=150)
    p.showPage()
    p.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Event_Ticket_{evt_booking.booking_id}.pdf"'
    return response


# ==========================================
# TASK 6: ADMIN BUSINESS INSIGHTS DASHBOARD
# ==========================================

@user_passes_test(lambda u: u.is_authenticated and u.is_staff, login_url='/login/')
def admin_dashboard(request):
    now = timezone.now()
    today = now.date()

    # Parse custom date range filters
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = today - timedelta(days=30)
    else:
        start_date = today - timedelta(days=30)

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            end_date = today
    else:
        end_date = today

    # 1. Total Revenue Aggregations (Daily, Weekly, Monthly, Yearly, Custom)
    rev_today = Booking.objects.filter(status='CONFIRMED', booked_at__date=today).aggregate(tot=Sum('total_amount'))['tot'] or 0.00
    rev_week  = Booking.objects.filter(status='CONFIRMED', booked_at__date__gte=today - timedelta(days=7)).aggregate(tot=Sum('total_amount'))['tot'] or 0.00
    rev_month = Booking.objects.filter(status='CONFIRMED', booked_at__date__gte=today - timedelta(days=30)).aggregate(tot=Sum('total_amount'))['tot'] or 0.00
    rev_year  = Booking.objects.filter(status='CONFIRMED', booked_at__year=today.year).aggregate(tot=Sum('total_amount'))['tot'] or 0.00

    range_bookings = Booking.objects.filter(booked_at__date__range=(start_date, end_date))
    range_confirmed = range_bookings.filter(status='CONFIRMED')
    filtered_revenue = range_confirmed.aggregate(tot=Sum('total_amount'))['tot'] or 0.00

    # 2. Booking Trends & Cancellation Statistics
    total_bookings_count = range_bookings.count()
    confirmed_count = range_confirmed.count()
    cancelled_count = range_bookings.filter(status='CANCELLED').count()
    failed_count = range_bookings.filter(status='FAILED').count()
    pending_count = range_bookings.filter(status='PENDING').count()

    cancellation_rate = round((cancelled_count / total_bookings_count * 100), 1) if total_bookings_count > 0 else 0.0

    # 3. Theater Occupancy Percentage & Performance
    theaters = Theater.objects.annotate(
        total_seats_count=Count('seats', distinct=True),
        booked_seats_count=Count('seats', filter=Q(seats__is_booked=True), distinct=True),
        total_revenue=Coalesce(Sum('booking__total_amount', filter=Q(booking__status='CONFIRMED', booking__booked_at__date__range=(start_date, end_date)), distinct=True), Value(0.00), output_field=FloatField())
    )

    theater_occupancy_list = []
    for th in theaters:
        total_s = th.total_seats_count or 1
        booked_s = th.booked_seats_count or 0
        pct = round((booked_s / total_s) * 100, 1)
        theater_occupancy_list.append({
            'theater': th,
            'total_seats': total_s,
            'booked_seats': booked_s,
            'occupancy_pct': pct,
            'revenue': th.total_revenue,
        })

    theater_occupancy_list.sort(key=lambda x: x['revenue'], reverse=True)

    # 4. Most Booked Movies
    most_booked_movies = Movie.objects.annotate(
        confirmed_bookings=Count('booking', filter=Q(booking__status='CONFIRMED', booking__booked_at__date__range=(start_date, end_date)), distinct=True),
        revenue=Coalesce(Sum('booking__total_amount', filter=Q(booking__status='CONFIRMED', booking__booked_at__date__range=(start_date, end_date)), distinct=True), Value(0.00), output_field=FloatField())
    ).order_by('-confirmed_bookings')[:5]

    # 5. Top Performing Theaters
    top_theaters = sorted(theater_occupancy_list, key=lambda x: x['revenue'], reverse=True)[:5]

    # 6. Peak Booking Hours Distribution
    peak_hours_raw = (
        range_confirmed
        .annotate(hour=ExtractHour('booked_at'))
        .values('hour')
        .annotate(
            count=Count('id'),
            revenue=Coalesce(Sum('total_amount'), Value(0.00), output_field=FloatField())
        )
        .order_by('hour')
    )

    peak_hours = []
    for item in peak_hours_raw:
        hr = item['hour']
        hr_str = f"{hr:02d}:00 - {hr+1:02d}:00"
        peak_hours.append({
            'hour_str': hr_str,
            'count': item['count'],
            'revenue': item['revenue'],
        })

    # 7. User Growth Report
    from django.contrib.auth.models import User
    user_growth_raw = (
        User.objects.filter(date_joined__date__range=(start_date, end_date))
        .annotate(day=TruncDay('date_joined'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )

    user_growth = [
        {'day': item['day'].strftime('%Y-%m-%d'), 'count': item['count']}
        for item in user_growth_raw if item['day']
    ]

    total_users_count = User.objects.count()

    context = {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'revenue_today': rev_today,
        'revenue_week': rev_week,
        'revenue_month': rev_month,
        'revenue_year': rev_year,
        'filtered_revenue': filtered_revenue,
        'total_bookings_count': total_bookings_count,
        'confirmed_count': confirmed_count,
        'cancelled_count': cancelled_count,
        'failed_count': failed_count,
        'pending_count': pending_count,
        'cancellation_rate': cancellation_rate,
        'theater_occupancy_list': theater_occupancy_list,
        'most_booked_movies': most_booked_movies,
        'top_theaters': top_theaters,
        'peak_hours': peak_hours,
        'user_growth': user_growth,
        'total_users_count': total_users_count,
    }
    return render(request, 'movies/admin_dashboard.html', context)


@user_passes_test(lambda u: u.is_authenticated and u.is_staff, login_url='/login/')
def export_analytics_csv(request):
    now = timezone.now()
    today = now.date()

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else today - timedelta(days=30)
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else today
    except ValueError:
        start_date = today - timedelta(days=30)
        end_date = today

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="business_insights_report_{start_date}_{end_date}.csv"'

    writer = csv.writer(response)

    # Section 1: Executive Summary
    writer.writerow(['=== BOOKMYSEAT BUSINESS INSIGHTS REPORT ==='])
    writer.writerow(['Report Date Range', f"{start_date} to {end_date}"])
    writer.writerow(['Generated At', now.strftime('%Y-%m-%d %H:%M:%S UTC')])
    writer.writerow([])

    # Revenue Metrics
    rev_today = Booking.objects.filter(status='CONFIRMED', booked_at__date=today).aggregate(tot=Sum('total_amount'))['tot'] or 0.00
    rev_month = Booking.objects.filter(status='CONFIRMED', booked_at__date__gte=today - timedelta(days=30)).aggregate(tot=Sum('total_amount'))['tot'] or 0.00
    rev_year  = Booking.objects.filter(status='CONFIRMED', booked_at__year=today.year).aggregate(tot=Sum('total_amount'))['tot'] or 0.00
    range_bookings = Booking.objects.filter(booked_at__date__range=(start_date, end_date))
    range_confirmed = range_bookings.filter(status='CONFIRMED')
    filtered_rev = range_confirmed.aggregate(tot=Sum('total_amount'))['tot'] or 0.00

    writer.writerow(['=== REVENUE METRICS ==='])
    writer.writerow(['Metric', 'Amount (INR)'])
    writer.writerow(['Today Revenue', f"Rs.{rev_today:.2f}"])
    writer.writerow(['Last 30 Days Revenue', f"Rs.{rev_month:.2f}"])
    writer.writerow(['Current Year Revenue', f"Rs.{rev_year:.2f}"])
    writer.writerow(['Selected Range Revenue', f"Rs.{filtered_rev:.2f}"])
    writer.writerow([])

    # Booking Statistics
    tot_cnt = range_bookings.count()
    conf_cnt = range_confirmed.count()
    canc_cnt = range_bookings.filter(status='CANCELLED').count()
    fail_cnt = range_bookings.filter(status='FAILED').count()
    canc_rate = round((canc_cnt / tot_cnt * 100), 1) if tot_cnt > 0 else 0.0

    writer.writerow(['=== BOOKING TRENDS & CANCELLATION STATS ==='])
    writer.writerow(['Stat', 'Count'])
    writer.writerow(['Total Bookings Processed', tot_cnt])
    writer.writerow(['Confirmed Bookings', conf_cnt])
    writer.writerow(['Cancelled Bookings', canc_cnt])
    writer.writerow(['Failed Transactions', fail_cnt])
    writer.writerow(['Cancellation Rate (%)', f"{canc_rate}%"])
    writer.writerow([])

    # Theater Occupancy Report
    writer.writerow(['=== THEATER OCCUPANCY & PERFORMANCE ==='])
    writer.writerow(['Theater Name', 'Screen', 'City', 'Total Seats', 'Booked Seats', 'Occupancy (%)', 'Total Revenue (INR)'])
    theaters = Theater.objects.annotate(
        total_seats_count=Count('seats', distinct=True),
        booked_seats_count=Count('seats', filter=Q(seats__is_booked=True), distinct=True),
        total_revenue=Coalesce(Sum('booking__total_amount', filter=Q(booking__status='CONFIRMED', booking__booked_at__date__range=(start_date, end_date)), distinct=True), Value(0.00), output_field=FloatField())
    )
    for th in theaters:
        total_s = th.total_seats_count or 1
        booked_s = th.booked_seats_count or 0
        pct = round((booked_s / total_s) * 100, 1)
        writer.writerow([th.name, th.screen, th.get_city_display(), total_s, booked_s, f"{pct}%", f"Rs.{th.total_revenue:.2f}"])
    writer.writerow([])

    # Most Booked Movies
    writer.writerow(['=== MOST BOOKED MOVIES ==='])
    writer.writerow(['Movie Name', 'Genre', 'Language', 'Rating', 'Confirmed Bookings', 'Total Revenue (INR)'])
    movies = Movie.objects.annotate(
        confirmed_bookings=Count('booking', filter=Q(booking__status='CONFIRMED', booking__booked_at__date__range=(start_date, end_date)), distinct=True),
        revenue=Coalesce(Sum('booking__total_amount', filter=Q(booking__status='CONFIRMED', booking__booked_at__date__range=(start_date, end_date)), distinct=True), Value(0.00), output_field=FloatField())
    ).order_by('-confirmed_bookings')[:10]

    for m in movies:
        writer.writerow([m.name, m.get_genre_display(), m.get_language_display(), float(m.rating), m.confirmed_bookings, f"Rs.{m.revenue:.2f}"])
    writer.writerow([])

    # Peak Booking Hours
    writer.writerow(['=== PEAK BOOKING HOURS ==='])
    writer.writerow(['Hour Window', 'Bookings Count', 'Total Revenue (INR)'])
    peak_hours_raw = (
        range_confirmed
        .annotate(hour=ExtractHour('booked_at'))
        .values('hour')
        .annotate(
            count=Count('id'),
            revenue=Coalesce(Sum('total_amount'), Value(0.00), output_field=FloatField())
        )
        .order_by('hour')
    )
    for p in peak_hours_raw:
        hr = p['hour']
        writer.writerow([f"{hr:02d}:00 - {hr+1:02d}:00", p['count'], f"Rs.{p['revenue']:.2f}"])

    return response

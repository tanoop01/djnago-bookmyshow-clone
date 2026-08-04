import threading
from datetime import time as dt_time, datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.utils import timezone

from .models import Movie, Theater, Seat, Booking, MovieView
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


def async_email_dispatch(booking_id):
    def _worker():
        try:
            send_ticket_email_task(booking_id)
        except Exception as e:
            print("Background email error:", e)
    threading.Thread(target=_worker, daemon=True).start()


def set_city(request):
    if request.method == 'POST':
        city = request.POST.get('city', '').lower()
        if city:
            request.session['user_city'] = city
    elif request.method == 'GET':
        city = request.GET.get('city', '').lower()
        if city:
            request.session['user_city'] = city
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
            booking_count=Count('booking', distinct=True)
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

    if request.user.is_authenticated:
        MovieView.objects.create(user=request.user, movie=movie)
    else:
        if not request.session.session_key:
            request.session.create()
        MovieView.objects.create(session_key=request.session.session_key, movie=movie)

    context = {
        'movie': movie,
        'theaters': theaters,
        'date_tabs': date_tabs,
        'selected_date': selected_date_str,
        'user_city': user_city,
        'city_choices': Theater.CITY_CHOICES,
    }
    return render(request, 'movies/theater_list.html', context)


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

        created_booking_ids = []
        for seat_id in selected_seats:
            seat = get_object_or_404(Seat, id=seat_id, theater=theaters)
            if seat.is_booked:
                error_seats.append(seat.seat_number)
                continue
            try:
                booking = Booking.objects.create(
                    user=request.user,
                    seat=seat,
                    movie=theaters.movie,
                    theater=theaters,
                    show_date=show_date,
                    show_time=show_time_str,
                )
                seat.is_booked = True
                seat.save()
                created_booking_ids.append(booking.id)

            except IntegrityError:
                error_seats.append(seat.seat_number)

        if created_booking_ids:
            async_email_dispatch(created_booking_ids)

        if error_seats:
            error_message = f"The following seats are already booked: {', '.join(error_seats)}"
            return render(request, 'movies/seat_selection.html', {
                'theaters': theaters,
                'seats': seats,
                'show_date': show_date,
                'show_time': show_time_str,
                'error': error_message,
            })

        return redirect('profile')

    return render(request, 'movies/seat_selection.html', {
        'theaters': theaters,
        'seats': seats,
        'show_date': show_date,
        'show_time': show_time_str,
    })


@login_required(login_url='/login/')
def download_ticket(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if booking.user != request.user and not request.user.is_staff:
        return redirect('profile')

    pdf_bytes = generate_ticket_pdf(booking)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Ticket_{booking.booking_id}.pdf"'
    return response

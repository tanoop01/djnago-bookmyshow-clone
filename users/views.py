from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required

from movies.models import Movie, Booking, Payment, Event, EventBooking
from movies.utils import get_recommendations
from .forms import UserRegisterForm, UserUpdateForm


def home(request):
    user_city = request.session.get('user_city')
    
    recommendations = get_recommendations(request, limit=4)
    movies = Movie.objects.all().order_by('-release_date')[:8]

    # Non-movie categories
    live_events_qs = Event.objects.filter(category='events')
    plays_qs       = Event.objects.filter(category='plays')
    sports_qs      = Event.objects.filter(category='sports')
    music_qs       = Event.objects.filter(category='music')

    if user_city:
        if live_events_qs.filter(city=user_city).exists():
            live_events_qs = live_events_qs.filter(city=user_city)
        if plays_qs.filter(city=user_city).exists():
            plays_qs = plays_qs.filter(city=user_city)
        if sports_qs.filter(city=user_city).exists():
            sports_qs = sports_qs.filter(city=user_city)
        if music_qs.filter(city=user_city).exists():
            music_qs = music_qs.filter(city=user_city)

    context = {
        'recommendations': recommendations,
        'movies': movies,
        'live_events': live_events_qs[:6],
        'plays': plays_qs[:4],
        'sports': sports_qs[:6],
        'music_concerts': music_qs[:6],
        'user_city': user_city,
    }
    return render(request, 'home.html', context)


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url:
                return redirect(next_url)
            if user.is_staff:
                return redirect('admin_dashboard')
            return redirect('/')
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})


@login_required
def profile(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-booked_at')
    event_bookings = EventBooking.objects.filter(user=request.user).order_by('-booked_at')
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')

    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        if u_form.is_valid():
            u_form.save()
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)

    context = {
        'u_form': u_form,
        'bookings': bookings,
        'event_bookings': event_bookings,
        'payments': payments,
    }
    return render(request, 'users/profile.html', context)


@login_required
def reset_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('profile')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'users/reset_password.html', {'form': form})
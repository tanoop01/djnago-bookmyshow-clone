from django.contrib import admin
from .models import Movie, Theater, Seat, Booking, MovieView


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['name', 'genre', 'language', 'rating', 'price', 'release_date']
    list_filter = ['genre', 'language']
    search_fields = ['name', 'cast']


@admin.register(Theater)
class TheaterAdmin(admin.ModelAdmin):
    list_display = ['name', 'movie', 'city', 'time']
    list_filter = ['city']
    search_fields = ['name']


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ['theater', 'seat_number', 'is_booked']
    list_filter = ['is_booked']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'theater', 'seat', 'booked_at']
    list_filter = ['movie', 'theater']
    search_fields = ['user__username']


@admin.register(MovieView)
class MovieViewAdmin(admin.ModelAdmin):
    list_display = ['movie', 'user', 'session_key', 'viewed_at']
    list_filter = ['movie']

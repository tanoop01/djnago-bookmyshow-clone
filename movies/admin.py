from django.contrib import admin
from .models import Movie, MoviePoster, Theater, Seat, Booking, Review, MovieView


class MoviePosterInline(admin.TabularInline):
    model = MoviePoster
    extra = 2
    fields = ['image', 'caption']


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['name', 'genre', 'language', 'age_certification', 'duration_mins', 'rating', 'price', 'release_date']
    list_filter = ['genre', 'language', 'age_certification']
    search_fields = ['name', 'cast', 'description']
    inlines = [MoviePosterInline]
    fieldsets = (
        ('Basic Details', {
            'fields': ('name', 'image', 'description', 'genre', 'language', 'price', 'rating')
        }),
        ('Movie Specs & Media', {
            'fields': ('trailer_url', 'duration_mins', 'age_certification', 'release_date', 'cast')
        }),
    )


@admin.register(MoviePoster)
class MoviePosterAdmin(admin.ModelAdmin):
    list_display = ['movie', 'caption', 'created_at']
    list_filter = ['movie']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['movie', 'user', 'rating', 'is_verified_viewer', 'is_reported', 'created_at']
    list_filter = ['rating', 'is_verified_viewer', 'is_reported', 'movie']
    search_fields = ['user__username', 'movie__name', 'comment', 'report_reason']
    actions = ['approve_and_clear_reports', 'delete_reported_reviews']

    def approve_and_clear_reports(self, request, queryset):
        queryset.update(is_reported=False, report_reason=None)
        self.message_user(request, "Selected reported reviews have been cleared.")
    approve_and_clear_reports.short_description = "Clear reported status on selected reviews"

    def delete_reported_reviews(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} review(s) deleted.")
    delete_reported_reviews.short_description = "Delete selected reported reviews"


@admin.register(Theater)
class TheaterAdmin(admin.ModelAdmin):
    list_display = ['name', 'movie', 'city', 'screen', 'time']
    list_filter = ['city', 'screen', 'movie']
    search_fields = ['name']


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ['theater', 'seat_number', 'is_booked']
    list_filter = ['is_booked', 'theater']
    search_fields = ['seat_number']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_id', 'user', 'movie', 'theater', 'seat', 'show_date', 'show_time', 'booked_at']
    list_filter = ['movie', 'theater', 'show_date']
    search_fields = ['booking_id', 'payment_reference', 'user__username', 'movie__name']


@admin.register(MovieView)
class MovieViewAdmin(admin.ModelAdmin):
    list_display = ['movie', 'user', 'session_key', 'viewed_at']
    list_filter = ['movie']

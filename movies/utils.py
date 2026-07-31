from django.db.models import Count


def get_recommendations(request, limit=8):
    from .models import Movie, Booking, MovieView

    if request.user.is_authenticated:
        booked_ids = list(
            Booking.objects.filter(user=request.user)
            .values_list('movie_id', flat=True)
        )

        preferred_genres = list(
            Movie.objects.filter(id__in=booked_ids)
            .values_list('genre', flat=True)
            .distinct()
        )

        viewed_ids = list(
            MovieView.objects.filter(user=request.user)
            .order_by('-viewed_at')
            .values_list('movie_id', flat=True)[:30]
        )

        viewed_genres = list(
            Movie.objects.filter(id__in=viewed_ids)
            .values_list('genre', flat=True)
            .distinct()
        )

        all_genres = list(set(preferred_genres + viewed_genres))

        if all_genres:
            recs = (
                Movie.objects.filter(genre__in=all_genres)
                .exclude(id__in=booked_ids)
                .annotate(booking_count=Count('booking', distinct=True))
                .order_by('-booking_count', '-rating')[:limit]
            )
            if recs.exists():
                return recs

    return (
        Movie.objects.annotate(booking_count=Count('booking', distinct=True))
        .order_by('-booking_count', '-rating')[:limit]
    )

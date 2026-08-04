from django.core.management.base import BaseCommand
from django.utils import timezone
import datetime
from movies.models import Movie, Theater, Seat, Booking


class Command(BaseCommand):
    help = 'Seeds theaters across cities, upcoming dates, and resets available seats for testing'

    def handle(self, *args, **options):
        self.stdout.write('Clearing old bookings, theaters, and refreshing seats...')

        Booking.objects.all().delete()
        Seat.objects.all().delete()
        Theater.objects.all().delete()

        now = timezone.now()
        cities = ['mumbai', 'delhi', 'bangalore', 'chennai', 'hyderabad', 'pune', 'kolkata', 'ahmedabad']

        theater_names = {
            'mumbai': ['PVR ICON Phoenix Palladium', 'INOX Megaplex Inorbit', 'Cinepolis Fun Republic'],
            'delhi': ['PVR Director Cut Vasant Kunj', 'INOX Select Citywalk', 'DT Cinemas DLF Mall'],
            'bangalore': ['PVR Forum Mall Koramangala', 'INOX Lido Mall MG Road', 'Cinepolis Forum Shantiniketan'],
            'chennai': ['PVR Satham Royapettah', 'INOX Chennai Citi Centre', 'AGS Cinemas T Nagar'],
            'hyderabad': ['PVR Next Galleria Mall', 'AMB Cinemas Gachibowli', 'Prasads IMAX Tank Bund'],
            'pune': ['PVR Market City Viman Nagar', 'INOX Bund Garden', 'Cinepolis Seasons Mall'],
            'kolkata': ['PVR Mani Square', 'INOX Quest Mall', 'Cinepolis Acropolis Mall'],
            'ahmedabad': ['PVR Acropolis Mall', 'INOX Himalaya Mall', 'Cinepolis Alpha One']
        }

        screens = ['Screen 1', 'Screen 2', 'IMAX 3D', 'VIP Screen']
        seat_rows = ['A', 'B', 'C', 'D']

        movies = Movie.objects.all()
        total_seats = 0
        total_theaters = 0

        for movie in movies:
            for city in cities:
                names = theater_names.get(city, [f"PVR {city.capitalize()}"])
                for idx, t_name in enumerate(names[:2]):
                    for day_offset in range(5):
                        show_date = (now + datetime.timedelta(days=day_offset)).date()
                        show_time = datetime.datetime.combine(
                            show_date,
                            datetime.time(hour=14 + (idx * 3) + (day_offset % 2), minute=30)
                        )
                        show_time = timezone.make_aware(show_time) if timezone.is_naive(show_time) else show_time

                        theater = Theater.objects.create(
                            name=t_name,
                            movie=movie,
                            time=show_time,
                            city=city,
                            screen=screens[(idx + day_offset) % len(screens)]
                        )
                        total_theaters += 1

                        for row in seat_rows:
                            for num in range(1, 9):
                                Seat.objects.create(
                                    theater=theater,
                                    seat_number=f"{row}{num}",
                                    is_booked=False
                                )
                                total_seats += 1

        self.stdout.write(self.style.SUCCESS(f'Done! Created {total_theaters} showtimes with {total_seats} seats across 8 cities.'))

import uuid
import re
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg


class Movie(models.Model):
    GENRE_CHOICES = [
        ('action', 'Action'),
        ('comedy', 'Comedy'),
        ('drama', 'Drama'),
        ('horror', 'Horror'),
        ('romance', 'Romance'),
        ('thriller', 'Thriller'),
        ('sci_fi', 'Sci-Fi'),
        ('animation', 'Animation'),
        ('documentary', 'Documentary'),
        ('fantasy', 'Fantasy'),
        ('adventure', 'Adventure'),
        ('biography', 'Biography'),
    ]

    LANGUAGE_CHOICES = [
        ('english', 'English'),
        ('hindi', 'Hindi'),
        ('tamil', 'Tamil'),
        ('telugu', 'Telugu'),
        ('kannada', 'Kannada'),
        ('malayalam', 'Malayalam'),
        ('bengali', 'Bengali'),
        ('marathi', 'Marathi'),
    ]

    AGE_CERTIFICATION_CHOICES = [
        ('U', 'U - Unrestricted Public Exhibition'),
        ('U/A 7+', 'U/A 7+ - Parental Guidance for under 7'),
        ('U/A 13+', 'U/A 13+ - Parental Guidance for under 13'),
        ('U/A 16+', 'U/A 16+ - Parental Guidance for under 16'),
        ('A', 'A - Restricted to Adults'),
        ('S', 'S - Restricted to Special Class'),
    ]

    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='movies/')
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    cast = models.TextField()
    description = models.TextField(blank=True, null=True)
    genre = models.CharField(max_length=50, choices=GENRE_CHOICES, default='action')
    language = models.CharField(max_length=50, choices=LANGUAGE_CHOICES, default='hindi')
    release_date = models.DateField(null=True, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=200.00)
    trailer_url = models.URLField(blank=True, null=True, help_text="YouTube Trailer URL (e.g. https://www.youtube.com/watch?v=...)")
    duration_mins = models.PositiveIntegerField(default=120, help_text="Duration in minutes")
    age_certification = models.CharField(max_length=20, choices=AGE_CERTIFICATION_CHOICES, default='U/A 13+')

    @property
    def trailer_embed_url(self):
        if not self.trailer_url:
            return None
        match = re.search(r'(?:v=|\/embed\/|\/youtu\.be\/|\/v\/|\/e\/|watch\?v=|\&v=)([^#\&\?]{11})', self.trailer_url)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube-nocookie.com/embed/{video_id}"
        return None

    def update_average_rating(self):
        avg_rating = self.reviews.filter(is_reported=False).aggregate(Avg('rating'))['rating__avg']
        if avg_rating is not None:
            self.rating = round(avg_rating, 1)
        else:
            self.rating = 0.0
        self.save(update_fields=['rating'])

    def __str__(self):
        return self.name


class MoviePoster(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='posters')
    image = models.ImageField(upload_to='movie_posters/')
    caption = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Poster for {self.movie.name}"


class Theater(models.Model):
    CITY_CHOICES = [
        ('mumbai', 'Mumbai'),
        ('delhi', 'Delhi'),
        ('bangalore', 'Bangalore'),
        ('chennai', 'Chennai'),
        ('hyderabad', 'Hyderabad'),
        ('kolkata', 'Kolkata'),
        ('pune', 'Pune'),
        ('ahmedabad', 'Ahmedabad'),
        ('jaipur', 'Jaipur'),
        ('surat', 'Surat'),
    ]

    name = models.CharField(max_length=255)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='theaters')
    time = models.DateTimeField()
    city = models.CharField(max_length=50, choices=CITY_CHOICES, default='mumbai')
    screen = models.CharField(max_length=50, default='Screen 1')

    def __str__(self):
        return f'{self.name} ({self.screen}) - {self.movie.name} at {self.time}'


class Seat(models.Model):
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE, related_name='seats')
    seat_number = models.CharField(max_length=10)
    is_booked = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.seat_number} in {self.theater.name}'


class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seat = models.OneToOneField(Seat, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE)
    show_date = models.DateField(null=True, blank=True)
    show_time = models.CharField(max_length=100, blank=True)
    booked_at = models.DateTimeField(auto_now_add=True)
    booking_id = models.CharField(max_length=50, unique=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        if not self.booking_id:
            self.booking_id = f"BMS-{uuid.uuid4().hex[:8].upper()}"
        if not self.payment_reference:
            self.payment_reference = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Booking {self.booking_id} by {self.user.username} for {self.seat.seat_number}'


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(default=10, help_text="Rating from 1 to 10")
    comment = models.TextField()
    is_verified_viewer = models.BooleanField(default=False)
    is_reported = models.BooleanField(default=False)
    report_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'movie')
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.movie.update_average_rating()

    def delete(self, *args, **kwargs):
        movie = self.movie
        super().delete(*args, **kwargs)
        movie.update_average_rating()

    def __str__(self):
        return f"Review by {self.user.username} for {self.movie.name} ({self.rating}/10)"


class MovieView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='views')
    session_key = models.CharField(max_length=40, null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']

    def __str__(self):
        return f'{self.movie.name} viewed at {self.viewed_at}'
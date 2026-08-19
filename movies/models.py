import uuid
import re
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg
from django.utils import timezone


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

    class Meta:
        indexes = [
            models.Index(fields=['genre', 'rating']),
            models.Index(fields=['language', 'rating']),
            models.Index(fields=['release_date']),
        ]

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
        # Metros & Tier 1
        ('mumbai', 'Mumbai'),
        ('delhi', 'Delhi-NCR'),
        ('bangalore', 'Bengaluru / Bangalore'),
        ('chennai', 'Chennai'),
        ('hyderabad', 'Hyderabad'),
        ('kolkata', 'Kolkata'),
        ('pune', 'Pune'),
        ('ahmedabad', 'Ahmedabad'),
        
        # Key Cities Across India
        ('jalandhar', 'Jalandhar'),
        ('amritsar', 'Amritsar'),
        ('ludhiana', 'Ludhiana'),
        ('chandigarh', 'Chandigarh'),
        ('patiala', 'Patiala'),
        ('bathinda', 'Bathinda'),
        ('jaipur', 'Jaipur'),
        ('surat', 'Surat'),
        ('lucknow', 'Lucknow'),
        ('kanpur', 'Kanpur'),
        ('nagpur', 'Nagpur'),
        ('indore', 'Indore'),
        ('thane', 'Thane'),
        ('bhopal', 'Bhopal'),
        ('visakhapatnam', 'Visakhapatnam'),
        ('patna', 'Patna'),
        ('vadodara', 'Vadodara'),
        ('ghaziabad', 'Ghaziabad'),
        ('agra', 'Agra'),
        ('nashik', 'Nashik'),
        ('faridabad', 'Faridabad'),
        ('meerut', 'Meerut'),
        ('rajkot', 'Rajkot'),
        ('varanasi', 'Varanasi'),
        ('srinagar', 'Srinagar'),
        ('aurangabad', 'Chhatrapati Sambhajinagar / Aurangabad'),
        ('dhanbad', 'Dhanbad'),
        ('navi_mumbai', 'Navi Mumbai'),
        ('allahabad', 'Prayagraj / Allahabad'),
        ('ranchi', 'Ranchi'),
        ('howrah', 'Howrah'),
        ('coimbatore', 'Coimbatore'),
        ('jabalpur', 'Jabalpur'),
        ('gwalior', 'Gwalior'),
        ('vijayawada', 'Vijayawada'),
        ('jodhpur', 'Jodhpur'),
        ('madurai', 'Madurai'),
        ('raipur', 'Raipur'),
        ('kota', 'Kota'),
        ('guwahati', 'Guwahati'),
        ('solapur', 'Solapur'),
        ('bareilly', 'Bareilly'),
        ('moradabad', 'Moradabad'),
        ('mysore', 'Mysuru / Mysore'),
        ('gurgaon', 'Gurugram / Gurgaon'),
        ('noida', 'Noida'),
        ('mangalore', 'Mangaluru / Mangalore'),
        ('kochi', 'Kochi / Cochin'),
        ('goa', 'Goa'),
        ('trivandrum', 'Thiruvananthapuram / Trivandrum'),
        ('pondicherry', 'Puducherry / Pondicherry'),
        ('dehradun', 'Dehradun'),
        ('shimla', 'Shimla'),
        ('bhubaneswar', 'Bhubaneswar'),
        ('cuttack', 'Cuttack'),
        ('jammu', 'Jammu'),
    ]

    name = models.CharField(max_length=255)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='theaters')
    time = models.DateTimeField()
    city = models.CharField(max_length=50, choices=CITY_CHOICES, default='mumbai')
    screen = models.CharField(max_length=50, default='Screen 1')

    class Meta:
        indexes = [
            models.Index(fields=['city', 'time']),
            models.Index(fields=['movie', 'city']),
        ]

    def __str__(self):
        return f'{self.name} ({self.screen}) - {self.movie.name} at {self.time}'


class Seat(models.Model):
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE, related_name='seats')
    seat_number = models.CharField(max_length=10)
    is_booked = models.BooleanField(default=False)
    reserved_at = models.DateTimeField(null=True, blank=True)
    reserved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reserved_seats')

    class Meta:
        indexes = [
            models.Index(fields=['theater', 'is_booked']),
            models.Index(fields=['reserved_at', 'reserved_by']),
        ]

    def is_reservation_active(self):
        if self.reserved_at and self.reserved_by:
            elapsed = (timezone.now() - self.reserved_at).total_seconds()
            return elapsed < 120
        return False

    def is_locked_for_user(self, user=None):
        if self.is_booked:
            return True
        if self.is_reservation_active():
            if user is None or (user.is_authenticated and self.reserved_by != user):
                return True
        return False

    def status_for_user(self, user=None):
        if self.is_booked:
            return 'BOOKED'
        if self.is_reservation_active():
            return 'RESERVED'
        return 'AVAILABLE'

    def release_reservation(self):
        self.reserved_at = None
        self.reserved_by = None
        self.save(update_fields=['reserved_at', 'reserved_by'])

    def __str__(self):
        return f'{self.seat_number} in {self.theater.name}'


class Booking(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Payment'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('FAILED', 'Failed Payment'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    theater = models.ForeignKey(Theater, on_delete=models.CASCADE)
    show_date = models.DateField(null=True, blank=True)
    show_time = models.CharField(max_length=100, blank=True)
    booked_at = models.DateTimeField(auto_now_add=True)
    booking_id = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'booked_at']),
            models.Index(fields=['show_date', 'status']),
            models.Index(fields=['movie', 'status']),
            models.Index(fields=['theater', 'status']),
            models.Index(fields=['user', 'status']),
        ]

    def save(self, *args, **kwargs):
        if not self.booking_id:
            self.booking_id = f"BMS-{uuid.uuid4().hex[:8].upper()}"
        if not self.payment_reference:
            self.payment_reference = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Booking {self.booking_id} ({self.status}) by {self.user.username}'


# ==========================================
# NON-MOVIE EVENTS, PLAYS, SPORTS, CONCERTS
# ==========================================

class Event(models.Model):
    CATEGORY_CHOICES = [
        ('events', 'Live Events'),
        ('plays', 'Plays & Theater'),
        ('sports', 'Sports Matches'),
        ('music', 'Music & Concerts'),
    ]

    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='events')
    image_url = models.URLField(max_length=500, blank=True, null=True)
    banner_url = models.URLField(max_length=500, blank=True, null=True)
    city = models.CharField(max_length=50, choices=Theater.CITY_CHOICES, default='mumbai')
    venue_name = models.CharField(max_length=255, default='Main Arena / Auditorium')
    event_date = models.DateTimeField()
    price = models.DecimalField(max_digits=8, decimal_places=2, default=499.00)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.5)
    description = models.TextField(blank=True, null=True)
    organizer = models.CharField(max_length=255, default='BookMySeat Live')
    duration_mins = models.PositiveIntegerField(default=150)
    language = models.CharField(max_length=50, default='English / Hindi')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['event_date']
        indexes = [
            models.Index(fields=['category', 'city']),
            models.Index(fields=['event_date']),
        ]

    def __str__(self):
        return f"[{self.get_category_display()}] {self.name} ({self.city.capitalize()})"


class EventBooking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_bookings')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='bookings')
    ticket_count = models.PositiveIntegerField(default=1)
    booking_id = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=Booking.STATUS_CHOICES, default='PENDING')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    booked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-booked_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['event', 'status']),
        ]

    def save(self, *args, **kwargs):
        if not self.booking_id:
            self.booking_id = f"EVT-{uuid.uuid4().hex[:8].upper()}"
        if not self.payment_reference:
            self.payment_reference = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"EventBooking {self.booking_id} for {self.event.name} by {self.user.username}"


class Payment(models.Model):
    STATUS_CHOICES = [
        ('CREATED', 'Created'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booking_group_id = models.CharField(max_length=100, blank=True, help_text="Group identifier for multi-seat bookings")
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CREATED')
    failure_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['razorpay_order_id']),
            models.Index(fields=['booking_group_id']),
        ]

    def __str__(self):
        return f"Payment {self.razorpay_order_id} ({self.status}) - Rs.{self.amount}"


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
        indexes = [
            models.Index(fields=['movie', 'is_reported']),
            models.Index(fields=['is_verified_viewer']),
        ]

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
        indexes = [
            models.Index(fields=['user', 'viewed_at']),
            models.Index(fields=['session_key', 'viewed_at']),
        ]

    def __str__(self):
        return f'{self.movie.name} viewed at {self.viewed_at}'
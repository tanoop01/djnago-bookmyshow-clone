# BookMySeat – Django BookMyShow Clone

A full-featured movie ticket booking application built with Django, PostgreSQL (Render), and deployed on Vercel.

---

## Live URL

> Deploy to Vercel and paste the public URL here.

---

## Tech Stack

| Layer      | Technology                              |
|------------|-----------------------------------------|
| Backend    | Django 3.2, Python 3.x, Celery          |
| Database   | PostgreSQL (Render) via dj-database-url |
| Task Queue | Celery + Redis (background email delivery) |
| PDF & QR   | ReportLab, qrcode                       |
| Frontend   | Bootstrap 4, Vanilla CSS, Vanilla JS    |
| Storage    | Local media (development)               |
| Deployment | Vercel (serverless Python runtime)      |

---

## Setup and Running Locally

```bash
git clone <repo-url>
cd djnago-bookmyshow-clone

pip install -r requirements.txt

python manage.py migrate

python manage.py createsuperuser

# Start Celery worker (optional for local background processing)
celery -A bookmyseat worker --loglevel=info

python manage.py runserver
```

Visit `http://127.0.0.1:8000/`.

---

## Project Structure

```
djnago-bookmyshow-clone/
├── bookmyseat/          # Project config (settings, root URLs, celery app)
│   ├── celery.py        # Celery task queue configuration
├── movies/              # Core booking app
│   ├── models.py        # Movie, Theater, Seat, Booking, MovieView
│   ├── views.py         # movie_list, theater_list, book_seats, download_ticket
│   ├── pdf.py           # ReportLab PDF ticket generator with embedded QR code
│   ├── tasks.py         # Celery task for async ticket email confirmation
│   ├── utils.py         # Recommendation engine
│   ├── urls.py          # /movies/ routes
│   └── migrations/
├── users/               # Auth app
│   ├── views.py         # home, register, login, profile, reset_password
│   ├── forms.py         # UserRegisterForm, UserUpdateForm
│   └── urls.py          # auth routes
├── templates/
│   ├── home.html
│   ├── movies/
│   │   ├── movie_list.html
│   │   ├── theater_list.html
│   │   └── seat_selection.html
│   └── users/
│       ├── basic.html
│       ├── login.html
│       ├── register.html
│       └── profile.html
└── media/
```

---

## Task 1 — Movie Discovery with Search, Filters and Recommendations

### Search

Full-text search across **movie name**, **cast**, and **description** using combined `Q` objects.

### Filters

All filters are combinable and use optimised Django ORM queries.

| Filter       | Field / Lookup                                                      |
|--------------|---------------------------------------------------------------------|
| Genre        | `Movie.genre` (12 choices)                                          |
| Language     | `Movie.language` (8 choices)                                        |
| City         | `Theater.city` (10 cities)                                          |
| Theater      | `Theater` FK lookup                                                 |
| Release Date | `Movie.release_date` date range (from / to)                         |
| Rating       | `Movie.rating` minimum threshold via range slider                   |
| Show Timing  | `Theater.time__time__range` — Morning / Afternoon / Evening / Night |

### Sorting

| Option            | ORM Strategy                                      |
|-------------------|---------------------------------------------------|
| Most Popular      | Annotated booking count, descending               |
| Newest First      | `release_date` descending                         |
| Highest Rated     | `rating` descending                               |
| Price: Low to High | `price` ascending                               |
| Price: High to Low | `price` descending                              |

### Pagination

9 movies per page using Django's `Paginator` with `get_elided_page_range`. All active filters and sort state are preserved across page navigations.

### Active Filter Pills

Each active filter is shown as a dismissable chip above the movie grid. Clicking a chip removes only that filter via client-side URL manipulation. "Clear All" strips all filters at once.

### Dynamic Movie Count

The result count updates after every filter/search combination and is shown both in the results bar and inside the filter sidebar header.

### Recommendations

**Authenticated users**

1. Collects genres from the user's booking history.
2. Collects genres from the user's recently viewed movies (last 30 `MovieView` entries).
3. Queries movies matching those genres, excluding titles already booked, ranked by booking popularity then rating.
4. Falls back to global popularity if no history exists.

**Anonymous users**

Top movies ranked by booking count then rating.

**View tracking**

Every visit to a theater listing page (`/movies/<id>/theaters`) creates a `MovieView` record, feeding future recommendations.

---

## Task 2 — Automated Ticket Generation and Email Confirmation

### PDF Ticket & Verification QR Code
- **PDF Ticket Generator (`movies/pdf.py`)**: Built using ReportLab (`SimpleDocTemplate`, `TableStyle`, `ParagraphStyle`) with custom brand styling (#1E3A8A blue accent).
- **Dynamic QR Code**: Generated on the fly using `qrcode` library into an in-memory buffer and embedded into the PDF. Contains full verification data: Booking ID, Movie Name, Theater, Screen, Show Timing, Seat Number, Payment Ref, and Verified status.
- **Included Details**: Movie name, genre, language, rating, theater name, city, screen number, show timing, seat number, booking date, ticket price, unique booking ID, and payment reference.

### Asynchronous Email Confirmation with Celery
- **Celery Task (`movies/tasks.py`)**: `@shared_task(bind=True, max_retries=3, default_retry_delay=5, autoretry_for=(Exception,), retry_backoff=True)`.
- **Non-Blocking Dispatch**: Upon successful seat reservation in `book_seats`, `send_ticket_email_task.delay(booking.id)` is invoked. The booking response returns immediately without blocking for SMTP transmission.
- **Automatic Retry Policy**: Retries failed email deliveries automatically up to 3 times with exponential backoff.
- **Graceful Fallback**: If Celery broker/Redis is offline during local evaluation, a non-blocking daemon thread executes the task as a fallback, ensuring the user flow is never disrupted.

### Ticket Download Feature
- **Download Endpoint (`/movies/booking/<id>/ticket/`)**: `@login_required` view `download_ticket` streams the PDF as an attachment (`Content-Disposition: attachment; filename="Ticket_BMS-XXXXXX.pdf"`).
- **Booking History (Profile Page)**: Each card in "Your Bookings" displays the Booking ID badge, Screen, Payment Reference, and a dedicated **"Download Ticket (PDF)"** button.

---

### Database Field Updates (Task 1 & Task 2)

**Movie**

| Field          | Type         | Default  |
|----------------|--------------|----------|
| `genre`        | CharField    | `action` |
| `language`     | CharField    | `hindi`  |
| `release_date` | DateField    | null     |
| `price`        | DecimalField | 200.00   |

**Theater**

| Field    | Type      | Default    |
|----------|-----------|------------|
| `city`   | CharField | `mumbai`   |
| `screen` | CharField | `Screen 1` |

**Booking**

| Field               | Type      | Notes                                  |
|---------------------|-----------|----------------------------------------|
| `booking_id`        | CharField | Unique, auto-generated e.g. `BMS-8F92A1B3` |
| `payment_reference` | CharField | Auto-generated e.g. `PAY-7C2D1E4F9A0B` |

---

## User Flow

```
Home (/)
  └── Recommended Movies (personalised or popular)

Movies (/movies/)
  ├── Search + 7 Filters + 5 Sort modes
  ├── Paginated grid, 9 per page
  └── Recommended for You / Popular Right Now

Movie Theaters (/movies/<id>/theaters)      [records MovieView]
  └── Seat Selection (/movies/theater/<id>/seats/book/)  [login required]
        ├── Triggers non-blocking Celery email task (with retry policy)
        └── Profile (/profile/)
              ├── View Bookings (Booking ID, Screen, Payment Ref)
              └── "Download Ticket (PDF)" button → Ticket_BMS-XXXXXX.pdf
```

---

## Admin Panel

Visit `/admin/` to manage Movies (genre, language, price, release date, poster), Theaters (city, screen, showtime), Seats, Bookings (booking ID, payment ref), and MovieViews.

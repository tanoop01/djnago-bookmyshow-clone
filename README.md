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
│   ├── models.py        # Movie, MoviePoster, Theater, Seat, Booking, Review, MovieView
│   ├── views.py         # movie_list, movie_detail, add_or_edit_review, report_review, theater_list, book_seats, download_ticket
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
│   │   ├── movie_detail.html
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

---

## Task 2 — Automated Ticket Generation and Email Confirmation

### PDF Ticket & Verification QR Code
- **PDF Ticket Generator (`movies/pdf.py`)**: Built using ReportLab (`SimpleDocTemplate`, `TableStyle`, `ParagraphStyle`) with custom brand styling (#1E3A8A blue accent).
- **Dynamic QR Code**: Generated on the fly using `qrcode` library into an in-memory buffer and embedded into the PDF. Contains full verification data: Booking ID, Movie Name, Theater, Screen, Show Timing, Seat Number, Payment Ref, and Verified status.
- **Consolidated Multi-Seat Tickets**: Groups multiple seats booked in a single transaction into a single email and single PDF ticket.

### Asynchronous Email Confirmation with Celery
- **Celery Task (`movies/tasks.py`)**: `@shared_task(bind=True, max_retries=3, default_retry_delay=5, autoretry_for=(Exception,), retry_backoff=True)`.
- **Non-Blocking Dispatch**: Upon successful seat reservation in `book_seats`, background daemon thread triggers `send_ticket_email_task`.
- **Automatic Retry Policy**: Retries failed email deliveries automatically up to 3 times with exponential backoff.

### Ticket Download Feature
- **Download Endpoint (`/movies/booking/<id>/ticket/`)**: `@login_required` view `download_ticket` streams the PDF as an attachment (`Content-Disposition: attachment; filename="Ticket_BMS-XXXXXX.pdf"`).
- **Booking History (Profile Page)**: Each card in "Your Bookings" displays the Booking ID badge, Screen, Payment Reference, and a dedicated **"Download Ticket (PDF)"** button.

---

## Task 3 — Movie Management with Trailer, Reviews and Ratings

### YouTube Trailer Embedding & Multiple Posters
- **YouTube Embed Player**: Converts standard YouTube URLs into secure iframe-ready embed URLs (`https://www.youtube-nocookie.com/embed/VIDEO_ID`).
- **Multiple Posters Gallery**: `MoviePoster` model supporting image uploads and captions displayed as a gallery on movie detail pages and inline in Django Admin.
- **Age Certification & Duration**: Supports certification levels (`U`, `U/A 7+`, `U/A 13+`, `U/A 16+`, `A`) and movie duration in minutes.

### Verified Reviews & Automated Rating Calculations
- **Verified Viewer Authorization**: Only registered users with a confirmed `Booking` for the movie can submit ratings (1–10 stars) and written reviews.
- **Verified Viewer Badge**: Displays a prominent green checkmark badge (`Verified Viewer`) on reviews written by ticket holders.
- **Automated Average Rating**: `Movie.update_average_rating()` automatically calculates and updates the overall average star rating on every review submit, edit, or deletion.
- **Review Editing & Reporting**: Authors can edit their reviews, and users can report inappropriate reviews to administrators with custom report reasons (`is_reported`).

### Recommendations Showcase
- **Similar Movies**: Recommends movies matching the current movie's genre or language.
- **Trending & Recent Releases**: Showcases trending movies ranked by booking activity alongside recently released titles.

---

### Database Fields Overview

**Movie**

| Field               | Type         | Default    | Description                           |
|---------------------|--------------|------------|---------------------------------------|
| `genre`             | CharField    | `action`   | 12 choices                            |
| `language`          | CharField    | `hindi`    | 8 choices                             |
| `release_date`      | DateField    | null       | Release date                          |
| `price`             | DecimalField | 200.00     | Ticket price                          |
| `trailer_url`       | URLField     | null       | YouTube trailer URL                   |
| `duration_mins`     | IntegerField | 120        | Duration in minutes                   |
| `age_certification` | CharField    | `U/A 13+`  | Age rating certification              |

**MoviePoster (new)**

| Field     | Type          | Description                           |
|-----------|---------------|---------------------------------------|
| `movie`   | FK to Movie   | Associated movie                      |
| `image`   | ImageField    | Poster image upload                   |
| `caption` | CharField     | Poster caption                        |

**Review (new)**

| Field                | Type          | Description                           |
|----------------------|---------------|---------------------------------------|
| `user`               | FK to User    | Review author                         |
| `movie`              | FK to Movie   | Movie being reviewed                  |
| `rating`             | IntegerField  | Rating scale 1 to 10                  |
| `comment`            | TextField     | Written review comment                |
| `is_verified_viewer` | BooleanField  | True if user booked a ticket          |
| `is_reported`        | BooleanField  | True if flagged for moderation        |
| `report_reason`      | TextField     | Reason for reporting                  |

---

## User Flow

```
Home (/)
  └── Movie Detail (/movies/<id>/detail/)
        ├── View Poster, Duration, Age Certification, Cast & Description
        ├── Watch Embedded YouTube Trailer
        ├── Browse Photo Gallery
        ├── View Verified Reviews & Ratings
        ├── Submit/Edit Verified Review (requires Booking)
        ├── Report Inappropriate Review
        ├── View Similar & Trending Movies
        └── Book Tickets → Theaters (/movies/<id>/theaters)
              └── Seat Selection (/movies/theater/<id>/seats/book/)
                    ├── Triggers non-blocking email task with PDF ticket
                    └── Profile (/profile/)
                          └── "Download Ticket (PDF)" button
```

---

## Admin Panel

Visit `/admin/` to manage:
- **Movies**: manage details, YouTube trailers, age certification, duration, and `MoviePosterInline` photo gallery.
- **Reviews**: moderate reviews with `is_reported` & `is_verified_viewer` filters, approve reported reviews, or delete inappropriate content.
- **Theaters & Showtimes**: assign city, screen, and showtime schedules.
- **Seats & Bookings**: manage booking records, payment references, and seat availability.

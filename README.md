# BookMySeat – Django BookMyShow Clone

A full-featured movie & event ticket booking application built with Django, PostgreSQL (Render), and deployed on Vercel.

---

## Live URL

> Deploy to Vercel and paste the public URL here.

---

## Admin Credentials

- **Username**: `girish`
- **Password**: `admin123` (Superuser & Staff Access)
- **Admin Dashboard**: `http://127.0.0.1:8000/movies/admin-dashboard/`

---

## Tech Stack

| Layer      | Technology                              |
|------------|-----------------------------------------|
| Backend    | Django 3.2, Python 3.x, Celery          |
| Database   | PostgreSQL (Render) via dj-database-url |
| Task Queue | Celery + Redis (background email delivery) |
| Payments   | Razorpay SDK (Order creation, HMAC-SHA256 verification, Webhooks) |
| PDF & QR   | ReportLab, qrcode                       |
| Frontend   | Bootstrap 4, Vanilla CSS, Vanilla JS    |
| Location   | HTML5 Geolocation, Reverse Geocoding, IP Fallback |
| Deployment | Vercel (serverless Python runtime)      |

---

## Setup and Running Locally

```bash
git clone <repo-url>
cd djnago-bookmyshow-clone

pip install -r requirements.txt

python manage.py migrate

python manage.py seed_seats
python manage.py seed_events

# Start Celery worker (optional for local background processing)
celery -A bookmyseat worker --loglevel=info

python manage.py runserver
```

Visit `http://127.0.0.1:8000/`.

---

## Auto-Detect Location & Expanded 60+ Cities

1. **Auto Detect My Location**:
   - Integrated an **"Auto Detect My City"** button (`<i class="fas fa-crosshairs"></i>`) in the city selection modal.
   - Uses **HTML5 Geolocation** (`navigator.geolocation`) with OpenStreetMap Nominatim reverse geocoding API.
   - Gracefully falls back to **IP Geolocation** (`ipapi.co`) if browser permission is blocked.
2. **60+ All-India Cities Support**:
   - Expanded city database covering Metros, Tier 1, Tier 2, and Tier 3 cities across all Indian states.
   - Includes real-time live search filter inside the city modal.

---

## Complete Multi-Category Support

BookMySeat provides full interactive ticket booking across 5 major categories:

1. 🎬 **Movies**: Full-text search, 7 combinable filters, YouTube trailers, age ratings, verified viewer reviews, live seat selection with 2-minute hold timer, and Razorpay checkout.
2. 🎤 **Live Events**: Standup comedy specials, food festivals, tech conclaves.
3. 🎭 **Plays & Theater**: Broadway musicals, satirical theater, classical plays.
4. ⚽ **Sports Matches**: T20 cricket finals, football derbies, league matches.
5. 🎵 **Music Studio & Concerts**: Live symphony concerts, rock bands, EDM music festivals.

---

## Project Structure

```
djnago-bookmyshow-clone/
├── bookmyseat/          # Project config (settings, root URLs, celery app)
│   ├── celery.py        # Celery task queue configuration
├── movies/              # Core booking app
│   ├── models.py        # Movie, MoviePoster, Theater, Seat, Booking, Payment, Review, MovieView, Event, EventBooking
│   ├── views.py         # movie_list, movie_detail, add_or_edit_review, report_review, theater_list, book_seats, live_seat_availability, cancel_or_modify_reservation, payment_checkout, payment_verify, payment_retry, payment_webhook, download_ticket, admin_dashboard, export_analytics_csv, event_list, event_detail, book_event, download_event_ticket
│   ├── pdf.py           # ReportLab PDF ticket generator with embedded QR code
│   ├── tasks.py         # Celery task for async ticket email confirmation
│   ├── utils.py         # Recommendation engine
│   ├── urls.py          # /movies/ routes
│   └── management/commands/
│       ├── seed_seats.py
│       └── seed_events.py
├── users/               # Auth app
│   ├── views.py         # home, register, login_view, profile, reset_password
│   ├── forms.py         # UserRegisterForm, UserUpdateForm
│   └── urls.py          # auth routes
├── templates/
│   ├── home.html
│   ├── movies/
│   │   ├── movie_list.html
│   │   ├── movie_detail.html
│   │   ├── theater_list.html
│   │   ├── seat_selection.html
│   │   ├── payment_checkout.html
│   │   ├── payment_failed.html
│   │   ├── admin_dashboard.html
│   │   ├── event_list.html
│   │   └── event_detail.html
│   └── users/
│       ├── basic.html
│       ├── login.html
│       ├── register.html
│       └── profile.html
└── media/
```

---

## User Flow

```
Home (/)  [Auto-Detect City Modal]
  ├── Movies (/movies/) ➔ Detail ➔ Theater ➔ Seat Selection (3s Live Polling) ➔ Checkout (2m Hold) ➔ Razorpay Payment ➔ PDF Ticket (QR Code)
  ├── Live Events (/movies/events/?category=events) ➔ Detail ➔ Ticket Selection ➔ Checkout ➔ Razorpay Payment ➔ PDF Ticket
  ├── Plays & Theater (/movies/events/?category=plays) ➔ Detail ➔ Ticket Selection ➔ Checkout ➔ Razorpay Payment ➔ PDF Ticket
  ├── Sports Matches (/movies/events/?category=sports) ➔ Detail ➔ Ticket Selection ➔ Checkout ➔ Razorpay Payment ➔ PDF Ticket
  └── Music Concerts (/movies/events/?category=music) ➔ Detail ➔ Ticket Selection ➔ Checkout ➔ Razorpay Payment ➔ PDF Ticket

Admin Access (/movies/admin-dashboard/)  [Staff Only]
  ├── Revenue KPI Metrics (Daily, Weekly, Monthly, Yearly)
  ├── Theater Occupancy % & Revenue Breakdown
  ├── Top Movies & Theaters Leaderboards
  ├── Peak Booking Hours & User Growth
  └── Export CSV Report
```

# BookMySeat – Django BookMyShow Clone

BookMySeat is a comprehensive, production-ready full-stack entertainment & ticket booking web application built with Django, Python, Bootstrap 4, and PostgreSQL. It delivers real-time movie & live event ticket reservations, interactive seat selection with hold timers, online Razorpay payment processing, automated PDF ticket generation with embedded QR codes, location auto-detection across 60+ Indian cities, and an executive Business Insights Admin Dashboard.

---

## Quick Start & Running Locally

### 1. Prerequisites
- Python 3.9+ installed
- Git installed

### 2. Installation Steps

```bash
# Clone the repository
git clone https://github.com/your-username/djnago-bookmyshow-clone.git
cd djnago-bookmyshow-clone

# Create and activate virtual environment (optional)
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables file
cp .env.example .env

# Apply database migrations
python manage.py migrate

# Seed sample seats and multi-category live events
python manage.py seed_seats
python manage.py seed_events

# Run the Django development server
python manage.py runserver
```

Open your browser and visit: **`http://127.0.0.1:8000/`**

---

## Admin Credentials

- **Admin Dashboard**: `http://127.0.0.1:8000/movies/admin-dashboard/`
- **Username**: `girish`
- **Password**: `admin123` *(Staff & Superuser access)*

---

## Key Features

### 🎬 1. Movie Discovery & Advanced Filtering
- **Multi-Filter System**: Combine genre, language, city, theater, minimum rating, release date range, and showtime window filters simultaneously.
- **Search & Sort**: Real-time search across movie titles, cast members, and descriptions with popularity/newest/rating/price sorting.
- **Trailers & Reviews**: Embedded YouTube trailer player, CBFC age certification badges (`U`, `U/A 13+`, `A`), and verified viewer review system.

### 🎟️ 2. Smart Seat Locking & Concurrency Protection
- **Live Seat Map**: 3-second live availability polling (`/movies/theater/<id>/seats/live/`).
- **2-Minute Temporary Reservation Timer**: Atomic row-level locking (`select_for_update`) with automatic expiration to prevent double-booking.
- **Modify & Retry**: Seamless seat reservation release and payment retry workflow.

### 🎤 3. Multi-Category Entertainment Booking
Full ticket booking flow across 5 categories:
1. **Movies**: Interactive theater & seat selection.
2. **Live Events**: Standup comedy specials, tech conclaves.
3. **Plays & Theater**: Classical & Broadway-style musicals.
4. **Sports Matches**: Cricket T20 finals, football derbies.
5. **Music Studio & Concerts**: Symphony orchestra, rock bands, EDM festivals.

### 💳 4. Razorpay Payments & Automated PDF Tickets
- **Razorpay Integration**: Server-side HMAC-SHA256 signature verification, order creation, idempotency checks, and webhook handling.
- **Automated PDF Ticket**: ReportLab PDF generator featuring booking details and embedded QR codes readable by event scanners.

### 📍 5. Auto-Detect Location & 60+ Indian Cities
- **Auto-Detect My Location**: Uses HTML5 Geolocation (`navigator.geolocation`) with OpenStreetMap Nominatim reverse-geocoding, falling back gracefully to IP-location (`ipapi.co`).
- **Navbar Dropdown**: Compact dropdown featuring a live search bar and 60+ supported Indian cities across all states.

### 📊 6. Executive Business Insights Admin Dashboard
- **KPI Metrics**: Daily, Weekly, Monthly, Yearly, and custom date range revenue aggregations.
- **Analytics & Reports**: Theater occupancy %, top-booked movies, peak booking hour distribution, user growth tracking, and one-click CSV export (`/movies/admin-dashboard/export-csv/`).
- **Database Optimization**: 19 database indexes on high-frequency query columns (`Booking`, `Seat`, `Movie`, `Theater`, `Review`, `Payment`).

---

## Tech Stack & Dependencies

| Component            | Technology / Library                                        |
|----------------------|-------------------------------------------------------------|
| **Framework**        | Django 3.2.19                                               |
| **Language**         | Python 3.9+                                                 |
| **Database**         | PostgreSQL (Production) / SQLite (Development)              |
| **ORMs & Drivers**   | `dj-database-url`, `psycopg2-binary`                       |
| **Task Queue**       | Celery + Redis (Background email delivery)                  |
| **Payments**         | `razorpay` SDK                                              |
| **Document & QR**    | `reportlab`, `qrcode`, `Pillow`                             |
| **Frontend**         | Bootstrap 4, Vanilla CSS, JavaScript, FontAwesome 5         |
| **Location API**     | HTML5 Geolocation, OpenStreetMap Nominatim API, IP-API      |

---

## Project Structure

```
djnago-bookmyshow-clone/
├── .env                 # Local environment secrets (git-ignored)
├── .env.example         # Environment template for deployment
├── .gitignore           # Git ignore patterns
├── requirements.txt     # Dependency requirements
├── vercel.json          # Vercel serverless deployment config
├── manage.py            # Django CLI entrypoint
├── bookmyseat/          # Project configuration
│   ├── settings.py      # Production settings & environment variables
│   ├── urls.py          # Master routing table
│   └── wsgi.py          # WSGI application entrypoint
├── movies/              # Primary booking application
│   ├── models.py        # Movie, Theater, Seat, Booking, Payment, Review, Event, EventBooking
│   ├── views.py         # Catalog, Seat Locking, Payment, Admin Dashboard, CSV Export, Event views
│   ├── pdf.py           # ReportLab PDF ticket generator with embedded QR code
│   ├── tasks.py         # Async Celery email notification task
│   ├── urls.py          # App routes
│   └── management/commands/
│       ├── seed_seats.py   # Populates theaters and seat layout
│       └── seed_events.py  # Populates live events and concerts
├── users/               # Authentication application
│   ├── views.py         # Home, Register, Login, Profile, Password Reset
│   └── urls.py          # Auth routes
└── templates/           # HTML templates
    ├── home.html
    ├── movies/          # Movie & Event templates
    └── users/           # Auth & Profile templates
```

---

## Environment Variables Reference (`.env`)

```env
# Django Core Settings
SECRET_KEY=your-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,.vercel.app

# Database Connection (Leave empty for local SQLite)
DATABASE_URL=postgres://user:password@hostname:5432/dbname

# Razorpay Credentials (Test Keys)
RAZORPAY_KEY_ID=rzp_test_TLk8pA8d25h1Em
RAZORPAY_KEY_SECRET=T02goY9Sb582m7tE6kNe0q1Z
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

# Email Delivery Configuration (Gmail SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=your_email@gmail.com

# Celery Task Queue
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

---

## Route Overview

| Route | View Method | Description |
|-------|-------------|-------------|
| `/` | `users.views.home` | Homepage rendering recommended movies & live event cards |
| `/movies/` | `movies.views.movie_list` | Movie catalog with 7 filters, search, and sorting |
| `/movies/<id>/detail/` | `movies.views.movie_detail` | Movie detail view with trailers and verified reviews |
| `/movies/<id>/theaters` | `movies.views.theater_list` | Showtimes & date picker |
| `/movies/theater/<id>/seats/book/` | `movies.views.book_seats` | Seat selection map with 2-min lock timer |
| `/movies/events/` | `movies.views.event_list` | Non-movie categories (Events, Plays, Sports, Concerts) |
| `/movies/events/<id>/detail/` | `movies.views.event_detail` | Event details and pass quantity selector modal |
| `/movies/payment/checkout/<id>/` | `movies.views.payment_checkout` | Razorpay checkout interface |
| `/movies/admin-dashboard/` | `movies.views.admin_dashboard` | Executive business insights dashboard |
| `/movies/admin-dashboard/export-csv/` | `movies.views.export_analytics_csv` | CSV analytics export |
| `/profile/` | `users.views.profile` | User account settings and booking history tabs |

---

## License & Maintenance

Developed for BookMySeat. All rights reserved.

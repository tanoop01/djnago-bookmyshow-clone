# BookMySeat – Django BookMyShow Clone

A full-featured movie ticket booking application built with Django, PostgreSQL (Render), and deployed on Vercel.

---

## Live URL

> Deploy to Vercel and paste the public URL here.

---

## Tech Stack

| Layer      | Technology                              |
|------------|-----------------------------------------|
| Backend    | Django 3.2, Python 3.x                  |
| Database   | PostgreSQL (Render) via dj-database-url |
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

python manage.py runserver
```

Visit `http://127.0.0.1:8000/`.

---

## Project Structure

```
djnago-bookmyshow-clone/
├── bookmyseat/          # Project config (settings, root URLs)
├── movies/              # Core booking app
│   ├── models.py        # Movie, Theater, Seat, Booking, MovieView
│   ├── views.py         # movie_list, theater_list, book_seats
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

### New Database Fields

**Movie**

| Field          | Type         | Default  |
|----------------|--------------|----------|
| `genre`        | CharField    | `action` |
| `language`     | CharField    | `hindi`  |
| `release_date` | DateField    | null     |
| `price`        | DecimalField | 200.00   |

**Theater**

| Field  | Type      | Default  |
|--------|-----------|----------|
| `city` | CharField | `mumbai` |

**MovieView (new)**

| Field         | Type                   |
|---------------|------------------------|
| `user`        | FK to User (nullable)  |
| `movie`       | FK to Movie            |
| `session_key` | CharField (nullable)   |
| `viewed_at`   | DateTimeField (auto)   |

---

### ORM Optimisations

- `distinct()` is applied only when a filter joins through `theaters` (city, theater, show timing) to prevent duplicate movie rows.
- `Count('booking', distinct=True)` prevents inflated counts when `distinct()` is also active.
- `get_elided_page_range` handles large page ranges without rendering all page numbers.
- Recommendation sub-queries operate on pre-fetched ID lists, avoiding N+1 patterns.

---

## Responsive Design

- Filter sidebar collapses to a full-width toggle button on screens narrower than 992 px.
- Movie grid: 3 columns (desktop) → 2 columns (tablet) → 1 column (mobile).

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
        └── Profile (/profile/)             [shows booking history]
```

---

## Admin Panel

Visit `/admin/` to manage Movies (genre, language, price, release date, poster), Theaters (city, showtime), Seats, Bookings, and MovieViews.

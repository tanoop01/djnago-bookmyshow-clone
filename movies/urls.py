from django.urls import path
from . import views

urlpatterns = [
    path('', views.movie_list, name='movie_list'),
    path('set-city/', views.set_city, name='set_city'),
    path('<int:movie_id>/detail/', views.movie_detail, name='movie_detail'),
    path('<int:movie_id>/review/submit/', views.add_or_edit_review, name='add_or_edit_review'),
    path('review/<int:review_id>/report/', views.report_review, name='report_review'),
    path('<int:movie_id>/theaters', views.theater_list, name='theater_list'),
    path('theater/<int:theater_id>/seats/book/', views.book_seats, name='book_seats'),
    path('theater/<int:theater_id>/seats/live/', views.live_seat_availability, name='live_seat_availability'),

    # Events, Plays, Sports, Concerts routes
    path('events/', views.event_list, name='event_list'),
    path('events/<int:event_id>/detail/', views.event_detail, name='event_detail'),
    path('events/<int:event_id>/book/', views.book_event, name='book_event'),
    path('events/booking/<int:booking_id>/ticket/', views.download_event_ticket, name='download_event_ticket'),

    # Payment & Checkout routes
    path('payment/checkout/<int:payment_id>/', views.payment_checkout, name='payment_checkout'),
    path('payment/verify/', views.payment_verify, name='payment_verify'),
    path('payment/retry/<int:payment_id>/', views.payment_retry, name='payment_retry'),
    path('payment/modify/<int:payment_id>/', views.cancel_or_modify_reservation, name='cancel_or_modify_reservation'),
    path('payment/webhook/', views.payment_webhook, name='payment_webhook'),
    path('booking/<int:booking_id>/ticket/', views.download_ticket, name='download_ticket'),

    # Admin Dashboard routes
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/export-csv/', views.export_analytics_csv, name='export_analytics_csv'),
]
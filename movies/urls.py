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
    path('booking/<int:booking_id>/ticket/', views.download_ticket, name='download_ticket'),
]
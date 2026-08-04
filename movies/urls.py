from django.urls import path
from . import views

urlpatterns = [
    path('', views.movie_list, name='movie_list'),
    path('set-city/', views.set_city, name='set_city'),
    path('<int:movie_id>/theaters', views.theater_list, name='theater_list'),
    path('theater/<int:theater_id>/seats/book/', views.book_seats, name='book_seats'),
    path('booking/<int:booking_id>/ticket/', views.download_ticket, name='download_ticket'),
]
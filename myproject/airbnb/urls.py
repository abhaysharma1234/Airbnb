from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('properties/', views.property_list, name='property_list'),
    path('property/<int:pk>/', views.property_detail, name='property_detail'),
    path('property/new/', views.property_create, name='property_create'),
    path('property/<int:pk>/edit/', views.property_update, name='property_update'),
    path('property/<int:pk>/delete/', views.property_delete, name='property_delete'),
    path('property/<int:pk>/book/', views.book_property, name='book_property'),
    path('bookings/', views.my_bookings, name='my_bookings'),
    path('host/bookings/', views.host_bookings, name='host_bookings'),
    path('property/<int:pk>/like/', views.like_property, name='like_property'),
    path('property/<int:pk>/review/', views.add_review, name='add_review'),
    path('property/<int:pk>/review/<int:review_id>/reply/', views.reply_review, name='reply_review'),
    path('property/<int:pk>/reply/<int:reply_id>/delete/', views.delete_reply, name='delete_reply'),
    path('booking/<int:booking_id>/update-status/', views.update_booking_status, name='update_booking_status'),
    path('search/', views.search_properties, name='search_properties'),
        path('signup/', views.signup, name='signup'),
    path('my-properties/', views.my_properties, name='my_properties'),
    path('liked-properties/', views.liked_properties, name='liked_properties'),
    path('host/liked-properties/', views.host_liked_properties, name='host_liked_properties'),
]

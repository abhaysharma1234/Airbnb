from django.contrib import admin
from .models import Property, Booking, Review, Like


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['title', 'host', 'city', 'property_type', 'price_per_night', 'is_available', 'created_at']
    list_filter = ['property_type', 'is_available', 'created_at']
    search_fields = ['title', 'city', 'country']
    readonly_fields = ['created_at']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['property', 'guest', 'check_in', 'check_out', 'total_price', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['property__title', 'guest__username']
    readonly_fields = ['created_at']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['property', 'guest', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['property__title', 'guest__username', 'comment']
    readonly_fields = ['created_at']


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['property', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['property__title', 'user__username']
    readonly_fields = ['created_at']

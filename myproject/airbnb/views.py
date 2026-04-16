from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import PropertyForm, BookingForm, ReviewForm, ReplyReviewForm, CustomUserCreationForm
from django.contrib import messages
from django.db.models import Q, Avg
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Property, Booking, Review, Like


def home(request):
    properties = Property.objects.filter(is_available=True)
    
    # Get search parameters
    query = request.GET.get('q', '')
    city = request.GET.get('city', '')
    property_type = request.GET.get('property_type', '')
    
    # Apply filters
    if query:
        properties = properties.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(city__icontains=query) |
            Q(country__icontains=query)
        )
    
    if city:
        properties = properties.filter(city__icontains=city)
    
    if property_type:
        properties = properties.filter(property_type=property_type)
    
    # If no search parameters, show featured properties
    if not query and not city and not property_type:
        featured_properties = Property.objects.filter(is_available=True)[:6]
        
        # Get liked properties for authenticated users
        liked_properties = []
        if request.user.is_authenticated:
            liked_properties = Like.objects.filter(user=request.user).values_list('property_id', flat=True)
        
        return render(request, 'airbnb/home.html', {
            'featured_properties': featured_properties,
            'liked_properties': liked_properties,
            'query': query,
            'city': city,
            'property_type': property_type
        })
    
    # If search parameters exist, show paginated results
    paginator = Paginator(properties, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get liked properties for authenticated users
    liked_properties = []
    if request.user.is_authenticated:
        liked_properties = Like.objects.filter(user=request.user).values_list('property_id', flat=True)
    
    return render(request, 'airbnb/home.html', {
        'page_obj': page_obj,
        'liked_properties': liked_properties,
        'query': query,
        'city': city,
        'property_type': property_type
    })


def property_list(request):
    properties = Property.objects.filter(is_available=True)
    
    # Get search parameters
    query = request.GET.get('q', '')
    city = request.GET.get('city', '')
    property_type = request.GET.get('property_type', '')
    
    # Apply filters
    if query:
        properties = properties.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(city__icontains=query) |
            Q(country__icontains=query)
        )
    
    if city:
        properties = properties.filter(city__icontains=city)
    
    if property_type:
        properties = properties.filter(property_type=property_type)
    
    paginator = Paginator(properties, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get liked properties for authenticated users
    liked_properties = []
    if request.user.is_authenticated:
        liked_properties = Like.objects.filter(user=request.user).values_list('property_id', flat=True)
    
    return render(request, 'airbnb/property_list.html', {
        'page_obj': page_obj,
        'liked_properties': liked_properties,
        'query': query,
        'city': city,
        'property_type': property_type
    })


def property_detail(request, pk):
    property = get_object_or_404(Property, pk=pk)
    # Get only top-level reviews (not replies)
    reviews = property.reviews.filter(parent=None).order_by('-created_at')
    
    is_liked = False
    can_review = False
    has_reviewed = False
    
    if request.user.is_authenticated:
        is_liked = Like.objects.filter(property=property, user=request.user).exists()
        
        # Check if user can review
        has_booked = Booking.objects.filter(
            property=property,
            guest=request.user,
            status__in=['confirmed', 'completed']
        ).exists()
        
        has_reviewed = Review.objects.filter(property=property, guest=request.user, parent=None).exists()
        can_review = has_booked and not has_reviewed
    
    return render(request, 'airbnb/property_detail.html', {
        'property': property,
        'reviews': reviews,
        'is_liked': is_liked,
        'can_review': can_review,
        'has_reviewed': has_reviewed
    })


@login_required
def property_create(request):
    if not request.user.is_host():
        messages.error(request, 'Only hosts can add properties!')
        return redirect('home')
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            property = form.save(commit=False)
            property.host = request.user
            property.save()
            messages.success(request, 'Property listed successfully!')
            return redirect('property_detail', pk=property.pk)
    else:
        form = PropertyForm()
    return render(request, 'airbnb/property_form.html', {'form': form, 'title': 'Add Property'})


@login_required
def property_update(request, pk):
    property = get_object_or_404(Property, pk=pk)
    if property.host != request.user:
        messages.error(request, 'You can only edit your own properties!')
        return redirect('property_detail', pk=pk)
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, instance=property)
        if form.is_valid():
            form.save()
            messages.success(request, 'Property updated successfully!')
            return redirect('property_detail', pk=property.pk)
    else:
        form = PropertyForm(instance=property)
    return render(request, 'airbnb/property_form.html', {'form': form, 'title': 'Edit Property'})


@login_required
def property_delete(request, pk):
    property = get_object_or_404(Property, pk=pk)
    if property.host != request.user:
        messages.error(request, 'You can only delete your own properties!')
        return redirect('property_detail', pk=pk)
    
    if request.method == 'POST':
        property.delete()
        messages.success(request, 'Property deleted successfully!')
        return redirect('my_properties')
    return render(request, 'airbnb/property_confirm_delete.html', {'property': property})


@login_required
def book_property(request, pk):
    property = get_object_or_404(Property, pk=pk)
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.property = property
            booking.guest = request.user
            
            # Check for overlapping bookings
            overlapping = Booking.objects.filter(
                property=property,
                status__in=['pending', 'confirmed'],
                check_in__lt=booking.check_out,
                check_out__gt=booking.check_in
            ).exists()
            
            if overlapping:
                messages.error(request, 'Property is already booked for these dates!')
            else:
                booking.save()
                messages.success(request, 'Booking request sent successfully!')
                return redirect('my_bookings')
    else:
        form = BookingForm()
    
    return render(request, 'airbnb/book_property.html', {'form': form, 'property': property})


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(guest=request.user).order_by('-created_at')
    return render(request, 'airbnb/my_bookings.html', {'bookings': bookings})


@login_required
def host_bookings(request):
    if not request.user.is_host():
        messages.error(request, 'Only hosts can manage bookings!')
        return redirect('home')
    
    properties = Property.objects.filter(host=request.user)
    bookings = Booking.objects.filter(property__in=properties).order_by('-created_at')
    return render(request, 'airbnb/host_bookings.html', {'bookings': bookings})


@login_required
def update_booking_status(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(Booking, pk=booking_id)
        
        # Check if user is the host of this property
        if booking.property.host != request.user:
            return JsonResponse({'success': False, 'error': 'Unauthorized'})
        
        # Try to get status from JSON data first, then from POST
        import json
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                status = data.get('status')
            else:
                status = request.POST.get('status')
        except (ValueError, json.JSONDecodeError):
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        
        if status in ['confirmed', 'cancelled', 'completed']:
            booking.status = status
            booking.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid status'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def like_property(request, pk):
    property = get_object_or_404(Property, pk=pk)
    like, created = Like.objects.get_or_create(property=property, user=request.user)
    
    if not created:
        like.delete()
        is_liked = False
    else:
        is_liked = True
    
    return JsonResponse({'is_liked': is_liked, 'likes_count': property.likes.count()})


@login_required
def add_review(request, pk):
    property = get_object_or_404(Property, pk=pk)
    
    # Check if user has booked the property
    has_booked = Booking.objects.filter(
        property=property,
        guest=request.user,
        status__in=['confirmed', 'completed']
    ).exists()
    
    if not has_booked:
        messages.error(request, 'You can only review properties you have booked!')
        return redirect('property_detail', pk=pk)
    
    # Check if user has already reviewed
    if Review.objects.filter(property=property, guest=request.user, parent=None).exists():
        messages.error(request, 'You have already reviewed this property!')
        return redirect('property_detail', pk=pk)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.property = property
            review.guest = request.user
            review.save()
            messages.success(request, 'Your review has been added successfully!')
            return redirect('property_detail', pk=pk)
    else:
        form = ReviewForm()
    
    return render(request, 'airbnb/add_review.html', {'form': form, 'property': property})


@login_required
def reply_review(request, pk, review_id):
    property = get_object_or_404(Property, pk=pk)
    parent_review = get_object_or_404(Review, id=review_id, property=property)
    
    # Check if user has booked the property (can reply if they've stayed there)
    has_booked = Booking.objects.filter(
        property=property,
        guest=request.user,
        status__in=['confirmed', 'completed']
    ).exists()
    
    if not has_booked:
        messages.error(request, 'You can only reply to reviews if you have booked this property!')
        return redirect('property_detail', pk=pk)
    
    if request.method == 'POST':
        form = ReplyReviewForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.property = property
            reply.guest = request.user
            reply.parent = parent_review
            # Use the rating of the top-level review (main review)
            if parent_review.parent:
                reply.rating = parent_review.parent.rating
            else:
                reply.rating = parent_review.rating
            reply.save()
            messages.success(request, 'Your reply has been added successfully!')
            return redirect('property_detail', pk=pk)
    else:
        form = ReplyReviewForm()
    
    return render(request, 'airbnb/reply_review.html', {
        'form': form, 
        'property': property, 
        'parent_review': parent_review
    })


@login_required
def delete_reply(request, pk, reply_id):
    property = get_object_or_404(Property, pk=pk)
    reply = get_object_or_404(Review, id=reply_id, property=property)
    
    # Check if user is the author of the reply
    if reply.guest != request.user:
        messages.error(request, 'You can only delete your own replies!')
        return redirect('property_detail', pk=pk)
    
    # Check if it's actually a reply (has a parent)
    if not reply.parent:
        messages.error(request, 'You can only delete replies, not main reviews!')
        return redirect('property_detail', pk=pk)
    
    if request.method == 'POST':
        reply.delete()
        messages.success(request, 'Your reply has been deleted successfully!')
        return redirect('property_detail', pk=pk)
    
    return render(request, 'airbnb/delete_reply.html', {
        'property': property, 
        'reply': reply
    })


def search_properties(request):
    query = request.GET.get('q', '')
    city = request.GET.get('city', '')
    property_type = request.GET.get('property_type', '')
    
    properties = Property.objects.filter(is_available=True)
    
    if query:
        properties = properties.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(city__icontains=query) |
            Q(country__icontains=query)
        )
    
    if city:
        properties = properties.filter(city__icontains=city)
    
    if property_type:
        properties = properties.filter(property_type=property_type)
    
    paginator = Paginator(properties, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'airbnb/property_list.html', {
        'page_obj': page_obj,
        'query': query,
        'city': city,
        'property_type': property_type,
    })


def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})




@login_required
def my_properties(request):
    if not request.user.is_host():
        messages.error(request, 'Only hosts can view their properties!')
        return redirect('home')
    
    properties = Property.objects.filter(host=request.user).order_by('-created_at')
    return render(request, 'airbnb/my_properties.html', {'properties': properties})


@login_required
def liked_properties(request):
    liked = Like.objects.filter(user=request.user).select_related('property')
    # Extract the property objects from the likes
    properties = [like.property for like in liked]
    
    # Check if user is host and add host-specific data
    is_host = request.user.is_host()
    host_properties = []
    if is_host:
        host_properties = Property.objects.filter(host=request.user)
    
    return render(request, 'airbnb/liked_properties.html', {
        'liked_properties': properties,
        'is_host': is_host,
        'host_properties': host_properties
    })


@login_required
def host_liked_properties(request):
    if not request.user.is_host():
        messages.error(request, 'This feature is only available for hosts!')
        return redirect('home')
    
    # Get all properties owned by the host
    host_properties = Property.objects.filter(host=request.user)
    
    # Get all likes for the host's properties
    likes = Like.objects.filter(property__in=host_properties).select_related('property', 'user').order_by('-created_at')
    
    return render(request, 'airbnb/host_liked_properties.html', {
        'likes': likes,
        'host_properties': host_properties
    })

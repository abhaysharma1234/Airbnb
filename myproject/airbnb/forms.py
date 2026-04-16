from django import forms
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from .models import Property, Booking, Review, User


class CustomUserCreationForm(UserCreationForm):
    ROLE_CHOICES = [
        ('guest', 'Guest'),
        ('host', 'Host'),
    ]
    
    role = forms.ChoiceField(choices=ROLE_CHOICES, required=True, label='I am a')
    phone = forms.CharField(max_length=20, required=False, label='Phone Number')
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role', 'phone')


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            'title', 'description', 'address', 'city', 'state', 'country',
            'property_type', 'bedrooms', 'bathrooms', 'max_guests',
            'price_per_night', 'image', 'is_available'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'price_per_night': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'max_guests': forms.NumberInput(attrs={'min': '1', 'max': '20'}),
        }


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['check_in', 'check_out']
        widgets = {
            'check_in': forms.DateInput(attrs={'type': 'date'}),
            'check_out': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')
        
        if check_in and check_out:
            if check_in >= check_out:
                raise forms.ValidationError('Check-out date must be after check-in date.')
            
            if check_in < timezone.now().date():
                raise forms.ValidationError('Check-in date cannot be in the past.')
        
        return cleaned_data


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Share your experience...'})
        }

class ReplyReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write your reply...'})
        }

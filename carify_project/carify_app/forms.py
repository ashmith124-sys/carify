from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import modelformset_factory
from .models import Product, ProductMedia, Service, Category

class BuyerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Enter a working email address for OTP verification.')

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('email',)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_active = False  # Deactivate until OTP is verified
        if commit:
            user.save()
        return user

class SellerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Enter your business email address.')
    shop_name = forms.CharField(max_length=100, required=True)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('email',)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_active = False  # Deactivate until OTP is verified
        if commit:
            user.save()
        return user

class OTPVerifyForm(forms.Form):
    otp_code = forms.CharField(max_length=6, min_length=6, widget=forms.TextInput(attrs={'placeholder': '000000', 'class': 'otp-input'}))

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'parent']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'cg-input', 'placeholder': 'Category description...'}),
            'name': forms.TextInput(attrs={'class': 'cg-input', 'placeholder': 'Category Name'}),
            'parent': forms.Select(attrs={'class': 'cg-input'}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'quantity', 'price', 'image', 'category']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'description', 'price', 'image', 'video', 'contact_info', 'category']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'cg-input', 'placeholder': 'Describe the ritual...'}),
            'name': forms.TextInput(attrs={'class': 'cg-input', 'placeholder': 'Protocol Name'}),
            'price': forms.NumberInput(attrs={'class': 'cg-input', 'placeholder': 'Starting Price'}),
            'contact_info': forms.TextInput(attrs={'class': 'cg-input', 'placeholder': 'Contact details...'}),
            'category': forms.Select(attrs={'class': 'cg-input'}),
        }

ProductMediaFormset = modelformset_factory(
    ProductMedia,
    fields=('media_type', 'image', 'video', 'caption', 'sort_order'),
    extra=3,
    can_delete=True,
    widgets={
        'caption': forms.TextInput(attrs={'placeholder': 'Optional caption'}),
    }
)

from django.contrib.auth.models import User
from .models import SellerProfile

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'cg-input', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'cg-input', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'cg-input', 'placeholder': 'Email Address'}),
        }

class SellerProfileForm(forms.ModelForm):
    class Meta:
        model = SellerProfile
        fields = ['shop_name', 'description', 'logo']
        widgets = {
            'shop_name': forms.TextInput(attrs={'class': 'cg-input', 'placeholder': 'Shop Name'}),
            'description': forms.Textarea(attrs={'class': 'cg-input', 'placeholder': 'Shop Description', 'rows': 4}),
            'logo': forms.ClearableFileInput(attrs={'class': 'cg-input'}),
        }

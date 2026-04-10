from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import modelformset_factory
from .models import Product, ProductMedia

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

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'quantity', 'price', 'image', 'category']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
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

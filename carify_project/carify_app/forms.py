from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import modelformset_factory
from .models import Product, ProductMedia

class SellerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Enter a working email address.')

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('email',)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

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

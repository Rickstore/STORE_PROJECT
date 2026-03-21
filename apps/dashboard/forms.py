from django import forms
from django.forms import inlineformset_factory
from apps.catalog.models import Product, Category, ProductSpecification, ProductVariant, Color, Capacity
from apps.users.models import CustomUser

class ColorForm(forms.ModelForm):
    class Meta:
        model = Color
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]', 'placeholder': 'Ex: Titane'}),
            'code': forms.TextInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]', 'placeholder': 'Ex: #C0C0C0'}),
        }

class CapacityForm(forms.ModelForm):
    class Meta:
        model = Capacity
        fields = ['value']
        widgets = {
            'value': forms.TextInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]', 'placeholder': 'Ex: 128 GB'}),
        }

class ProductSpecificationForm(forms.ModelForm):
    class Meta:
        model = ProductSpecification
        fields = ['name', 'value']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]', 'placeholder': 'Ex: Processeur'}),
            'value': forms.TextInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]', 'placeholder': 'Ex: A17 Pro'}),
        }

ProductSpecificationFormSet = inlineformset_factory(
    Product, ProductSpecification,
    form=ProductSpecificationForm,
    extra=1, can_delete=True
)

class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['color', 'capacity', 'price', 'stock']
        widgets = {
            'color': forms.Select(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'}),
            'capacity': forms.Select(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'}),
            'price': forms.NumberInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'}),
            'stock': forms.NumberInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'}),
        }

ProductVariantFormSet = inlineformset_factory(
    Product, ProductVariant,
    form=ProductVariantForm,
    extra=1, can_delete=True
)

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'brand', 'price', 'stock', 'description', 'image', 'available_colors', 'available_capacities', 'is_active', 'is_second_hand', 'fast_deal']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'}),
            'category': forms.Select(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'}),
            'brand': forms.TextInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]', 'placeholder': 'Ex: Apple, Samsung...'}),
            'price': forms.NumberInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'}),
            'stock': forms.NumberInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'}),
            'description': forms.Textarea(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]', 'rows': 4}),
            'image': forms.FileInput(attrs={'class': 'w-full text-xs text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-[#8CC63F]/10 file:text-[#8CC63F] hover:file:bg-[#8CC63F]/20'}),
            'available_colors': forms.CheckboxSelectMultiple(attrs={'class': 'flex flex-wrap gap-4'}),
            'available_capacities': forms.CheckboxSelectMultiple(attrs={'class': 'flex flex-wrap gap-4'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-[#8CC63F] focus:ring-[#8CC63F]'}),
            'is_second_hand': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-[#8CC63F] focus:ring-[#8CC63F]'}),
            'fast_deal': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-[#8CC63F] focus:ring-[#8CC63F]'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'}),
            'slug': forms.TextInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]', 'placeholder': 'ex: smartphones'}),
            'description': forms.Textarea(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]', 'rows': 2}),
            'image': forms.FileInput(attrs={'class': 'w-full text-xs text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-[#8CC63F]/10 file:text-[#8CC63F] hover:file:bg-[#8CC63F]/20'}),
        }


class LivreurCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'}), label="Mot de passe")
    city = forms.CharField(max_length=100, required=False, label="Ville (Zone de livraison)", widget=forms.TextInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'}))
    vehicle_type = forms.CharField(max_length=50, required=False, label="Type de véhicule", widget=forms.TextInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'}))
    is_available = forms.BooleanField(initial=True, required=False, label="Disponible", widget=forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-[#8CC63F] focus:ring-[#8CC63F]'}))

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'}),
            'phone': forms.TextInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]', 'placeholder': 'Ex: 670000000'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        import re
        if phone and not re.match(r'^6[25789]\d{7}$', phone.replace(' ', '')):
            raise forms.ValidationError("Veuillez entrer un numéro de téléphone camerounais valide (ex: 67xxxxxxx).")
        return phone.replace(' ', '') if phone else phone

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password') or "0000"
        user.set_password(password)
        user.role = 'livreur'
        user.is_staff = True  # Donner l'accès au panel si besoin ou juste le flag
        user.must_change_password = True  # Force password change on first login
        if commit:
            user.save()
            from apps.delivery.models import LivreurProfile
            LivreurProfile.objects.create(
                user=user,
                city=self.cleaned_data.get('city'),
                vehicle_type=self.cleaned_data.get('vehicle_type'),
                is_available=self.cleaned_data.get('is_available')
            )
        return user

class LivreurUpdateForm(forms.ModelForm):
    city = forms.CharField(max_length=100, required=False, label="Ville (Zone de livraison)", widget=forms.TextInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'}))
    vehicle_type = forms.CharField(max_length=50, required=False, label="Type de véhicule", widget=forms.TextInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'}))
    is_available = forms.BooleanField(required=False, label="Disponible", widget=forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-[#8CC63F] focus:ring-[#8CC63F]'}))

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'}),
            'email': forms.EmailInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'}),
            'phone': forms.TextInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]', 'placeholder': 'Ex: 670000000'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-[#8CC63F] focus:ring-[#8CC63F]'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'livreur_profile'):
            profile = self.instance.livreur_profile
            self.fields['city'].initial = profile.city
            self.fields['vehicle_type'].initial = profile.vehicle_type
            self.fields['is_available'].initial = profile.is_available

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        import re
        if phone and not re.match(r'^6[25789]\d{7}$', phone.replace(' ', '')):
            raise forms.ValidationError("Veuillez entrer un numéro de téléphone camerounais valide (ex: 67xxxxxxx).")
        return phone.replace(' ', '') if phone else phone

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            from apps.delivery.models import LivreurProfile
            profile, created = LivreurProfile.objects.get_or_create(user=user)
            profile.city = self.cleaned_data.get('city')
            profile.vehicle_type = self.cleaned_data.get('vehicle_type')
            profile.is_available = self.cleaned_data.get('is_available')
            profile.save()
        return user

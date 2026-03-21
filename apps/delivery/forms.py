from django import forms
from apps.users.models import CustomUser
from .models import LivreurProfile

class LivreurProfileForm(forms.ModelForm):
    phone = forms.CharField(max_length=20, label="Téléphone", required=False)
    avatar = forms.ImageField(label="Photo de profil", required=False)
    first_name = forms.CharField(max_length=50, label="Prénom", required=False)
    last_name = forms.CharField(max_length=50, label="Nom", required=False)

    class Meta:
        model = LivreurProfile
        fields = ['city', 'vehicle_type', 'is_available']
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['phone'].initial = self.user.phone
            self.fields['avatar'].initial = self.user.avatar
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            
        for name, field in self.fields.items():
            if type(field.widget) not in (forms.CheckboxInput, forms.RadioSelect):
                field.widget.attrs.update({
                    'class': 'w-full px-4 py-2 border rounded-md shadow-sm focus:ring-brand-green focus:border-brand-green sm:text-sm dark:bg-[#1C212E] dark:border-gray-700 dark:text-white'
                })

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.phone = self.cleaned_data['phone']
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            
            if self.cleaned_data.get('avatar'):
                self.user.avatar = self.cleaned_data['avatar']
            
            if commit:
                self.user.save()
                profile.save()
        return profile

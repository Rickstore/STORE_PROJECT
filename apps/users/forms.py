from django import forms
from .models import CustomUser

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-brand-green focus:border-brand-green sm:text-sm p-2 border'}),
            'last_name': forms.TextInput(attrs={'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-brand-green focus:border-brand-green sm:text-sm p-2 border'}),
            'email': forms.EmailInput(attrs={'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-brand-green focus:border-brand-green sm:text-sm p-2 border'}),
            'phone': forms.TextInput(attrs={'class': 'mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-brand-green focus:border-brand-green sm:text-sm p-2 border'}),
            'avatar': forms.FileInput(attrs={'class': 'mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-brand-green file:text-white hover:file:bg-[#7ab32f]'}),
        }

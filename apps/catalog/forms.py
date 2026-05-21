from django import forms
from .models import Product, BRAND_CHOICES


class ProductAdminForm(forms.ModelForm):
    marque = forms.ChoiceField(choices=BRAND_CHOICES, required=False, label="Marque")
    autre_marque = forms.CharField(
        label="Nouvelle Marque (si Autre sélectionné)",
        required=False,
        help_text="Entrez le nom de la marque si vous avez sélectionné 'Autre' ci-dessus."
    )

    class Meta:
        model = Product
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_marque = self.instance.marque if self.instance and self.instance.pk else None
        if current_marque and current_marque not in [c[0] for c in BRAND_CHOICES]:
            self.fields['marque'].choices = BRAND_CHOICES + [(current_marque, current_marque)]

    def clean(self):
        cleaned_data = super().clean()
        marque = cleaned_data.get('marque')
        autre_marque = cleaned_data.get('autre_marque')
        if marque == 'Autre' and autre_marque:
            cleaned_data['marque'] = autre_marque
        return cleaned_data

from django import forms
from apps.catalog.models import Product, ProductVariant, VariantStock, Store, Category, BRAND_CHOICES, COLOR_CHOICES, CAPACITY_CHOICES, ProductImage
from apps.users.models import CustomUser


class ProductForm(forms.ModelForm):
    """Formulaire de création/modification d'un Produit (sans les variantes)."""
    marque = forms.ChoiceField(
        choices=BRAND_CHOICES,
        required=False,
        label="Marque",
        widget=forms.Select(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'})
    )
    autre_marque = forms.CharField(
        required=False,
        label="Autre Marque",
        widget=forms.TextInput(attrs={
            'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]',
            'placeholder': 'Entrez la marque...'
        })
    )
    prix_unit = forms.DecimalField(
        max_digits=12, decimal_places=0, required=True, label="Prix unitaire (FCFA)", min_value=0,
        widget=forms.NumberInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]', 'min': '0'})
    )
    capacite = forms.ChoiceField(
        choices=[('', 'Aucune')] + CAPACITY_CHOICES, required=False, label="Capacité par défaut",
        widget=forms.Select(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'})
    )
    available_colors = forms.MultipleChoiceField(
        choices=COLOR_CHOICES, required=False, label="Couleurs",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'accent-[#8CC63F]'})
    )
    available_capacities = forms.MultipleChoiceField(
        choices=CAPACITY_CHOICES, required=False, label="Capacités",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'accent-[#8CC63F]'})
    )
    stk_dla = forms.IntegerField(
        initial=1, min_value=0, required=True, label="Stock Douala",
        widget=forms.NumberInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'})
    )
    stk_yde = forms.IntegerField(
        initial=1, min_value=0, required=True, label="Stock Yaoundé",
        widget=forms.NumberInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'})
    )
    img_path = forms.ImageField(
        required=False, label="Image du Produit",
        widget=forms.FileInput(attrs={'class': 'w-full text-xs text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-[#8CC63F]/10 file:text-[#8CC63F] hover:file:bg-[#8CC63F]/20'})
    )
    reset_stocks = forms.BooleanField(
        required=False, 
        initial=False,
        label="Réinitialiser les stocks",
        help_text="Cochez pour appliquer ces valeurs à TOUTES les variantes existantes."
    )

    class Meta:
        model = Product
        fields = [
            'nom_prod', 'marque', 'autre_marque', 'cat_id',
            'description', 'specs',
            'is_active', 'is_2ndmain', 'fast_deal'
        ]
        widgets = {
            'nom_prod': forms.TextInput(attrs={
                'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]',
                'placeholder': 'Ex: iPhone 17 Pro Max'
            }),
            'cat_id': forms.Select(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'}),
            'description': forms.Textarea(attrs={
                'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]',
                'rows': 3,
                'placeholder': 'Description visible par les clients...'
            }),
            'specs': forms.Textarea(attrs={
                'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]',
                'rows': 4,
                'placeholder': 'Ex: Processeur: A18 Pro\nRam: 8 Go\nBatterie: 4685mAh'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-[#8CC63F] focus:ring-[#8CC63F]'}),
            'is_2ndmain': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-[#8CC63F] focus:ring-[#8CC63F]'}),
            'fast_deal': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-[#8CC63F] focus:ring-[#8CC63F]'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ajouter dynamiquement les champs de prix pour chaque capacité
        for cap_code, cap_label in CAPACITY_CHOICES:
            field_name = f'price_{cap_code}'
            self.fields[field_name] = forms.DecimalField(
                required=False,
                max_digits=12,
                decimal_places=0,
                widget=forms.NumberInput(attrs={
                    'class': 'w-full pl-2 pr-10 py-1.5 text-xs border border-gray-200 rounded-lg focus:outline-none focus:border-[#8CC63F] focus:ring-1 focus:ring-[#8CC63F]/20',
                    'placeholder': 'Prix FCFA'
                })
            )

        if self.instance and self.instance.pk:
            choices_values = [c[0] for c in BRAND_CHOICES]
            if self.instance.marque in choices_values:
                self.fields['marque'].initial = self.instance.marque
            elif self.instance.marque:
                self.fields['marque'].initial = 'Autre'
                self.fields['autre_marque'].initial = self.instance.marque
                
            # Peupler les champs dynamiques depuis les variantes    
            variants = self.instance.variants.all()
            if variants.exists():
                first_v = variants.filter(is_active=True).first() or variants.first()
                self.fields['prix_unit'].initial = first_v.prix_unit
                self.fields['capacite'].initial = first_v.capacite
                
                colors = set(v.couleur for v in variants if v.couleur)
                caps = set(v.capacite for v in variants if v.capacite)
                self.fields['available_colors'].initial = list(colors)
                self.fields['available_capacities'].initial = list(caps)
                
                # Peupler les prix spécifiques pour chaque capacité
                for variant in variants.filter(is_active=True):
                    if variant.capacite:
                        self.fields[f'price_{variant.capacite}'].initial = variant.prix_unit
                
                # Pour le stock simple, on somme la première variante si existante pour éviter de compliquer form
                stk_dla = 0
                stk_yde = 0
                for v in variants:
                    for vs in v.stocks.all():
                        if 'douala' in vs.store.city.lower():
                            stk_dla += vs.quantity
                        if 'yaound' in vs.store.city.lower():
                            stk_yde += vs.quantity
                
                self.fields['stk_dla'].initial = stk_dla
                self.fields['stk_yde'].initial = stk_yde

    def save(self, commit=True):
        instance = super().save(commit=False)
        marque_choice = self.cleaned_data.get('marque')
        autre = self.cleaned_data.get('autre_marque')
        if marque_choice == 'Autre' and autre:
            instance.marque = autre
        else:
            instance.marque = marque_choice
        if commit:
            instance.save()
            
            # Gestion de l'image
            img_file = self.cleaned_data.get('img_path')
            if img_file:
                # Créer ou écraser l'image principale
                ProductImage.objects.create(product=instance, image=img_file, is_primary=True, order=0)

            # Gestion des variantes et stock
            prix = self.cleaned_data.get('prix_unit')
            colors = self.cleaned_data.get('available_colors') or []
            capacities = self.cleaned_data.get('available_capacities') or []
            default_cap = self.cleaned_data.get('capacite')
            stk_dla = self.cleaned_data.get('stk_dla') or 0
            stk_yde = self.cleaned_data.get('stk_yde') or 0

            # Désactiver les anciennes variantes
            instance.variants.update(is_active=False)
            
            store_dla, _ = Store.objects.get_or_create(city='Douala', defaults={'name': 'Boutique Douala'})
            store_yde, _ = Store.objects.get_or_create(city='Yaoundé', defaults={'name': 'Boutique Yaoundé'})

            if not colors and not capacities:
                # Créer une variante simple (sans options supplémentaires)
                v, created = ProductVariant.objects.get_or_create(
                    product=instance, couleur=None, capacite=default_cap or None,
                    defaults={'prix_unit': prix, 'is_active': True}
                )
                v.is_active = True
                v.prix_unit = prix
                v.save()
                VariantStock.objects.update_or_create(variant=v, store=store_dla, defaults={'quantity': stk_dla})
                VariantStock.objects.update_or_create(variant=v, store=store_yde, defaults={'quantity': stk_yde})
            else:
                if not colors: colors = [None]
                if not capacities: capacities = [default_cap or None]

                for c in colors:
                    for cap in capacities:
                        # Chercher un prix spécifique pour cette capacité dans les données POST
                        specific_price = self.data.get(f'price_{cap}')
                        variant_price = prix
                        if specific_price and specific_price.strip():
                            try:
                                variant_price = float(specific_price)
                            except ValueError:
                                variant_price = prix

                        v, created = ProductVariant.objects.update_or_create(
                            product=instance, couleur=c, capacite=cap,
                            defaults={'prix_unit': variant_price, 'is_active': True}
                        )
                        v.is_active = True
                        v.prix_unit = variant_price
                        v.save()
                        
                        # Gestion des stocks détaillés (overrides depuis la matrice JS)
                        # Format attendu : v_stock_<store_city_prefix>_<color>_<capacity>
                        c_slug = c if c else "none"
                        cap_slug = cap if cap else "none"
                        
                        spec_dla = self.data.get(f'v_stock_dla_{c_slug}_{cap_slug}')
                        spec_yde = self.data.get(f'v_stock_yde_{c_slug}_{cap_slug}')
                        
                        target_stk_dla = stk_dla
                        target_stk_yde = stk_yde
                        
                        if spec_dla is not None and spec_dla.strip() != '':
                            try: target_stk_dla = int(spec_dla)
                            except ValueError: pass
                        if spec_yde is not None and spec_yde.strip() != '':
                            try: target_stk_yde = int(spec_yde)
                            except ValueError: pass

                        # On met à jour le stock si :
                        # 1. C'est une nouvelle variante
                        # 2. L'utilisateur a explicitement demandé un reset global
                        # 3. Des valeurs spécifiques ont été fournies dans la matrice (prioritaires)
                        has_specific = (spec_dla is not None and spec_dla.strip() != '') or (spec_yde is not None and spec_yde.strip() != '')
                        
                        if created or self.cleaned_data.get('reset_stocks') or has_specific:
                            VariantStock.objects.update_or_create(variant=v, store=store_dla, defaults={'quantity': target_stk_dla})
                            VariantStock.objects.update_or_create(variant=v, store=store_yde, defaults={'quantity': target_stk_yde})
            
        return instance


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['nom_cat', 'slug_cat', 'desc_cat', 'img_cat']
        widgets = {
            'nom_cat': forms.TextInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'}),
            'slug_cat': forms.TextInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]', 'placeholder': 'ex: smartphones'}),
            'desc_cat': forms.Textarea(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]', 'rows': 2}),
            'img_cat': forms.FileInput(attrs={'class': 'w-full text-xs text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-[#8CC63F]/10 file:text-[#8CC63F] hover:file:bg-[#8CC63F]/20'}),
        }


class LivreurCreationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#8CC63F]'}),
        label="Mot de passe"
    )
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
        user.is_staff = True
        user.must_reset = True
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

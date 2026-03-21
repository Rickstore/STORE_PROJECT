from django.core.management.base import BaseCommand
from apps.catalog.models import Store

class Command(BaseCommand):
    help = 'Seeds Douala and Yaoundé stores'

    def handle(self, *args, **kwargs):
        stores = [
            {'name': 'AUDSTORE Douala', 'city': 'Douala', 'address': 'Akwa, Rue de la Joie'},
            {'name': 'AUDSTORE Yaoundé', 'city': 'Yaoundé', 'address': 'Rue Kennedy, ancien direction Orange'},
        ]
        
        for store_data in stores:
            store, created = Store.objects.get_or_create(
                name=store_data['name'],
                city=store_data['city'],
                defaults={'address': store_data['address']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Magasin créé: {store.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Magasin existe déjà: {store.name}"))

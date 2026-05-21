import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.catalog.models import Category
for c in Category.objects.all():
    print(f"'{c.nom_cat}' | '{c.slug_cat}'")

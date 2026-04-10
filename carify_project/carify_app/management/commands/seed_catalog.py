import os
import random
import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from carify_app.models import Category, Product

# Highly curated Unsplash IDs mapped to Supercars, Interiors, Carbon Fiber, and Automotive Art
IMAGE_URLS = [
    "https://images.unsplash.com/photo-1583121274602-3e2820c69888?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1544829099-b9a0c07fad1a?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1563720223185-11003d516935?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1614200179396-2bdb77ebf81b?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1542282088-fe8426682b8f?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1542362567-b07e54358753?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1545620999-db040b9918fb?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1503376712341-ea1c340d86fa?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1580274455191-1c62238fa333?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1550346049-7c85859942a2?auto=format&fit=crop&w=800&q=80"
]

CATEGORIES = [
    "Hypercar Chassis", "Carbon Aerodynamics", "Forged Wheels", 
    "Bespoke Interiors", "Performance Exhausts", "Track Suspension", 
    "Ceramic Protection", "Exotic Engine Bays", "Telemetry Systems", "Artisan Apparel"
]

LUXURY_ADJECTIVES = ["Bespoke", "Carbon", "Forged", "Titanium", "Aero", "Hyper", "Elite", "Obsidian", "Satin"]
LUXURY_NOUNS = ["Splitter", "Diffuser", "Exhaust Array", "Calipers", "ECU Tune", "Coilovers", "Steering Rack", "Harness", "Ceramic Pads"]

class Command(BaseCommand):
    help = 'Seeds the database with 10 exact categories and 150 products'

    def handle(self, *args, **kwargs):
        self.stdout.write("Booting Elite Catalog Seeder...")

        # Find or Create Superuser Seller to host the products
        seller, created = User.objects.get_or_create(username='CarifyBoutique', defaults={'email': 'vault@carify.com', 'is_staff': True})
        if created:
            seller.set_password('carify123!')
            seller.save()
        
        self.stdout.write("Establishing Image Core... Downloading 10 4K Assets. Please wait...")
        image_pool = []
        for idx, url in enumerate(IMAGE_URLS):
            try:
                response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
                if response.status_code == 200:
                    image_pool.append({'name': f'luxury_asset_{idx}.jpg', 'content': response.content})
                    self.stdout.write(f" -> Downloaded asset {idx+1}/{len(IMAGE_URLS)}")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Failed to fetch image {idx} due to timeout."))

        if not image_pool:
            self.stdout.write(self.style.ERROR("CRITICAL: Failed to download any images. Script Aborted."))
            return

        total_products = 0
        for cat_name in CATEGORIES:
            category, _ = Category.objects.get_or_create(name=cat_name, description=f"The finest selection of {cat_name}.")
            self.stdout.write(self.style.SUCCESS(f"\nBuilding Category: {category.name}"))
            
            for i in range(15):
                name = f"{random.choice(LUXURY_ADJECTIVES)} {random.choice(LUXURY_NOUNS)} X-Spec"
                desc = (
                    f"A masterclass in automotive engineering. This {name} belongs in the {category.name} collection. "
                    "Forged with ultra-lightweight materials and tested under extreme aerodynamic pressure to ensure absolute "
                    "perfection. Elevate your driving dynamic instantly with absolute precision."
                )
                price = round(random.uniform(1200.00, 25000.00), 2)
                
                # Construct Product
                product = Product.objects.create(
                    name=name,
                    description=desc,
                    quantity=random.randint(1, 10),
                    price=price,
                    seller=seller,
                    category=category
                )
                
                # Mount Local Image
                img_data = random.choice(image_pool)
                product.image.save(f"p_{product.id}_{img_data['name']}", ContentFile(img_data['content']), save=True)
                total_products += 1
                
            self.stdout.write(f" -> Generated 15 exclusive products.")

        self.stdout.write(self.style.SUCCESS(f"\n[SYSTEM ONLINE] Successfully mapped 10 Catalogs and {total_products} Products into the DB!"))

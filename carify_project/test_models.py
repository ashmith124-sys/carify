import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'carify_project.settings')
import django
django.setup()

from carify_app.models import Product

for p in Product.objects.all()[:5]:
    try:
        url = p.image.url if p.image else "No Image"
    except Exception as e:
        url = f"Error: {e}"
    
    print(f"Product {p.id}: image name= '{p.image.name}', url= '{url}', first_media_image_url= '{p.first_media_image_url}'")
    

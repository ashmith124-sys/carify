from django.core.management.base import BaseCommand
from carify_app.models import Service, Category
from django.contrib.auth.models import User
from django.core.files import File
import os

class Command(BaseCommand):
    help = 'Populate the database with demo services'

    def handle(self, *args, **options):
        # Get admin user and category
        admin_user = User.objects.filter(is_superuser=True).first()
        preservation_cat = Category.objects.filter(name__icontains='Preservation').first()

        if not admin_user:
            self.stdout.write(self.style.ERROR('No admin user found. Create one first.'))
            return

        services_data = [
            {
                'name': 'MOLECULAR PAINT CORRECTION',
                'description': 'Our multi-stage correction ritual utilizes nano-abrasives and laser-guided leveling to eliminate microscopic imperfections, restoring the specimen\'s finish to a better-than-factory brilliance.',
                'price': 1850.00,
                'image_path': 'services/molecular_paint_correction.png',
                'category': preservation_cat
            },
            {
                'name': 'BESPOKE INTERIOR RESTORATION',
                'description': 'A comprehensive rejuvenation of the cabin ecosystem. We utilize pH-balanced steam, Swiss-grade conditioners, and surgical-grade instruments to restore every fiber and hide to its original grandeur.',
                'price': 1200.00,
                'image_path': 'services/bespoke_interior_restoration.png',
                'category': preservation_cat
            },
            {
                'name': 'PERFORMANCE OPTIMIZATION AUDIT',
                'description': 'A deep-tier technical interrogation of the specimen\'s vital systems. Using advanced telemetry and endoscopic analysis, we identify and calibrate performance bottlenecks for peak operational efficiency.',
                'price': 950.00,
                'image_path': 'services/performance_optimization_audit.png',
                'category': preservation_cat
            },
            {
                'name': 'VINTAGE HERITAGE CERTIFICATION',
                'description': 'A formal authentication and preservation protocol for historic specimens. Our master curators document chassis integrity, drivetrain originality, and historical provenance for the ultimate collector dossier.',
                'price': 2500.00,
                'image_path': 'services/vintage_heritage_certification.png',
                'category': preservation_cat
            }
        ]

        for data in services_data:
            service, created = Service.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'price': data['price'],
                    'seller': admin_user,
                    'category': data['category'],
                    'image': data['image_path']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created service: {service.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Service already exists: {service.name}'))

        self.stdout.write(self.style.SUCCESS('Population complete.'))

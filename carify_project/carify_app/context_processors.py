from django.conf import settings

def stripe_settings(request):
    return {
        'STRIPE_PUBLIC_KEY': getattr(settings, 'STRIPE_PUBLIC_KEY', ''),
    }

from django.conf import settings

def api_keys(request):
    """
    Exposes API keys from settings to all templates.
    """
    return {
        'GOOGLE_MAPS_API_KEY': getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
    }

from django.conf import settings


def cloudinary_config(request):
    return {
        'CLOUDINARY_CLOUD_NAME': settings.CLOUDINARY_CLOUD_NAME,
        'CLOUDINARY_UPLOAD_PRESET': settings.CLOUDINARY_UPLOAD_PRESET,
    }

def health_api_config(request):
    return {
        'CALORIE_NINJAS_API_KEY': getattr(settings, 'CALORIE_NINJAS_API_KEY', ''),
        'CALORIE_NINJAS_API_URL': getattr(settings, 'CALORIE_NINJAS_API_URL', 'https://api.api-ninjas.com/v1/nutrition'),
    }

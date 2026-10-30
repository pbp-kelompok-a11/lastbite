from django.conf import settings
from django.http import HttpResponse
from django.views.static import serve

from main.models import StoredFile


def serve_media(request, path):
    """Layani /media/<path>: cari di database dulu, lalu fallback ke folder media/."""
    obj = StoredFile.objects.filter(name=path).first()
    if obj is None:
        return serve(request, path, document_root=settings.MEDIA_ROOT)
    response = HttpResponse(
        bytes(obj.content),
        content_type=obj.content_type or 'application/octet-stream',
    )
    response['Cache-Control'] = 'public, max-age=86400'
    return response
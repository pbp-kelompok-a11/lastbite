import mimetypes

from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.conf import settings
from django.utils.deconstruct import deconstructible


@deconstructible
class DatabaseStorage(Storage):
    """Menyimpan file unggahan di tabel main.StoredFile (bukan di disk server)."""

    @staticmethod
    def _clean(name):
        return str(name).replace('\\', '/').lstrip('/')

    def _model(self):
        from main.models import StoredFile  # import lokal agar aman saat startup
        return StoredFile

    def _open(self, name, mode='rb'):
        obj = self._model().objects.get(name=self._clean(name))
        return ContentFile(bytes(obj.content), name=self._clean(name))

    def _save(self, name, content):
        name = self._clean(name)
        content.seek(0)
        data = content.read()
        if isinstance(data, str):
            data = data.encode()
        content_type = mimetypes.guess_type(name)[0] or 'application/octet-stream'
        self._model().objects.update_or_create(
            name=name,
            defaults={'content': data, 'content_type': content_type, 'size': len(data)},
        )
        return name

    def exists(self, name):
        return self._model().objects.filter(name=self._clean(name)).exists()

    def delete(self, name):
        self._model().objects.filter(name=self._clean(name)).delete()

    def size(self, name):
        return self._model().objects.values_list('size', flat=True).get(name=self._clean(name))

    def url(self, name):
        return settings.MEDIA_URL + self._clean(name)
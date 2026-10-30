from django.db import models


class StoredFile(models.Model):
    """File unggahan (foto profil, toko, Surprise Bag) yang disimpan di database.

    Disk server PWS tidak permanen (hilang saat restart/deploy ulang), jadi foto
    disimpan di database supaya tidak hilang. Lihat main/storage.py.
    """

    name = models.CharField(max_length=255, unique=True)
    content = models.BinaryField()
    content_type = models.CharField(max_length=100, blank=True)
    size = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
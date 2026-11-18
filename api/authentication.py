from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    Session authentication untuk aplikasi Flutter (pbp_django_auth).

    pbp_django_auth menyimpan cookie `sessionid` tetapi tidak mengirim header
    X-CSRFToken, sehingga SessionAuthentication bawaan DRF akan menolak
    request POST/PUT/PATCH/DELETE dari user yang sudah login ("CSRF Failed").

    Kelas ini hanya dipakai oleh view DRF (lewat REST_FRAMEWORK di settings.py),
    jadi view Django biasa milik website tetap terlindungi CSRF seperti semula.
    Pendekatannya sama dengan @csrf_exempt di Tutorial 8 PBP.
    """

    def enforce_csrf(self, request):
        return None

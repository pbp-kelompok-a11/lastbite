"""Integrasi OpenStreetMap Nominatim (geocoding) + perhitungan jarak.

Kebijakan Nominatim yang dipatuhi di sini:
  * wajib mengirim User-Agent yang jelas (set lewat env NOMINATIM_USER_AGENT),
  * maksimal 1 request per detik (ada jeda antar-percobaan),
  * hasil di-cache agar alamat yang sama tidak diminta berulang.
"""
import hashlib
import json
import logging
import math
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from django.core.cache import cache

logger = logging.getLogger(__name__)

NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'
USER_AGENT = os.environ.get(
    'NOMINATIM_USER_AGENT',
    'LastBite-PBP-A11/1.0',
)
REQUEST_TIMEOUT = 6          # detik
POSITIVE_CACHE_SECONDS = 60 * 60 * 24
NEGATIVE_CACHE_SECONDS = 60 * 5
EARTH_RADIUS_KM = 6371.0088


class GeocodingError(Exception):
    """Layanan Nominatim tidak dapat dihubungi / mengembalikan respons rusak."""


# Geocoding
def _cache_key(query):
    digest = hashlib.sha1(' '.join(query.lower().split()).encode('utf-8')).hexdigest()
    return f'nominatim:{digest}'


def _request_nominatim(query):
    params = urllib.parse.urlencode({
        'q': query,
        'format': 'jsonv2',
        'limit': 1,
        'countrycodes': 'id',
        'accept-language': 'id',
    })
    request = urllib.request.Request(
        f'{NOMINATIM_URL}?{params}',
        headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'},
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            payload = json.loads(response.read().decode('utf-8'))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        logger.warning('Nominatim gagal untuk %r: %s', query, exc)
        raise GeocodingError(str(exc)) from exc

    if not payload:
        return None
    try:
        return {
            'lat': float(payload[0]['lat']),
            'lng': float(payload[0]['lon']),
            'display_name': payload[0].get('display_name', ''),
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise GeocodingError('Format respons Nominatim tidak dikenali') from exc


def _clean_parts(address):
    """Pecah alamat per koma; buang kode pos, 'Indonesia', dan bagian yang berulang."""
    seen = set()
    parts = []
    for raw in address.split(','):
        part = ' '.join(re.sub(r'\b\d{5}\b', '', raw).split())
        if not part or part.lower() == 'indonesia':
            continue
        key = part.lower()
        if key in seen:
            continue
        seen.add(key)
        parts.append(part)
    return parts


def _candidate_queries(address):
    """Alamat lengkap dulu; jika tidak ketemu, coba versi yang lebih ringkas.

    Contoh: "Jl. Margonda Raya No. 12, Pondok Cina, Depok" -> coba juga
    "Pondok Cina, Depok", karena Nominatim sering gagal pada nomor bangunan.

    Untuk alamat panjang (hasil salin dari peta) dicoba juga:
    "Nama Tempat, Kecamatan, Kabupaten/Kota" lalu "Kecamatan, Kabupaten/Kota".
    """
    raw_parts = [p.strip() for p in address.split(',') if p.strip()]
    candidates = [', '.join(raw_parts)] if raw_parts else []

    if len(raw_parts) <= 4:
        for start in (1, 2):
            if len(raw_parts) - start >= 2:
                candidates.append(', '.join(raw_parts[start:]))
        return candidates[:3]

    parts = _clean_parts(address)
    kec = next((p for p in parts if re.match(r'^kec(amatan)?\.?\s', p, re.I)), '')
    kab = next((p for p in parts if re.match(r'^(kabupaten|kab\.|kota)\s', p, re.I)), '')
    kec_name = re.sub(r'^kec(amatan)?\.?\s+', '', kec, flags=re.I) if kec else ''

    if kec_name and kab:
        candidates.append(f'{parts[0]}, {kec_name}, {kab}')
        candidates.append(f'{kec_name}, {kab}')
    else:
        candidates.append(', '.join(parts[:3]))
    candidates.append(', '.join(parts[-2:]))

    unique = []
    for query in candidates:
        if query and query not in unique:
            unique.append(query)
    return unique[:4]


def geocode_address(address):
    """Ubah alamat menjadi {'lat', 'lng', 'display_name'}.

    Return None jika alamat tidak ditemukan.
    Raise GeocodingError jika layanan Nominatim bermasalah.
    """
    address = (address or '').strip()
    if not address:
        return None

    last_error = None
    made_request = False
    for query in _candidate_queries(address):
        key = _cache_key(query)
        cached = cache.get(key)
        if cached is not None:
            if cached:                       # hasil positif
                return cached
            continue                         # {} = pernah dicari & tidak ada

        if made_request:
            time.sleep(1.1)                  # patuhi batas 1 request/detik
        made_request = True
        try:
            result = _request_nominatim(query)
        except GeocodingError as exc:
            last_error = exc
            continue

        if result:
            cache.set(key, result, POSITIVE_CACHE_SECONDS)
            return result
        cache.set(key, {}, NEGATIVE_CACHE_SECONDS)

    if last_error is not None:
        raise last_error
    return None


# Jarak
def haversine_km(lat1, lng1, lat2, lng2):
    """Jarak lingkaran-besar (km) antara dua titik koordinat."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = phi2 - phi1
    d_lambda = math.radians(lng2 - lng1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def bounding_box(lat, lng, radius_km):
    """Kotak kasar (min_lat, max_lat, min_lng, max_lng) untuk pra-filter di database."""
    d_lat = math.degrees(radius_km / EARTH_RADIUS_KM)
    cos_lat = max(math.cos(math.radians(lat)), 0.01)
    d_lng = math.degrees(radius_km / (EARTH_RADIUS_KM * cos_lat))
    return lat - d_lat, lat + d_lat, lng - d_lng, lng + d_lng

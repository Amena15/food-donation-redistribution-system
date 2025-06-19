# utils/geolocation.py
import requests
from django.conf import settings
from django.contrib.gis.geos import Point

def geocode_address(address):
    """
    Convert address to coordinates using Mapbox API
    Returns (latitude, longitude) or (None, None)
    """
    try:
        response = requests.get(
            'https://api.mapbox.com/geocoding/v5/mapbox.places/' + address + '.json',
            params={
                'access_token': settings.MAPBOX_ACCESS_TOKEN,
                'limit': 1
            }
        )
        data = response.json()
        if data['features']:
            longitude, latitude = data['features'][0]['center']
            return latitude, longitude
    except Exception:
        pass
    return None, None
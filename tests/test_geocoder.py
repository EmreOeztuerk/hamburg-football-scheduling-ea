import pytest
from geocoder.distance_matrix import (
    haversine,
    is_south_of_elbe,
    calculate_realistic_distance
)

def test_haversine_distance():
    """Testet die Großkreis-Berechnung mit bekannten Hamburger Koordinaten."""
    # Hamburg Hauptbahnhof
    lat_hbf, lon_hbf = 53.5528, 10.0067
    # Bahnhof Altona
    lat_alt, lon_alt = 53.5530, 9.9352

    dist = haversine(lat_hbf, lon_hbf, lat_alt, lon_alt)
    # Luftlinie Hbf -> Altona beträgt ca. 4.7 km
    assert 4.5 <= dist <= 5.0

def test_haversine_same_point():
    """Identische Koordinaten müssen Distanz 0.0 liefern."""
    assert haversine(53.55, 9.99, 53.55, 9.99) == pytest.approx(0.0)

def test_is_south_of_elbe():
    """Prüft die lineare Trennlinie für Nord- vs. Süd-Hamburg."""
    # Harburg (Südlich der Elbe)
    assert is_south_of_elbe(lat=53.46, lon=9.98) is True
    # Eimsbüttel (Nördlich der Elbe)
    assert is_south_of_elbe(lat=53.58, lon=9.95) is False

def test_calculate_realistic_distance_chokepoint_detour():
    """Prüft, ob bei Flussüberquerung ein Nadelöhr-Umweg erzwungen wird."""
    lat_north, lon_north = 53.58, 9.95  # Eimsbüttel
    lat_south, lon_south = 53.46, 9.98  # Harburg

    # Reale Distanz über Nadelöhr (inkl. Umwegfaktor 1.3)
    realistic_dist = calculate_realistic_distance(lat_north, lon_north, lat_south, lon_south)
    # Reines Haversine (Luftlinie)
    direct_air_dist = haversine(lat_north, lon_north, lat_south, lon_south)

    # Die berechnete Distanz muss durch den Nadelöhr-Zwang spürbar größer als Luftlinie sein
    assert realistic_dist > direct_air_dist
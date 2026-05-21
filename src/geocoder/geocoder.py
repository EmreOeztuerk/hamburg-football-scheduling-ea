"""
Adress-Geocoder für Hamburger Amateurvereine.

Liest die exakten Adressen aus der CSV, wandelt sie über Nominatim
in Längen- und Breitengrade um und nutzt einen Adress-Cache,
um API-Anfragen für Mannschaften desselben Vereins zu reduzieren.
"""

import csv
import os
import time
import requests

HEADERS = {
    'User-Agent': 'HamburgFootballEA/2.0 (Bachelorarbeit PoC)'
}

# Pfadkonfiguration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
INPUT_CSV = os.path.join(DATA_DIR, "hamburg_vereine_addresses_final.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "hamburg_vereine_geocoded_final.csv")

def geocode_address(address: str) -> tuple[float | None, float | None]:
    """
    Fragt Nominatim nach den Koordinaten einer Adresse.
    Mit intelligentem Fallback, falls Stadionnamen die Suche stören.
    """
    if "NICHT GEFUNDEN" in address or "FEHLER" in address:
        return None, None

    url = "https://nominatim.openstreetmap.org/search"

    # Variante 1: Komplette Adresse versuchen
    # Variante 2: Nur die letzten beiden Teile (meist Straße, PLZ + Ort)
    # Beispiel: "Stadion X, Musterstr. 1, 12345 Stadt" -> "Musterstr. 1, 12345 Stadt"
    parts = [p.strip() for p in address.split(',')]

    queries = [address]
    if len(parts) >= 2:
        queries.append(f"{parts[-2]}, {parts[-1]}")

    for query in queries:
        params = {
            'q': query,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'de'
        }

        try:
            response = requests.get(url, params=params, headers=HEADERS)
            response.raise_for_status()
            data = response.json()

            if data:
                return float(data[0]['lat']), float(data[0]['lon'])

        except Exception as e:
            print(f"API-Fehler bei '{query}': {e}")

        time.sleep(1.5) # Zwingende Pause (1 Sekunde Limit bei Nominatim)

    return None, None


def main():
    print("=== Geocoding der exakten Sportplatz-Adressen ===")

    if not os.path.exists(INPUT_CSV):
        print(f"FEHLER: Datei {INPUT_CSV} nicht gefunden.")
        return

    # Daten einlesen
    teams_data = []
    with open(INPUT_CSV, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            teams_data.append({
                "staffel": row["Staffel"],
                "mannschaft": row["Mannschaft"],
                "adresse": row["Adresse"]
            })

    print(f"{len(teams_data)} Mannschaften geladen. Beginne API-Abfragen...\n")

    # Der geniale Cache: Speichert Koordinaten pro ADRESSE, nicht pro Mannschaft!
    address_cache = {}

    with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8-sig') as out_file:
        writer = csv.writer(out_file, delimiter=';')
        writer.writerow(["Staffel", "Mannschaft", "Breitengrad", "Laengengrad", "Adresse"])

        for team in teams_data:
            adresse = team["adresse"]
            mannschaft = team["mannschaft"]

            print(f"Suche: {mannschaft} ... ", end="", flush=True)

            # Wenn die Adresse völlig fehlt
            if "NICHT GEFUNDEN" in adresse:
                print("ÜBERSPRUNG (Keine Adresse vorhanden)")
                writer.writerow([team["staffel"], mannschaft, "NICHT GEFUNDEN", "NICHT GEFUNDEN", adresse])
                continue

            # Wenn wir die Adresse noch nie geocodet haben -> API fragen
            if adresse not in address_cache:
                lat, lon = geocode_address(adresse)
                address_cache[adresse] = (lat, lon)

                if lat and lon:
                    print(f"GEFUNDEN! (Neu über API)")
                else:
                    print("FEHLER! (Adresse von Karte nicht erkannt)")
            else:
                # Wir haben die Adresse schon im Cache!
                lat, lon = address_cache[adresse]
                print("GEFUNDEN! (Aus Zwischenspeicher)")

            # In CSV schreiben
            if lat and lon:
                writer.writerow([team["staffel"], mannschaft, lat, lon, adresse])
            else:
                writer.writerow([team["staffel"], mannschaft, "NICHT GEFUNDEN", "NICHT GEFUNDEN", adresse])

    print("\n" + "="*50)
    print(f"Fertig! Die finalen Geodaten liegen hier:\n{OUTPUT_CSV}")
    print("="*50)


if __name__ == "__main__":
    main()
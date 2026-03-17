import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time
import os


def geocode_hamburg_teams():
    # Pfade
    input_path = "data/hamburg_vereine_raw.csv"
    output_path = "data/hamburg_teams_geocoded.csv"

    if not os.path.exists(input_path):
        print(f"Fehler: {input_path} nicht gefunden!")
        return

    # Daten laden (beachte dein Semikolon-Trennzeichen)
    df = pd.read_csv(input_path, sep=';', encoding='utf-8-sig')

    # Duplikate entfernen (gleiche Vereine in verschiedenen Staffeln)
    unique_teams = df[['Vereinsname']].drop_duplicates()

    geolocator = Nominatim(user_agent="hamburg_football_optimizer_thesis")
    # Rate Limiter: Maximal 1 Anfrage pro Sekunde (Vorgabe von Nominatim)
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.1)

    print(f"Starte Geocoding für {len(unique_teams)} eindeutige Vereine...")

    results = []
    for index, row in unique_teams.iterrows():
        name = row['Vereinsname']
        # Wir optimieren die Suchanfrage: "Vereinsname + Hamburg + Sportplatz"
        query = f"{name} Hamburg Sportplatz"

        try:
            location = geocode(query)
            if location:
                results.append({
                    "Vereinsname": name,
                    "lat": location.latitude,
                    "lon": location.longitude,
                    "address_found": location.address
                })
                print(f"Gefunden: {name}")
            else:
                # Fallback ohne "Sportplatz"
                location = geocode(f"{name} Hamburg")
                if location:
                    results.append({
                        "Vereinsname": name,
                        "lat": location.latitude,
                        "lon": location.longitude,
                        "address_found": location.address
                    })
                    print(f"Gefunden (Fallback): {name}")
                else:
                    print(f"!!! Nicht gefunden: {name}")
        except Exception as e:
            print(f"Fehler bei {name}: {e}")
            time.sleep(2)

    # Ergebnisse speichern
    geo_df = pd.DataFrame(results)

    # Jetzt führen wir die Geodaten wieder mit der ursprünglichen Staffelliste zusammen
    final_df = pd.merge(df, geo_df, on="Vereinsname", how="left")
    final_df.to_csv(output_path, index=False, sep=';', encoding='utf-8-sig')

    print(f"\nFertig! Geocodierte Daten in {output_path} gespeichert.")


if __name__ == "__main__":
    geocode_hamburg_teams()
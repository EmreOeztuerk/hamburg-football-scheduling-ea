"""
Goldstandard Distanzmatrix-Generator (OpenStreetMap / OSRM)

Dieses Skript berechnet die echten Straßenkilometer zwischen allen Hamburger
Amateurvereinen über die öffentliche OSRM-Routing-API.
Um Server-Sperren zu vermeiden, nutzt es Rate-Limiting, einen Auto-Save-Cache
und iteriert symmetrisch (nur A->B, nicht B->A).
"""

import csv
import os
import time
import json
import requests

# Pfadkonfiguration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
INPUT_CSV = os.path.join(DATA_DIR, "hamburg_vereine_geocoded_final.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "distance_matrix.csv")  # Überschreibt die alte Matrix!
CACHE_FILE = os.path.join(DATA_DIR, "osrm_cache.json")  # Sichert den Fortschritt

# API-Einstellungen
# Öffentlicher OSRM-Server
OSRM_BASE_URL = "http://router.project-osrm.org/route/v1/driving/"
SLEEP_TIME = 0.8  # Sekunden Pause zwischen Requests


def load_cache() -> dict:
    """Lädt den Zwischenspeicher, damit bei einem Absturz nichts verloren geht."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    """Speichert den aktuellen Fortschritt auf der Festplatte."""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def get_osrm_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """
    Fragt die echte Straßenroute bei OpenStreetMap an.
    Format: OSRM erwartet Koordinaten im Format Longitude,Latitude!
    """
    url = f"{OSRM_BASE_URL}{lon1},{lat1};{lon2},{lat2}?overview=false"

    while True:
        try:
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data["code"] == "Ok":
                    # OSRM gibt Distanzen in Metern zurück -> Umrechnung in km
                    return data["routes"][0]["distance"] / 1000.0
                else:
                    print(f"OSRM Fehler: {data['code']} - setze auf 0.0")
                    return 0.0

            elif response.status_code == 429:
                print("\n[WARNUNG] OSRM Server blockiert (Too Many Requests).")
                print("Warte 60 Sekunden und versuche es erneut...")
                time.sleep(60)

            else:
                print(f"HTTP Fehler {response.status_code}. Setze auf 0.0")
                return 0.0

        except requests.exceptions.RequestException as e:
            print(f"\n[NETZWERKFEHLER] {e}. Warte 10 Sekunden...")
            time.sleep(10)


def main():
    print("=== OSRM Straßen-Routing Matrix Generator ===")
    print("HINWEIS: Dieser Vorgang dauert lange!\n")

    teams = []
    if not os.path.exists(INPUT_CSV):
        print(f"Fehler: {INPUT_CSV} nicht gefunden.")
        return

    # 1. Geodaten laden
    with open(INPUT_CSV, mode='r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)
        for row in reader:
            if len(row) >= 4 and row[2] != "NICHT GEFUNDEN":
                teams.append({
                    "name": row[1],
                    "lat": float(row[2]),
                    "lon": float(row[3])
                })

    n_teams = len(teams)
    print(f"Geladene Teams: {n_teams}")
    total_pairs = (n_teams * (n_teams - 1)) // 2
    print(f"Zu berechnende Routen (Symmetrisch): {total_pairs}")

    # 2. Cache laden
    cache = load_cache()
    cached_count = len(cache)
    if cached_count > 0:
        print(f"-> {cached_count} Routen bereits im Cache gefunden. Mache da weiter...\n")
    else:
        print("-> Kein Cache gefunden. Beginne bei 0...\n")

    # 3. Routen berechnen
    requests_made = 0
    for i in range(n_teams):
        for j in range(i + 1, n_teams):  # Wir berechnen nur A -> B

            team_a = teams[i]["name"]
            team_b = teams[j]["name"]

            # Einzigartiger Schlüssel für das Team-Paar (alphabetisch sortiert, um sicherzugehen)
            pair_key = f"{min(team_a, team_b)}||{max(team_a, team_b)}"

            if pair_key not in cache:
                print(f"Route {requests_made + cached_count + 1}/{total_pairs}: {team_a} -> {team_b} ... ", end="",
                      flush=True)

                # API Call (OSRM braucht erst LON, dann LAT)
                dist = get_osrm_distance(teams[i]["lon"], teams[i]["lat"],
                                         teams[j]["lon"], teams[j]["lat"])

                print(f"{dist:.2f} km")
                cache[pair_key] = dist
                requests_made += 1

                # Pause, damit Server nicht belastet wird
                time.sleep(SLEEP_TIME)

                # Alle 50 Requests werden abgespeichert in den Cache
                if requests_made % 50 == 0:
                    save_cache(cache)

    # Am Ende final speichern
    save_cache(cache)
    print("\nAlle echten Straßenrouten erfolgreich abgerufen!")

    # 4. Matrix aufbauen (Spiegeln)
    print("Erstelle symmetrische Matrix-CSV...")
    matrix_header = ["Mannschaft"] + [team["name"] for team in teams]
    matrix_rows = []

    for i in range(n_teams):
        row_data = [teams[i]["name"]]
        for j in range(n_teams):
            if i == j:
                row_data.append(0.0)
            else:
                team_a = teams[i]["name"]
                team_b = teams[j]["name"]
                pair_key = f"{min(team_a, team_b)}||{max(team_a, team_b)}"

                # Wir holen die Distanz aus dem Cache (egal in welche Richtung wir gerade schauen)
                dist = cache.get(pair_key, 0.0)
                row_data.append(dist)

        matrix_rows.append(row_data)

    # 5. Finale CSV speichern
    with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8-sig') as out_file:
        writer = csv.writer(out_file, delimiter=';')
        writer.writerow(matrix_header)
        writer.writerows(matrix_rows)

    print(f"\nERFOLG: Berechnung abgeschlossen. Matrix erfolgreich exportiert: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
"""
Berechnung der Distanzmatrix (Haversine-Formel).

Dieses Skript liest die finalen Geodaten ein und berechnet die paarweisen
Distanzen (in km) zwischen allen Mannschaften. Das Ergebnis ist eine
N x N Matrix (CSV), die als Grundlage für den Evolutionären Algorithmus dient.
"""

import csv
import os
import math

# --- PFAD-RESOLUTION ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
INPUT_CSV = os.path.join(DATA_DIR, "hamburg_vereine_geocoded_final.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "distance_matrix.csv")


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Berechnet die Distanz zwischen zwei Koordinaten in Kilometern.
    Nutzt die Haversine-Formel + einen empirischen Umwegfaktor für Straßen.
    """
    R = 6371.0  # Erdradius in km

    # Umrechnung in Bogenmaß (Radians)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Haversine-Formel
    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    luftlinie = R * c

    # Reale Fahrstrecke simulieren: Luftlinie * 1.3 (Stadt-Faktor)
    fahrstrecke = luftlinie * 1.3
    return round(fahrstrecke, 2)


def main():
    print("=== Generierung der Distanzmatrix ===")

    if not os.path.exists(INPUT_CSV):
        print(f"FEHLER: Datei {INPUT_CSV} nicht gefunden.")
        return

    teams = []

    # 1. Daten einlesen und validieren
    print("Lese und validiere Geodaten...")
    with open(INPUT_CSV, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file, delimiter=';')

        for row_idx, row in enumerate(reader, start=2):  # Start bei 2 wegen Header
            mannschaft = row.get("Mannschaft")
            lat_str = row.get("Breitengrad")
            lon_str = row.get("Laengengrad")

            # Fehlerfänger: Falls "NICHT GEFUNDEN" oder Excel-Zahlenfehler existieren
            try:
                lat = float(lat_str)
                lon = float(lon_str)
                teams.append({
                    "name": mannschaft,
                    "lat": lat,
                    "lon": lon
                })
            except ValueError:
                print(
                    f"WARNUNG: Zeile {row_idx} ({mannschaft}) hat ungültige Koordinaten: '{lat_str}' / '{lon_str}'. Wird übersprungen!")

    n_teams = len(teams)
    print(f"Erfolgreich geladen: {n_teams} Mannschaften mit sauberen Koordinaten.\n")

    if n_teams == 0:
        print("Abbruch: Keine gültigen Daten gefunden.")
        return

    # 2. Distanzmatrix berechnen (N x N)
    print(f"Berechne {n_teams * n_teams} Distanzen...")

    # Header für die Matrix (Spaltenköpfe)
    matrix_header = ["Mannschaft"] + [team["name"] for team in teams]
    matrix_rows = []

    for i in range(n_teams):
        row_data = [teams[i]["name"]]  # Erste Spalte: Name der Mannschaft
        for j in range(n_teams):
            if i == j:
                # Distanz zu sich selbst ist 0
                dist = 0.0
            else:
                dist = haversine(teams[i]["lat"], teams[i]["lon"],
                                 teams[j]["lat"], teams[j]["lon"])
            row_data.append(dist)
        matrix_rows.append(row_data)

    # 3. Matrix als CSV speichern
    print("Speichere Matrix...")
    with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8-sig') as out_file:
        writer = csv.writer(out_file, delimiter=';')
        writer.writerow(matrix_header)
        writer.writerows(matrix_rows)

    print("=" * 50)
    print("ERFOLG! Die Distanzmatrix wurde erstellt.")
    print(f"Datei liegt hier: {OUTPUT_CSV}")
    print("Dein Projekt ist nun bereit für den Evolutionären Algorithmus!")
    print("=" * 50)


if __name__ == "__main__":
    main()
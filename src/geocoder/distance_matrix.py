"""
Berechnung der Distanzmatrix (Inkl. Elb-Barriere & Nadelöhr-Heuristik).

Dieses Skript berechnet die Distanzen zwischen den Mannschaften.
WICHTIG: Es nutzt eine erweiterte Nadelöhr-Heuristik (Chokepoint Routing)
für die Elbe. Teams, die auf unterschiedlichen Flussseiten liegen, werden gezwungen,
entweder den Elbtunnel, die innerstädtischen Elbbrücken (B4/B75) oder
die Norderelbbrücke (A1) zu passieren. Der kürzeste dieser drei Wege gewinnt.

Autor: Emre Öztürk
"""

import csv
import os
import math

# =============================================================================
# PFAD-KONFIGURATION
# =============================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
INPUT_CSV = os.path.join(DATA_DIR, "hamburg_vereine_geocoded_final.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "distance_matrix.csv")

# =============================================================================
# NADELÖHR-KOORDINATEN (Chokepoints für die Flussüberquerung)
# =============================================================================
ELBTUNNEL = {"lat": 53.5360, "lon": 9.9230}         # A7
ELBBRUECKEN = {"lat": 53.5340, "lon": 10.0220}       # B4 / B75 (Zentrum)
NORDERELBBRUECKE = {"lat": 53.5286, "lon": 10.0371}  # A1 (Ost-Umfahrung)

# Empirischer Umwegfaktor (Straßenverlauf ist nie exakte Luftlinie)
DETOUR_FACTOR = 1.3

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Berechnet die Großkreisdistanz (Luftlinie) in km zwischen zwei GPS-Punkten."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def is_south_of_elbe(lat: float, lon: float) -> bool:
    """
    Mathematische Trennlinie für die Elbe.
    Approximation des Flussverlaufs als lineare Funktion: y = m*x + b
    Grobe Linie: Von Rothenburgsort bis Blankenese.
    """
    lat_river = -0.2 * (lon - 10.05) + 53.50
    return lat < lat_river

def calculate_realistic_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Kernelement der Routing-Heuristik.
    Prüft Barrieren und erzwingt bei Flussüberquerungen einen Umweg über die Nadelöhre.
    """
    south1 = is_south_of_elbe(lat1, lon1)
    south2 = is_south_of_elbe(lat2, lon2)

    # Fall 1: Keine Barriere (Teams auf derselben Seite)
    if south1 == south2:
        return haversine(lat1, lon1, lat2, lon2) * DETOUR_FACTOR

    # Fall 2: Barriere muss überquert werden -> Evaluierung der 3 Nadelöhre
    else:
        # Route 1: Über den Elbtunnel (A7)
        dist_via_tunnel = haversine(lat1, lon1, ELBTUNNEL["lat"], ELBTUNNEL["lon"]) + \
                          haversine(ELBTUNNEL["lat"], ELBTUNNEL["lon"], lat2, lon2)

        # Route 2: Über die klassischen Elbbrücken (B4/B75)
        dist_via_bruecken = haversine(lat1, lon1, ELBBRUECKEN["lat"], ELBBRUECKEN["lon"]) + \
                            haversine(ELBBRUECKEN["lat"], ELBBRUECKEN["lon"], lat2, lon2)

        # Route 3: Über die Norderelbbrücke (A1)
        dist_via_norderelbe = haversine(lat1, lon1, NORDERELBBRUECKE["lat"], NORDERELBBRUECKE["lon"]) + \
                              haversine(NORDERELBBRUECKE["lat"], NORDERELBBRUECKE["lon"], lat2, lon2)

        # Algorithmus wählt den kürzesten physikalischen Weg
        shortest_chokepoint_route = min(dist_via_tunnel, dist_via_bruecken, dist_via_norderelbe)

        return shortest_chokepoint_route * DETOUR_FACTOR

def main():
    print("=== Distanzmatrix Generator (Inkl. Erweiterter Elb-Heuristik) ===")
    teams = []

    if not os.path.exists(INPUT_CSV):
        print(f"Fehler: Geocodierte Daten nicht gefunden: {INPUT_CSV}")
        return

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
    print(f"Erfolgreich geladen: {n_teams} Mannschaften.")
    print(f"Berechne {n_teams * n_teams} Routen über 3 mögliche Nadelöhre...")

    matrix_rows = []
    matrix_header = ["Mannschaft"] + [team["name"] for team in teams]

    for i in range(n_teams):
        row_data = [teams[i]["name"]]
        for j in range(n_teams):
            if i == j:
                dist = 0.0
            else:
                dist = calculate_realistic_distance(teams[i]["lat"], teams[i]["lon"],
                                                    teams[j]["lat"], teams[j]["lon"])
            row_data.append(dist)
        matrix_rows.append(row_data)

    print("Speichere aktualisierte Distanzmatrix...")
    with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8-sig') as out_file:
        writer = csv.writer(out_file, delimiter=';')
        writer.writerow(matrix_header)
        writer.writerows(matrix_rows)

    print(f"Fertig! Reale Distanzen wurden in {OUTPUT_CSV} überschrieben.")

if __name__ == "__main__":
    main()
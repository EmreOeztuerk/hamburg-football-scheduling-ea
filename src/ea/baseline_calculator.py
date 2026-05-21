"""
Berechnung der sportlichen Ist-Struktur (Baseline).

Das Modul aggregiert die aktuell hinterlegten Staffeln des HFVs
und berechnet den resultierenden ökologischen Fußabdruck (Routenkilometer)
anhand der zugrundeliegenden Distanzmatrix.
"""

import csv
import os

# Pfadkonfiguration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

TEAMS_CSV = os.path.join(DATA_DIR, "hamburg_vereine_geocoded_final.csv")
MATRIX_CSV = os.path.join(DATA_DIR, "distance_matrix.csv")


def load_distance_matrix():
    dist_matrix = {}
    with open(MATRIX_CSV, mode='r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')
        header = next(reader)
        for row in reader:
            team_name = row[0]
            dist_matrix[team_name] = {}
            for idx, val in enumerate(row[1:], start=1):
                target_team = header[idx]
                dist_matrix[team_name][target_team] = float(val)
    return dist_matrix


def calculate_baseline():
    print("=== Lade Daten für HFV-Baseline ===")
    dist_matrix = load_distance_matrix()
    staffeln = {}

    # 1. Teams ihren echten HFV-Staffeln zuordnen
    with open(TEAMS_CSV, mode='r', encoding='utf-8-sig') as f:
        # HIER WAR DER FEHLER: Deine CSV nutzt Semikolons (;), keine Kommas (,)
        reader = csv.reader(f, delimiter=';')
        header = next(reader)
        for row in reader:
            if len(row) < 4 or row[2] == "NICHT GEFUNDEN":
                continue  # Teams ohne Koordinaten ignorieren wir

            staffel = row[0]
            team = row[1]
            if staffel not in staffeln:
                staffeln[staffel] = []
            staffeln[staffel].append(team)

    print(f"-> Erfolgreich eingelesen: {len(staffeln)} Staffeln!\n")

    total_km = 0.0

    # 2. Distanzen innerhalb jeder echten Staffel berechnen (Hin- und Rückspiel)
    for staffel_name, teams in staffeln.items():
        staffel_km = 0.0
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                t1, t2 = teams[i], teams[j]
                if t1 in dist_matrix and t2 in dist_matrix[t1]:
                    # Hin- und Rückspiel (* 2)
                    staffel_km += dist_matrix[t1][t2] * 2

        total_km += staffel_km
        print(f"{staffel_name} ({len(teams)} Teams): {staffel_km:,.2f} km".replace(",", "."))

    print("\n" + "=" * 50)
    print(f"OFFIZIELLE HFV-BASELINE: {total_km:,.2f} km".replace(",", "."))
    print("=" * 50)


if __name__ == "__main__":
    calculate_baseline()
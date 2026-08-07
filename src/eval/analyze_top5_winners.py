"""
Analyse der Individual-Ökologischen Gewinner.
Berechnet die Fahrstrecke pro Verein im Ist-Zustand vs. Szenario A.
"""

import csv
import os
import sys

# Pfadkonfiguration (angepasst an src/eval/ Struktur)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) # src/eval
SRC_DIR = os.path.dirname(CURRENT_DIR)                   # src
PROJECT_ROOT = os.path.dirname(SRC_DIR)                  # hamburg-football-scheduling-ea
DATA_DIR = os.path.join(PROJECT_ROOT, "data")            # data

# Füge src/ea zum Pfad hinzu, um ea_optimizer zu importieren
EA_DIR = os.path.join(SRC_DIR, "ea")
sys.path.append(EA_DIR)

from ea_optimizer import load_data

BASELINE_CSV = os.path.join(DATA_DIR, "hamburg_vereine_geocoded_final.csv")
SCENARIO_A_CSV = os.path.join(DATA_DIR, "optimized_schedule_szenario_A.csv")

def get_team_staffel_mapping(filepath, is_baseline=False):
    """Liest ein CSV ein und gibt ein Dict {Staffel: [Teams]} zurück."""
    staffeln = {}
    with open(filepath, mode='r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader) # Header überspringen
        for row in reader:
            if is_baseline:
                if len(row) < 4 or row[2] == "NICHT GEFUNDEN":
                    continue
                staffel, team = row[0], row[1]
            else:
                staffel, team = row[1], row[2]

            if staffel not in staffeln:
                staffeln[staffel] = []
            staffeln[staffel].append(team)
    return staffeln

def calculate_team_distances(staffeln, dist_matrix):
    """Berechnet die Gesamtkilometer für jedes Team in seiner Staffel."""
    team_distances = {}
    for staffel, teams in staffeln.items():
        for team_a in teams:
            dist = 0.0
            for team_b in teams:
                if team_a != team_b:
                    dist += dist_matrix.get(team_a, {}).get(team_b, 0.0)
            team_distances[team_a] = dist
    return team_distances

def main():
    print("Lade Daten und berechne Distanzen...\n")
    dist_matrix, kk_teams, kl_teams = load_data()

    baseline_staffeln = get_team_staffel_mapping(BASELINE_CSV, is_baseline=True)
    optimzed_staffeln = get_team_staffel_mapping(SCENARIO_A_CSV, is_baseline=False)

    baseline_dist = calculate_team_distances(baseline_staffeln, dist_matrix)
    optimized_dist = calculate_team_distances(optimzed_staffeln, dist_matrix)

    # Vergleiche nur Teams, die in BEIDEN Listen existieren (Kreisklasse)
    results = []
    for team in kk_teams:
        if team in baseline_dist and team in optimized_dist:
            old_dist = baseline_dist[team]
            new_dist = optimized_dist[team]
            saved = old_dist - new_dist
            results.append((team, old_dist, new_dist, saved))

    # Nach Ersparnis absteigend sortieren
    results.sort(key=lambda x: x[3], reverse=True)

    # Saubere Konsolenausgabe
    print("=" * 85)
    print(f"{' TOP 5 GEWINNER: Individuelle Distanzersparnis (Baseline vs. Szenario A)':^85}")
    print("=" * 85)
    print(f"{'Verein':<35} | {'Baseline (km)':>13} | {'Szenario A (km)':>15} | {'Ersparnis (km)':>14}")
    print("-" * 85)

    for i in range(min(5, len(results))):
        team, old, new, saved = results[i]
        print(f"{team:<35} | {old:>13.1f} | {new:>15.1f} | {saved:>14.1f}")

    print("-" * 85)
    print("Hinweis: Diese Analyse zeigt die Vereine mit der größten absoluten Distanzreduktion.")

if __name__ == "__main__":
    main()
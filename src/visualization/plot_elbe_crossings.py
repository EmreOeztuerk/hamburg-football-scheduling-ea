"""
Analyse der verkehrstechnischen Nadelöhre (Elbüberquerungen).

Dieses Modul quantifiziert die Anzahl der notwendigen Flussüberquerungen
(Nord-Süd-Verkehr) im Ist-Zustand (HFV) gegenüber den algorithmisch
optimierten Szenarien. Dies demonstriert die Reduktion von Staurisiken.
"""

import csv
import os
import matplotlib.pyplot as plt

# PLOT-DESIGN (Globales Setup)
ACADEMIC_COLORS = ['#0072B2', '#E69F00', '#009E73', '#D55E00', '#CC79A7', '#56B4E9']

plt.rcParams.update({
    # Farbpalette global setzen
    'axes.prop_cycle': plt.cycler(color=ACADEMIC_COLORS),

    # Cleane, serifenlose Schrift (passt perfekt zum Typst-Standard)
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],

    # Rahmen entfernen (Tufte-Prinzip)
    'axes.spines.top': False,
    'axes.spines.right': False,

    # Dezentes Raster
    'axes.grid': True,
    'grid.alpha': 0.25,
    'grid.linestyle': '--',

    # Typografie
    'axes.titlesize': 13,
    'axes.titleweight': 'bold',
    'axes.labelsize': 11,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,

    # Legende ohne störende Box
    'legend.frameon': False,
    'legend.fontsize': 10,

    # Export-Qualität
    'figure.figsize': (9, 6),
    'savefig.dpi': 300,
    'savefig.bbox': 'tight'  # Verhindert unnötige weiße Ränder
})

# Pfadkonfiguration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

GEO_CSV = os.path.join(DATA_DIR, "hamburg_vereine_geocoded_final.csv")
SCHEDULE_A_CSV = os.path.join(DATA_DIR, "optimized_schedule_szenario_A.csv")
SCHEDULE_B_CSV = os.path.join(DATA_DIR, "optimized_schedule_szenario_B.csv")

# Einheitliche Farbpalette für alle Evaluations-Plots
COLORS = ['#e63946', '#2a9d8f', '#457b9d']
LABELS = ['Baseline\n(Ist-Zustand)', 'Szenario A\n(Struktur-Erhalt)', 'Szenario B\n(Kapazitäts-Limit)']


def is_south_of_elbe(lat: float, lon: float) -> bool:
    """
    Identifiziert die geographische Lage relativ zur Hamburger Elbe.
    Nutzt dieselbe lineare Approximation wie die Distanzmatrix.
    """
    lat_river = -0.2 * (lon - 10.05) + 53.50
    return lat < lat_river


def load_geodata() -> dict:
    """Lädt die GPS-Daten und die originäre Staffelzuordnung (Baseline)."""
    team_geo = {}
    with open(GEO_CSV, mode='r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)
        for row in reader:
            if len(row) >= 4 and row[2] != "NICHT GEFUNDEN":
                team_geo[row[1]] = {
                    "baseline_staffel": row[0],
                    "lat": float(row[2]),
                    "lon": float(row[3])
                }
    return team_geo


def load_optimized_schedule(filepath: str) -> dict:
    """Lädt eine optimierte Staffeleinteilung aus der CSV."""
    staffeln = {}
    with open(filepath, mode='r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)
        for row in reader:
            staffel, team = row[1], row[2]
            if staffel not in staffeln:
                staffeln[staffel] = []
            staffeln[staffel].append(team)
    return staffeln


def count_crossings(staffeln_dict: dict, team_geo: dict) -> int:
    """
    Berechnet die Gesamtzahl der Elbüberquerungen.
    Jede Paarung zweier Teams auf unterschiedlichen Flussseiten
    entspricht 2 Überquerungen (Hin- und Rückspiel).
    """
    total_crossings = 0

    for staffel, teams in staffeln_dict.items():
        # Nur Teams berücksichtigen, für die wir Geodaten haben
        valid_teams = [t for t in teams if t in team_geo]

        for i in range(len(valid_teams)):
            for j in range(i + 1, len(valid_teams)):
                t1 = valid_teams[i]
                t2 = valid_teams[j]

                south1 = is_south_of_elbe(team_geo[t1]["lat"], team_geo[t1]["lon"])
                south2 = is_south_of_elbe(team_geo[t2]["lat"], team_geo[t2]["lon"])

                # Wenn sie auf unterschiedlichen Seiten liegen -> Nadelöhr passiert
                if south1 != south2:
                    total_crossings += 2

    return total_crossings


def main():
    print("Starte Analyse der Nadelöhr-Auslastung (Elbüberquerungen)...")

    team_geo = load_geodata()

    # 1. Baseline aus den Geodaten rekonstruieren
    baseline_staffeln = {}
    for team, data in team_geo.items():
        staffel = data["baseline_staffel"]
        if staffel not in baseline_staffeln:
            baseline_staffeln[staffel] = []
        baseline_staffeln[staffel].append(team)

    crossings_baseline = count_crossings(baseline_staffeln, team_geo)

    # 2. Szenario A laden
    schedule_a = load_optimized_schedule(SCHEDULE_A_CSV)
    crossings_a = count_crossings(schedule_a, team_geo)

    # 3. Szenario B laden
    schedule_b = load_optimized_schedule(SCHEDULE_B_CSV)
    crossings_b = count_crossings(schedule_b, team_geo)

    print(f"HFV Baseline (Ist-Zustand): {crossings_baseline} Überquerungen")
    print(f"Szenario A (EA Optimiert):  {crossings_a} Überquerungen")
    print(f"Szenario B (Konsolidiert):  {crossings_b} Überquerungen")

    # Plot Generierung
    values = [crossings_baseline, crossings_a, crossings_b]

    plt.figure(figsize=(9, 6))
    bars = plt.bar(LABELS, values, color=ACADEMIC_COLORS, width=0.6)

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + (max(values) * 0.02),
                 f"{int(yval)} Fahrten", ha='center', va='bottom', fontsize=11, fontweight='bold')

    plt.title("Auslastung städtischer Nadelöhre (Elbüberquerungen pro Saison)",
              fontsize=14, fontweight='bold', pad=15)
    plt.ylabel("Anzahl der Flussüberquerungen (Hin- & Rückspiel)", fontsize=12)
    plt.ylim(0, max(values) * 1.15)

    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Reduktion in Prozent berechnen und als Subtitel einfügen
    reduction_a = ((crossings_baseline - crossings_a) / crossings_baseline) * 100
    reduction_b = ((crossings_baseline - crossings_b) / crossings_baseline) * 100

    info_text = (f"Reduktion des Verkehrsaufkommens am Elbtunnel / Elbbrücken:\n"
                 f"Szenario A reduziert Überquerungen um {reduction_a:.1f} % | "
                 f"Szenario B um {reduction_b:.1f} %")

    plt.figtext(0.5, 0.02, info_text, ha="center", fontsize=10, style='italic', color='gray')
    plt.subplots_adjust(bottom=0.15)

    output_path = os.path.join(DATA_DIR, "eval_elbe_crossings.png")
    plt.savefig(output_path, dpi=300)
    print(f"\nPlot erfolgreich gespeichert unter: {output_path}")


if __name__ == "__main__":
    main()
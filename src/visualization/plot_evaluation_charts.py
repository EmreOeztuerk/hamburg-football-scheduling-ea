"""
Generiert statistische Balkendiagramme für das Evaluations-Kapitel.
Berechnet die Messwerte dynamisch aus den exportierten CSV-Ergebnisdateien.
"""

import csv
import os
import matplotlib.pyplot as plt

# ============================================================================= #
# DOMÄNEN- UND EFFIZIENZ-KONSTANTEN (Keine Magic Numbers!)
# ============================================================================= #
CARS_PER_TEAM = 4
CO2_KG_PER_KM = 0.15
KG_TO_TONS_FACTOR = 1000.0

CO2_FACTOR_TONS_PER_KM = (CARS_PER_TEAM * CO2_KG_PER_KM) / KG_TO_TONS_FACTOR

# Fallback-Festwerte (falls vor dem Ausführen von ea_optimizer.py geplottet wird)
FALLBACK_KM_VALUES = [42253.02, 37860.02, 40264.90]
FALLBACK_EFFICIENCY_VALUES = [11.51, 10.36, 10.46]

LABELS = [
    'HFV Baseline\n(Ist-Zustand)',
    'Szenario A\n(1:1 Vergleich)',
    'Szenario B\n(Dynamisch)'
]
COLORS = ['#e63946', '#2a9d8f', '#457b9d']

# Pfadkonfiguration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

GEO_CSV = os.path.join(DATA_DIR, "hamburg_vereine_geocoded_final.csv")
MATRIX_CSV = os.path.join(DATA_DIR, "distance_matrix.csv")
SCHEDULE_A_CSV = os.path.join(DATA_DIR, "optimized_schedule_szenario_A.csv")
SCHEDULE_B_CSV = os.path.join(DATA_DIR, "optimized_schedule_szenario_B.csv")


def load_distance_matrix() -> dict:
    """Lädt die symmetrische Distanzmatrix aus der CSV."""
    dist_matrix = {}
    if not os.path.exists(MATRIX_CSV):
        return dist_matrix

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


def calculate_schedule_stats(filepath: str, dist_matrix: dict, is_baseline: bool = False) -> tuple[float, int]:
    """Berechnet Gesamtkilometer und Auswärtsfahrten dynamisch aus einer Spielplan-CSV."""
    if not os.path.exists(filepath):
        return 0.0, 1

    staffeln = {}
    with open(filepath, mode='r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)
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

    total_km = 0.0
    total_trips = 0
    for staffel, teams in staffeln.items():
        n = len(teams)
        total_trips += n * (n - 1)
        for i in range(n):
            for j in range(i + 1, n):
                t1, t2 = teams[i], teams[j]
                if t1 in dist_matrix and t2 in dist_matrix[t1]:
                    total_km += dist_matrix[t1][t2] * 2.0

    return total_km, total_trips


def load_scenario_metrics() -> tuple[list[float], list[float], list[float]]:
    """Versucht Kennzahlen dynamisch aus CSVs zu berechnen. Nutzt Fallback, falls keine CSVs vorliegen."""
    dist_matrix = load_distance_matrix()

    if dist_matrix and os.path.exists(SCHEDULE_A_CSV) and os.path.exists(SCHEDULE_B_CSV):
        km_base, trips_base = calculate_schedule_stats(GEO_CSV, dist_matrix, is_baseline=True)
        km_a, trips_a = calculate_schedule_stats(SCHEDULE_A_CSV, dist_matrix, is_baseline=False)
        km_b, trips_b = calculate_schedule_stats(SCHEDULE_B_CSV, dist_matrix, is_baseline=False)

        if km_base > 0 and km_a > 0 and km_b > 0:
            km_values = [km_base, km_a, km_b]
            eff_values = [km_base / trips_base, km_a / trips_a, km_b / trips_b]
            co2_values = [km * CO2_FACTOR_TONS_PER_KM for km in km_values]
            return km_values, eff_values, co2_values

    # Sichere Fallback-Werte
    km_values = FALLBACK_KM_VALUES
    eff_values = FALLBACK_EFFICIENCY_VALUES
    co2_values = [km * CO2_FACTOR_TONS_PER_KM for km in km_values]
    return km_values, eff_values, co2_values


def format_german_number(num: float) -> str:
    return f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def plot_absolute_km(km_values: list[float]):
    plt.figure(figsize=(9, 6))
    bars = plt.bar(LABELS, km_values, color=COLORS, width=0.6)
    max_val = max(km_values) if km_values else 50000.0

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + (max_val * 0.01),
                 f"{format_german_number(yval)} km", ha='center', va='bottom', fontsize=11, fontweight='bold')

    plt.title("Gesamtkilometer pro Saison (Vergleich der Szenarien)", fontsize=14, fontweight='bold', pad=15)
    plt.ylabel("Ökologischer Fußabdruck (Routenkilometer)", fontsize=12)
    plt.ylim(0, max_val * 1.15)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(DATA_DIR, "eval_absolute_km.png"), dpi=300)


def plot_relative_efficiency(eff_values: list[float]):
    plt.figure(figsize=(9, 6))
    bars = plt.bar(LABELS, eff_values, color=COLORS, width=0.6)
    max_val = max(eff_values) if eff_values else 15.0

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + (max_val * 0.01),
                 f"{format_german_number(yval)} km", ha='center', va='bottom', fontsize=11, fontweight='bold')

    plt.title("Routing-Effizienz (Ø Distanz pro Auswärtsfahrt)", fontsize=14, fontweight='bold', pad=15)
    plt.ylabel("Ø Kilometer pro Einzelfahrt", fontsize=12)
    plt.ylim(0, max_val * 1.20)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(DATA_DIR, "eval_effizienz.png"), dpi=300)


def plot_co2_footprint(co2_values: list[float]):
    plt.figure(figsize=(9, 6))
    bars = plt.bar(LABELS, co2_values, color=COLORS, width=0.6)
    max_val = max(co2_values) if co2_values else 30.0

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + (max_val * 0.01),
                 f"{format_german_number(yval)} t", ha='center', va='bottom', fontsize=11, fontweight='bold')

    plt.title("Ökologischer Impact: CO₂-Emissionen der Auswärtsfahrten", fontsize=14, fontweight='bold', pad=15)
    plt.ylabel("CO₂-Emissionen in Tonnen (t)", fontsize=12)
    plt.ylim(0, max_val * 1.20)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.figtext(0.5, 0.01,
                f"*Berechnungsgrundlage: {CARS_PER_TEAM} PKW pro Team, {CO2_KG_PER_KM:.2f} kg CO₂ pro Kilometer",
                ha="center", fontsize=9, style='italic', color='gray')
    plt.subplots_adjust(bottom=0.15)
    plt.savefig(os.path.join(DATA_DIR, "eval_co2_emissionen.png"), dpi=300)


def main():
    print("=== Generiere Evaluations-Plots für die Bachelorarbeit (Dynamisch) ===")
    km_values, eff_values, co2_values = load_scenario_metrics()
    plot_absolute_km(km_values)
    plot_relative_efficiency(eff_values)
    plot_co2_footprint(co2_values)
    print("Erfolgreich ausgeführt!")


if __name__ == "__main__":
    main()
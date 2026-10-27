"""
Visualisierung der Problemkomplexität (Laufzeitvergleich).
Berechnet die Stirling-Zahlen zweiter Art für das Partitionierungsproblem
(153 Teams in 12 Staffeln) und vergleicht die Brute-Force-Laufzeit eines Supercomputers
mit der Konvergenzzeit des Evolutionären Algorithmus.
"""

import math
import os
import matplotlib.pyplot as plt

# PLOT-DESIGN (Globales Setup)
ACADEMIC_COLORS = ['#0072B2', '#E69F00', '#009E73', '#D55E00', '#CC79A7', '#56B4E9']
plt.rcParams.update({
    'axes.prop_cycle': plt.cycler(color=ACADEMIC_COLORS),
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.alpha': 0.25,
    'grid.linestyle': '--',
    'axes.titlesize': 13,
    'axes.titleweight': 'bold',
    'axes.labelsize': 11,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.frameon': False,
    'legend.fontsize': 10,
    'figure.figsize': (9, 6),
    'savefig.dpi': 300,
    'savefig.bbox': 'tight'
})

# Pfadkonfiguration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

NUM_KK_TEAMS = 153
NUM_KK_STAFFELN = 12
SUPERCOMPUTER_OPS_PER_SEC = 1_000_000_000
AGE_OF_UNIVERSE_YEARS = 13_800_000_000
EA_RUNTIME_SECONDS = 300

def stirling_second(n: int, k: int) -> int:
    """Berechnet die Stirling-Zahl zweiter Art S(n, k)."""
    total = 0
    for j in range(k + 1):
        sign = (-1) ** (k - j)
        term = sign * math.comb(k, j) * (j ** n)
        total += term
    return total // math.factorial(k)

def main():
    print("Berechne mathematische Komplexität (Stirling-Zahlen)...")
    combinations = stirling_second(NUM_KK_TEAMS, NUM_KK_STAFFELN)
    print(f"\nMögliche Spielpläne (Kombinationen): {combinations}")

    seconds_needed = combinations / SUPERCOMPUTER_OPS_PER_SEC
    years_needed = seconds_needed / (60 * 60 * 24 * 365)
    age_of_universe = AGE_OF_UNIVERSE_YEARS
    ea_runtime_years = EA_RUNTIME_SECONDS / (60 * 60 * 24 * 365)

    print(f"Brute-Force Dauer (Jahre): {years_needed:.2e}")

    plt.figure(figsize=(10, 6))
    labels = [
        'Evolutionärer Algorithmus\n(~20 Minuten)',
        'Alter des Universums\n(13,8 Mrd. Jahre)',
        'Brute-Force Supercomputer\n(1 Mrd. Checks/Sek)'
    ]

    values_in_years = [ea_runtime_years, age_of_universe, years_needed]
    plt.bar(labels, values_in_years, color=ACADEMIC_COLORS[:3], width=0.6)
    plt.yscale('log')
    plt.title("Laufzeit-Komplexität: EA vs. Brute-Force (153 Teams in 12 Staffeln)",
              fontsize=14, fontweight='bold', pad=20)
    plt.ylabel("Benötigte Rechenzeit in Jahren (Logarithmische Skala)", fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.5)

    plt.text(0, ea_runtime_years * 1.5, "~ 20 Minuten", ha='center', va='bottom', fontsize=11, fontweight='bold')
    plt.text(1, age_of_universe * 1.5, "1.38 × 10^10 Jahre", ha='center', va='bottom', fontsize=11, fontweight='bold')
    plt.text(2, years_needed * 1.5, f"~10^{int(math.log10(years_needed))} Jahre", ha='center', va='bottom', fontsize=11, fontweight='bold')

    info_text = (
        f"Mathematischer Lösungsraum: S({NUM_KK_TEAMS}, {NUM_KK_STAFFELN}) ≈ 10^{int(math.log10(combinations))} Kombinationen\n"
        "Fazit: Die optimale Lösung ist durch menschliche Planung \noder reines Ausprobieren unmöglich zu finden."
    )
    plt.figtext(0.5, 0.02, info_text, ha="center", fontsize=10, style='italic',
                bbox={"facecolor": "white", "alpha": 0.8, "pad": 5, "edgecolor": "gray"})
    plt.subplots_adjust(bottom=0.2)

    output_path = os.path.join(DATA_DIR, "eval_complexity.png")
    plt.savefig(output_path, dpi=300)
    print(f"\nPlot erfolgreich gespeichert unter: {output_path}")

if __name__ == "__main__":
    main()
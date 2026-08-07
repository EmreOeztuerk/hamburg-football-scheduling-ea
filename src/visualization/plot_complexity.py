"""
Visualisierung der Problemkomplexität (Laufzeitvergleich).

Berechnet die Stirling-Zahlen zweiter Art für das Partitionierungsproblem
(160 Teams in 12 Staffeln) und vergleicht die Brute-Force-Laufzeit eines
Supercomputers mit der Konvergenzzeit des Evolutionären Algorithmus.
"""

import math
import matplotlib.pyplot as plt
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

# Pfadkonfiguratiion
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


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

    # 160 Kreisklassen-Teams auf 12 Staffeln
    n_teams = 160
    k_staffeln = 12

    combinations = stirling_second(n_teams, k_staffeln)
    print(f"\nMögliche Spielpläne (Kombinationen): {combinations}")

    # Annahme: Ein Supercomputer prüft 1.000.000.000 (1 Milliarde) Pläne pro Sekunde
    supercomputer_speed = 1_000_000_000
    seconds_needed = combinations / supercomputer_speed
    years_needed = seconds_needed / (60 * 60 * 24 * 365)

    # Alter des Universums zum Vergleich (ca. 13.8 Milliarden Jahre)
    age_of_universe = 13_800_000_000

    # Laufzeit unseres EA (Großzügig auf 60 Sekunden gerundet für den Plot)
    ea_runtime_seconds = 300
    ea_runtime_years = ea_runtime_seconds / (60 * 60 * 24 * 365)

    print(f"Brute-Force Dauer (Jahre): {years_needed:.2e}")

    # Plot
    plt.figure(figsize=(10, 6))

    labels = ['Evolutionärer Algorithmus\n(~60 Sekunden)',
              'Alter des Universums\n(13,8 Mrd. Jahre)',
              'Brute-Force Supercomputer\n(1 Mrd. Checks/Sek)']

    # Wir nutzen Logarithmus zur Basis 10 für die Y-Achse,
    # da die Werte sonst nicht in ein Diagramm passen.
    values_in_years = [ea_runtime_years, age_of_universe, years_needed]
    colors = ['#2a9d8f', '#e9c46a', '#e63946']

    bars = plt.bar(labels, values_in_years, color=ACADEMIC_COLORS, width=0.6)

    plt.yscale('log')
    plt.title("Laufzeit-Komplexität: EA vs. Brute-Force (160 Teams in 12 Staffeln)",
              fontsize=14, fontweight='bold', pad=20)
    plt.ylabel("Benötigte Rechenzeit in Jahren (Logarithmische Skala!)", fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.5)

    # Eigene Beschriftungen für die Extremwerte
    plt.text(0, ea_runtime_years * 1.5, "1 Minute", ha='center', va='bottom', fontsize=11, fontweight='bold')
    plt.text(1, age_of_universe * 1.5, "1.38 × 10^10 Jahre", ha='center', va='bottom', fontsize=11, fontweight='bold')
    plt.text(2, years_needed * 1.5, f"~10^{int(math.log10(years_needed))} Jahre", ha='center', va='bottom', fontsize=11,
             fontweight='bold')

    # Kleine Erklärungsbox
    info_text = (
        f"Mathematischer Lösungsraum: S({n_teams}, {k_staffeln}) ≈ 10^{int(math.log10(combinations))} Kombinationen\n"
        "Fazit: Die optimale Lösung ist durch menschliche Planung \noder reines Ausprobieren unmöglich zu finden.")
    plt.figtext(0.5, 0.02, info_text, ha="center", fontsize=10, style='italic',
                bbox={"facecolor": "white", "alpha": 0.8, "pad": 5, "edgecolor": "gray"})

    plt.subplots_adjust(bottom=0.2)

    output_path = os.path.join(DATA_DIR, "eval_complexity.png")
    plt.savefig(output_path, dpi=300)
    print(f"\nPlot erfolgreich gespeichert unter: {output_path}")


if __name__ == "__main__":
    main()
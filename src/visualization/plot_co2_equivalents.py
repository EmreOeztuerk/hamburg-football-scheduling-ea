"""
Visualisierung der ökologischen Äquivalente (Greifbarkeit).

Übersetzt die vom EA eingesparten CO2-Emissionen in alltagsnahe,
greifbare Metriken, um den gesellschaftlichen und ökologischen Impact
der Algorithmus-Implementierung zu verdeutlichen.
"""

import matplotlib.pyplot as plt
import os

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

# Brechnungsgrundlage (Szenario A vs. Baseline)
BASELINE_KM = 42253.02
EA_KM = 39687.45
SAVED_KM = BASELINE_KM - EA_KM

# 4 PKW pro Auswärtsmannschaft, 0.15 kg CO2 pro gefahrenem Kilometer
SAVED_CO2_KG = SAVED_KM * 4 * 0.15

# Äquivalent-Faktoren (kg CO2 pro Einheit)
FACTOR_TREE = 12.5  # Eine ausgewachsene Buche bindet ca. 12.5 kg CO2 pro Jahr
FACTOR_BEEF = 13.3  # Produktion von 1 kg Rindfleisch erzeugt ca. 13.3 kg CO2
FACTOR_FLIGHT = 250.0  # Flug Hamburg -> Mallorca (pro Passagier) ca. 250 kg CO2
FACTOR_MUNICH = 120.0  # Autofahrt Hamburg -> München (ca. 800 km) ca. 120 kg CO2


def main():
    print(f"Ermittelte CO2-Einsparung: {SAVED_CO2_KG:,.2f} kg".replace(",", "."))

    # Berechnungen der Äquivalente
    trees_needed = SAVED_CO2_KG / FACTOR_TREE
    beef_kg = SAVED_CO2_KG / FACTOR_BEEF
    flights = SAVED_CO2_KG / FACTOR_FLIGHT
    munich_trips = SAVED_CO2_KG / FACTOR_MUNICH

    # Daten für den Plot vorbereiten
    labels = [
        'Jahres-CO2-Bindung\nvon Buchen (Bäume)',
        'Produktion von\nRindfleisch (in kg)',
        'Autofahrten von\nHamburg nach München',
        'Flüge (pro Passagier)\nHamburg -> Mallorca'
    ]

    values = [trees_needed, beef_kg, munich_trips, flights]

    # Farben im professionellen Layout-Schema
    colors = ['#2a9d8f', '#e63946', '#e9c46a', '#457b9d']

    # Plot Generierung (Horizontales Balkendiagramm für bessere Lesbarkeit)
    plt.figure(figsize=(10, 6))

    # Wir drehen die Listen um, damit der größte Wert oben im Plot steht
    y_pos = range(len(labels))
    bars = plt.barh(y_pos, values[::-1], color=colors[::-1], height=0.6)

    plt.yticks(y_pos, labels[::-1], fontsize=11)

    # Werte direkt rechts neben den Balken anzeigen
    for bar in bars:
        width = bar.get_width()
        plt.text(width + (max(values) * 0.02), bar.get_y() + bar.get_height() / 2,
                 f"{int(round(width))}x",
                 ha='left', va='center', fontsize=12, fontweight='bold')

    plt.title(f"Greifbarkeit der Einsparung ({SAVED_CO2_KG:,.0f} kg CO2 pro Saison)".replace(",", "."),
              fontsize=14, fontweight='bold', pad=20)
    plt.xlabel("Menge / Anzahl der Einheiten", fontsize=12)

    # Rechten und oberen Rand ausblenden (für einen moderneren, cleaneren Look)
    ax = plt.gca()
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    # Maximalwert der X-Achse leicht erhöhen, damit die Texte nicht abgeschnitten werden
    plt.xlim(0, max(values) * 1.15)

    plt.tight_layout()

    output_path = os.path.join(DATA_DIR, "eval_co2_tangible.png")
    plt.savefig(output_path, dpi=300)
    print(f"Plot erfolgreich gespeichert unter: {output_path}")


if __name__ == "__main__":
    main()
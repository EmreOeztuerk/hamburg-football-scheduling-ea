"""
Generiert statistische Balkendiagramme für das Evaluations-Kapitel.
Nutzt die final ermittelten Festwerte aus der Szenario-Analyse.
"""

import matplotlib.pyplot as plt
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

LABELS = ['HFV Baseline\n(Ist-Zustand)', 'Szenario A\n(1:1 Vergleich)', 'Szenario B\n(Dynamisch)']
COLORS = ['#e63946', '#2a9d8f', '#457b9d']

# NEUE WERTE AUS DEM LETZTEN RUN
KM_VALUES = [42253.02, 37860.02, 40264.90]
EFFICIENCY_VALUES = [11.51, 10.36, 10.46]

CO2_FACTOR = (4 * 0.15) / 1000
CO2_VALUES = [km * CO2_FACTOR for km in KM_VALUES]

def format_german_number(num):
    return f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def plot_absolute_km():
    plt.figure(figsize=(9, 6))
    bars = plt.bar(LABELS, KM_VALUES, color=COLORS, width=0.6)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 500,
                 f"{format_german_number(yval)} km", ha='center', va='bottom', fontsize=11, fontweight='bold')
    plt.title("Gesamtkilometer pro Saison (Vergleich der Szenarien)", fontsize=14, fontweight='bold', pad=15)
    plt.ylabel("Ökologischer Fußabdruck (Routenkilometer)", fontsize=12)
    plt.ylim(0, 48000)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(DATA_DIR, "eval_absolute_km.png"), dpi=300)

def plot_relative_efficiency():
    plt.figure(figsize=(9, 6))
    bars = plt.bar(LABELS, EFFICIENCY_VALUES, color=COLORS, width=0.6)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.2,
                 f"{format_german_number(yval)} km", ha='center', va='bottom', fontsize=11, fontweight='bold')
    plt.title("Routing-Effizienz (Ø Distanz pro Auswärtsfahrt)", fontsize=14, fontweight='bold', pad=15)
    plt.ylabel("Ø Kilometer pro Einzelfahrt", fontsize=12)
    plt.ylim(0, 13)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(os.path.join(DATA_DIR, "eval_effizienz.png"), dpi=300)

def plot_co2_footprint():
    plt.figure(figsize=(9, 6))
    bars = plt.bar(LABELS, CO2_VALUES, color=COLORS, width=0.6)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.3,
                 f"{format_german_number(yval)} t", ha='center', va='bottom', fontsize=11, fontweight='bold')
    plt.title("Ökologischer Impact: CO₂-Emissionen der Auswärtsfahrten", fontsize=14, fontweight='bold', pad=15)
    plt.ylabel("CO₂-Emissionen in Tonnen (t)", fontsize=12)
    plt.ylim(0, max(CO2_VALUES) + 5)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.figtext(0.5, 0.01, "*Berechnungsgrundlage: 4 PKW pro Team, 0,15 kg CO₂ pro Kilometer",
                ha="center", fontsize=9, style='italic', color='gray')
    plt.subplots_adjust(bottom=0.15)
    plt.savefig(os.path.join(DATA_DIR, "eval_co2_emissionen.png"), dpi=300)

def main():
    print("=== Generiere Evaluations-Plots für die Bachelorarbeit ===")
    plot_absolute_km()
    plot_relative_efficiency()
    plot_co2_footprint()

if __name__ == "__main__":
    main()
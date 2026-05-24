"""
Analyse der Populationsdynamik und Konvergenzstabilität (Boxplots).

Dieses Modul führt einen exemplarischen Lauf des Evolutionären Algorithmus durch
und protokolliert die Fitness-Verteilung (Varianz) der gesamten Population
zu definierten Meilensteinen (Generationen). Es demonstriert den Selektionsdruck
und die methodische Robustheit des Algorithmus.
"""

import os
import sys
import copy
import random
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

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

# Pfadkonfiguration & Imports aus dem EA-Modul
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
EA_DIR = os.path.join(SRC_DIR, "ea")

# Wir fügen den EA-Ordner zum Python-Pfad hinzu, um die Funktionen zu importieren
sys.path.append(EA_DIR)
from ea_optimizer import (
    load_data, calculate_fitness, tournament_selection,
    order_crossover, swap_mutation, POPULATION_SIZE,
    ELITISM_RATE, MUTATION_RATE, GENERATIONS
)


def run_ea_and_collect_distributions(teams: list, num_staffeln: int, dist_matrix: dict) -> dict:
    """Führt den EA aus und extrahiert die Populations-Verteilung an Meilensteinen."""
    population = []
    for _ in range(POPULATION_SIZE):
        ind = copy.deepcopy(teams)
        random.shuffle(ind)
        population.append(ind)

    distributions = {}

    # Wir erfassen die Daten bei Generation 0, 500, 1000 und 1500
    milestones = [0, 500, 1000, GENERATIONS]

    print("Starte EA-Durchlauf zur Erfassung der Populationsdynamik...")

    for gen in range(GENERATIONS + 1):
        pop_with_fitness = [(ind, calculate_fitness(ind, num_staffeln, dist_matrix)) for ind in population]
        pop_with_fitness.sort(key=lambda x: x[1])

        # Datenpunkt erfassen, wenn ein Meilenstein erreicht ist
        if gen in milestones:
            # Speichere die Gesamtkilometer aller 50 Individuen
            distributions[gen] = [fit for _, fit in pop_with_fitness]
            print(
                f" -> Generation {gen:4d} erfasst | Bester Plan: {distributions[gen][0]:,.2f} km | Schlechtester Plan: {distributions[gen][-1]:,.2f} km")

        if gen == GENERATIONS:
            break

        # Evolutionärer Schritt
        elite_count = int(POPULATION_SIZE * ELITISM_RATE)
        next_population = [ind for ind, fit in pop_with_fitness[:elite_count]]

        while len(next_population) < POPULATION_SIZE:
            p1 = tournament_selection(pop_with_fitness, k=3)
            p2 = tournament_selection(pop_with_fitness, k=3)
            child = order_crossover(p1, p2)
            swap_mutation(child, MUTATION_RATE)
            next_population.append(child)

        population = next_population

    return distributions


def main():
    print("=== Populationsdynamik-Analyse (Boxplot) ===")
    dist_matrix, kk_teams, _ = load_data()

    # Wir testen die Populationsdynamik am Beispiel der Kreisklasse (Szenario A)
    num_staffeln = 12
    distributions = run_ea_and_collect_distributions(kk_teams, num_staffeln, dist_matrix)

    # Plot Generierung (Boxplots)
    plt.figure(figsize=(10, 6))

    # Daten für den Boxplot vorbereiten
    plot_data = [distributions[0], distributions[500], distributions[1000], distributions[1500]]
    labels = ['Generation 0\n(Initialisierung)', 'Generation 500', 'Generation 1000', 'Generation 1500\n(Konvergenz)']

    # Boxplot zeichnen mit professionellem Styling
    box = plt.boxplot(plot_data, patch_artist=True, tick_labels=labels,
                      boxprops=dict(facecolor='#457b9d', color='#1d3557', linewidth=1.5),
                      capprops=dict(color='#1d3557', linewidth=1.5),
                      whiskerprops=dict(color='#1d3557', linewidth=1.5),
                      flierprops=dict(marker='o', markerfacecolor='#e63946', markersize=5, alpha=0.5),
                      medianprops=dict(color='#e9c46a', linewidth=2.5))

    plt.title("Populationsdynamik und Selektionsdruck des EA (Szenario A)",
              fontsize=14, fontweight='bold', pad=15)
    plt.ylabel("Ökologischer Fußabdruck (Gesamtkilometer)", fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Y-Achse deutsch formatieren
    ax = plt.gca()
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',').replace(',', '.')))

    # Erklärende Subtitle-Box
    info_text = ("Die Boxen zeigen die Streuung der 50 Spielpläne pro Generation.\n"
                 "Die starke Reduktion der Varianz (Größe der Box) beweist die systematische Konvergenz\n"
                 "des Algorithmus und schließt eine rein zufällige Lösungsfindung aus.")
    plt.figtext(0.5, 0.02, info_text, ha="center", fontsize=10, style='italic',
                bbox={"facecolor": "white", "alpha": 0.8, "pad": 5, "edgecolor": "gray"})

    plt.subplots_adjust(bottom=0.2)

    output_path = os.path.join(DATA_DIR, "eval_population_boxplot.png")
    plt.savefig(output_path, dpi=300)
    print(f"\nPlot erfolgreich gespeichert unter: {output_path}")


if __name__ == "__main__":
    main()
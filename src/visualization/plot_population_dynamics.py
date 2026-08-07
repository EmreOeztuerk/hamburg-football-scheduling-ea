"""
Analyse der Populationsdynamik und Konvergenzstabilität (Boxplots).
Inklusive dynamischer Mutationsrate nach Zhu (2022).
"""

import os
import sys
import copy
import random
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

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

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
EA_DIR = os.path.join(SRC_DIR, "ea")

sys.path.append(EA_DIR)
from ea_optimizer import (
    load_data, calculate_fitness, tournament_selection,
    order_crossover, swap_mutation, POPULATION_SIZE,
    ELITISM_RATE, MUTATION_RATE_MIN, MUTATION_RATE_MAX,
    STAGNATION_LIMIT, GENERATIONS
)

def run_ea_and_collect_distributions(teams: list, num_staffeln: int, dist_matrix: dict) -> dict:
    population = []
    for _ in range(POPULATION_SIZE):
        ind = copy.deepcopy(teams)
        random.shuffle(ind)
        population.append(ind)

    distributions = {}
    # NEUE Meilensteine, passend zu 4000 Generationen
    milestones = [0, 1000, 2500, GENERATIONS]

    print("Starte EA-Durchlauf zur Erfassung der Populationsdynamik...")

    best_overall = float('inf')
    current_mutation_rate = MUTATION_RATE_MIN
    stagnation_counter = 0

    for gen in range(GENERATIONS + 1):
        pop_with_fitness = [(ind, calculate_fitness(ind, num_staffeln, dist_matrix)) for ind in population]
        pop_with_fitness.sort(key=lambda x: x[1])

        current_best = pop_with_fitness[0][1]

        # Dynamische Logik integrieren
        if current_best < best_overall:
            best_overall = current_best
            stagnation_counter = 0
            current_mutation_rate = MUTATION_RATE_MIN
        else:
            stagnation_counter += 1

        if stagnation_counter > STAGNATION_LIMIT:
            current_mutation_rate = min(MUTATION_RATE_MAX, current_mutation_rate + 0.15)
            stagnation_counter = 0

        if gen in milestones:
            distributions[gen] = [fit for _, fit in pop_with_fitness]
            print(f" -> Generation {gen:4d} erfasst | Bester Plan: {distributions[gen][0]:,.2f} km | Schlechtester: {distributions[gen][-1]:,.2f} km")

        if gen == GENERATIONS:
            break

        elite_count = int(POPULATION_SIZE * ELITISM_RATE)
        next_population = [ind for ind, fit in pop_with_fitness[:elite_count]]

        while len(next_population) < POPULATION_SIZE:
            p1 = tournament_selection(pop_with_fitness, k=3)
            p2 = tournament_selection(pop_with_fitness, k=3)
            child = order_crossover(p1, p2)
            swap_mutation(child, current_mutation_rate) # Dynamische Rate nutzen!
            next_population.append(child)

        population = next_population

    return distributions

def main():
    print("=== Populationsdynamik-Analyse (Boxplot) ===")
    dist_matrix, kk_teams, _ = load_data()

    num_staffeln = 12
    distributions = run_ea_and_collect_distributions(kk_teams, num_staffeln, dist_matrix)

    plt.figure(figsize=(10, 6))

    # Plot-Daten an neue Meilensteine anpassen
    plot_data = [distributions[0], distributions[1000], distributions[2500], distributions[GENERATIONS]]
    labels = ['Generation 0\n(Initialisierung)', 'Generation 1000', 'Generation 2500', f'Generation {GENERATIONS}\n']

    box = plt.boxplot(plot_data, patch_artist=True, tick_labels=labels,
                      boxprops=dict(facecolor='#457b9d', color='#1d3557', linewidth=1.5),
                      capprops=dict(color='#1d3557', linewidth=1.5),
                      whiskerprops=dict(color='#1d3557', linewidth=1.5),
                      flierprops=dict(marker='o', markerfacecolor='#e63946', markersize=5, alpha=0.5),
                      medianprops=dict(color='#e9c46a', linewidth=2.5))

    plt.title("Populationsdynamik und Selektionsdruck des EA (Szenario A)", fontsize=14, fontweight='bold', pad=15)
    plt.ylabel("Ökologischer Fußabdruck (Gesamtkilometer)", fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    ax = plt.gca()
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',').replace(',', '.')))

    info_text = (f"Die Boxen zeigen die Streuung der {POPULATION_SIZE} Spielpläne pro erfasster Generation.\n"
                 "Die starke Reduktion der Varianz beweist die systematische Konvergenz\n"
                 "des Algorithmus und schließt eine rein zufällige Lösungsfindung aus.")
    plt.figtext(0.5, 0.02, info_text, ha="center", fontsize=10, style='italic',
                bbox={"facecolor": "white", "alpha": 0.8, "pad": 5, "edgecolor": "gray"})

    plt.subplots_adjust(bottom=0.2)
    output_path = os.path.join(DATA_DIR, "eval_population_boxplot.png")
    plt.savefig(output_path, dpi=300)
    print(f"\nPlot erfolgreich gespeichert unter: {output_path}")

if __name__ == "__main__":
    main()
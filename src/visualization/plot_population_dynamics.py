"""
Analyse der Populationsdynamik und Konvergenzstabilität (Boxplots).
Erfasst die Fitnessverteilung der Population in 500er-Schritten über 5.000 Generationen.
"""

import os
import sys
import random
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
EA_DIR = os.path.join(SRC_DIR, "ea")

if EA_DIR not in sys.path:
    sys.path.append(EA_DIR)

from ea_optimizer import (
    load_data, calculate_fitness, tournament_selection,
    order_crossover, swap_mutation
)

ACADEMIC_COLORS = ['#0072B2', '#E69F00', '#009E73', '#D55E00']

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.alpha': 0.25,
    'grid.linestyle': '--',
    'figure.figsize': (12, 6),
    'savefig.dpi': 300,
    'savefig.bbox': 'tight'
})

POPULATION_SIZE = 300
GENERATIONS = 5000
STEP_SIZE = 1000


def run_ea_and_collect_distributions(teams: list, staffel_sizes: list, dist_matrix: dict) -> tuple[dict, list]:
    population = [random.sample(teams, len(teams)) for _ in range(POPULATION_SIZE)]
    distributions = {}

    # Meilensteine in 500er-Schritten (0, 500, 1000, ..., 5000)
    milestones = list(range(0, GENERATIONS + 1, STEP_SIZE))

    best_overall = float('inf')
    current_mutation_rate = 0.10
    stagnation_counter = 0

    print(f"Starte EA-Durchlauf zur Erfassung der Populationsdynamik (5.000 Gen., 500er-Schritte)...")

    for gen in range(GENERATIONS + 1):
        pop_with_fitness = [(ind, calculate_fitness(ind, staffel_sizes, dist_matrix)) for ind in population]
        pop_with_fitness.sort(key=lambda x: x[1])
        current_best = pop_with_fitness[0][1]

        if current_best < best_overall:
            best_overall = current_best
            stagnation_counter = 0
            current_mutation_rate = 0.10
        else:
            stagnation_counter += 1

        if stagnation_counter > 50:
            current_mutation_rate = min(0.85, current_mutation_rate + 0.15)
            stagnation_counter = 0

        if gen in milestones:
            distributions[gen] = [fit for _, fit in pop_with_fitness]
            print(f" -> Generation {gen:4d} erfasst | Bester: {distributions[gen][0]:,.2f} km")

        if gen == GENERATIONS:
            break

        elite_count = max(1, int(POPULATION_SIZE * 0.05))
        next_population = [ind for ind, _ in pop_with_fitness[:elite_count]]

        while len(next_population) < POPULATION_SIZE:
            p1 = tournament_selection(pop_with_fitness, k=3)
            p2 = tournament_selection(pop_with_fitness, k=3)
            child = order_crossover(p1, p2)
            swap_mutation(child, current_mutation_rate)
            next_population.append(child)

        population = next_population

    return distributions, milestones


def main():
    print("=== Populationsdynamik-Analyse (Boxplot in 1000er-Schritten) ===")
    dist_matrix, kk_teams, _, kk_caps_a, _ = load_data()

    distributions, milestones = run_ea_and_collect_distributions(kk_teams, kk_caps_a, dist_matrix)

    plt.figure(figsize=(12, 6))
    plot_data = [distributions[m] for m in milestones]
    labels = [f"Gen {m}" if m > 0 else "Gen 0\n(Start)" for m in milestones]

    plt.boxplot(plot_data, patch_artist=True, tick_labels=labels,
                boxprops=dict(facecolor='#457b9d', color='#1d3557', linewidth=1.2),
                capprops=dict(color='#1d3557', linewidth=1.2),
                whiskerprops=dict(color='#1d3557', linewidth=1.2),
                flierprops=dict(marker='o', markerfacecolor='#e63946', markersize=3, alpha=0.3),
                medianprops=dict(color='#e9c46a', linewidth=2.0))

    plt.title("Populationsdynamik und Selektionsdruck des EA (Kreisklasse Szenario A)", fontsize=13, fontweight='bold', pad=15)
    plt.ylabel("Ökologischer Fußabdruck (Gesamtkilometer)", fontsize=11)
    plt.xticks(fontsize=9, rotation=30)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    ax = plt.gca()
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: f"{int(x):,}".replace(',', '.')))

    output_path = os.path.join(DATA_DIR, "eval_population_boxplot.png")
    plt.savefig(output_path, dpi=300)
    print(f"\n✓ Plot erfolgreich gespeichert unter: {output_path}")


if __name__ == "__main__":
    main()
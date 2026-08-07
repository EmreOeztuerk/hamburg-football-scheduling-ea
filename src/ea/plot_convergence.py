"""
Statistische Analyse des Konvergenzverhaltens mit dynamischer Mutation.
"""

import os
import random
import copy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from ea_optimizer import (
    load_data, calculate_fitness, tournament_selection,
    order_crossover, swap_mutation
)

# Pfadkonfiguration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# NEUE Parameter (angepasst an den finalen Run)
POPULATION_SIZE = 300
GENERATIONS = 5000
ELITISM_RATE = 0.05
MUTATION_RATE_MIN = 0.1
MUTATION_RATE_MAX = 0.85
STAGNATION_LIMIT = 50

def run_experiment_history(teams: list, num_staffeln: int, dist_matrix: dict) -> tuple[list, list]:
    """Führt eine Iteration aus und protokolliert Fitness UND Mutationsrate."""
    population = []
    for _ in range(POPULATION_SIZE):
        ind = copy.deepcopy(teams)
        random.shuffle(ind)
        population.append(ind)

    history_fitness = []
    history_mutation = []

    best_overall = float('inf')
    current_mutation_rate = MUTATION_RATE_MIN
    stagnation_counter = 0

    for gen in range(GENERATIONS):
        pop_with_fitness = [(ind, calculate_fitness(ind, num_staffeln, dist_matrix)) for ind in population]
        pop_with_fitness.sort(key=lambda x: x[1])

        current_best = pop_with_fitness[0][1]

        if current_best < best_overall:
            best_overall = current_best
            stagnation_counter = 0
            current_mutation_rate = MUTATION_RATE_MIN
        else:
            stagnation_counter += 1

        if stagnation_counter > STAGNATION_LIMIT:
            current_mutation_rate = min(MUTATION_RATE_MAX, current_mutation_rate + 0.15)
            stagnation_counter = 0

        history_fitness.append(current_best)
        history_mutation.append(current_mutation_rate)

        elite_count = int(POPULATION_SIZE * ELITISM_RATE)
        next_population = [ind for ind, fit in pop_with_fitness[:elite_count]]

        while len(next_population) < POPULATION_SIZE:
            p1 = tournament_selection(pop_with_fitness, k=3)
            p2 = tournament_selection(pop_with_fitness, k=3)
            child = order_crossover(p1, p2)
            swap_mutation(child, current_mutation_rate)
            next_population.append(child)

        population = next_population

    return history_fitness, history_mutation

def generate_dual_plot(teams: list, num_staffeln: int, dist_matrix: dict, title: str, filename: str):
    """Erstellt den Plot mit zwei Y-Achsen (Fitness und Mutation)."""
    print(f"\nGeneriere Dual-Plot: {title}...")

    fit_history, mut_history = run_experiment_history(teams, num_staffeln, dist_matrix)

    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Achse 1: Fitness (Kilometer)
    color1 = '#0072B2'
    ax1.set_xlabel("Generationen", fontsize=12)
    ax1.set_ylabel("Ökologischer Fußabdruck (Gesamtkilometer)", color=color1, fontsize=12)
    ax1.plot(range(GENERATIONS), fit_history, color=color1, linewidth=2.0, label="Beste Fitness")
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',').replace(',', '.')))
    ax1.grid(True, linestyle='--', alpha=0.7)

    # Achse 2: Mutationsrate
    ax2 = ax1.twinx()
    color2 = '#D55E00'
    ax2.set_ylabel("Dynamische Mutationsrate", color=color2, fontsize=12)
    ax2.plot(range(GENERATIONS), mut_history, color=color2, linewidth=1.0, alpha=0.6, label="Mutationsrate")
    ax2.tick_params(axis='y', labelcolor=color2)
    ax2.set_ylim(0, 1.0)

    plt.title(title, fontsize=14, fontweight='bold', pad=15)
    fig.tight_layout()

    output_path = os.path.join(DATA_DIR, filename)
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"ERFOLG: Gespeichert unter {filename}")

def main():
    print("=== EA Konvergenz-Evaluation (Dual-Plots) ===")
    dist_matrix, kk_teams, kl_teams = load_data()

    generate_dual_plot(kk_teams, 12, dist_matrix, "Konvergenz Kreisklasse (Szenario A)", "konvergenz_szenario_a_kk.png")
    generate_dual_plot(kk_teams, 11, dist_matrix, "Konvergenz Kreisklasse (Szenario B)", "konvergenz_szenario_b_kk.png")
    generate_dual_plot(kl_teams, 8, dist_matrix, "Konvergenz Kreisliga", "konvergenz_kl.png")

if __name__ == "__main__":
    main()
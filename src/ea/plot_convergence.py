"""
Statistische Analyse des Konvergenzverhaltens (Evolutionärer Algorithmus).

Das Modul führt Replikationsstudien für distinkte Mutationsraten durch
und aggregiert die Resultate in Standardabweichungs-Graphen zur Methodenevaluation.
"""

import csv
import os
import random
import copy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from ea_optimizer import (
    load_data, calculate_fitness, tournament_selection,
    order_crossover, swap_mutation, POPULATION_SIZE, ELITISM_RATE
)

# Pfadkonfiguration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# Parameter
GENERATIONS = 1500
RUNS_PER_SETTING = 5
MUTATION_TESTS = [0.05, 0.20, 0.50]
COLORS = ['crimson', 'royalblue', 'forestgreen']
LABELS = ['5 % Mutation', '20 % Mutation', '50 % Mutation']

def run_experiment_history(teams: list, num_staffeln: int, dist_matrix: dict, mutation_rate: float) -> list:
    """Führt eine Iteration aus und protokolliert die Konvergenzhistorie."""
    population = []
    for _ in range(POPULATION_SIZE):
        ind = copy.deepcopy(teams)
        random.shuffle(ind)
        population.append(ind)

    history = []
    best_overall = float('inf')

    for gen in range(GENERATIONS):
        pop_with_fitness = [(ind, calculate_fitness(ind, num_staffeln, dist_matrix)) for ind in population]
        pop_with_fitness.sort(key=lambda x: x[1])

        current_best = pop_with_fitness[0][1]
        if current_best < best_overall:
            best_overall = current_best

        history.append(current_best)

        elite_count = int(POPULATION_SIZE * ELITISM_RATE)
        next_population = [ind for ind, fit in pop_with_fitness[:elite_count]]

        while len(next_population) < POPULATION_SIZE:
            p1 = tournament_selection(pop_with_fitness, k=3)
            p2 = tournament_selection(pop_with_fitness, k=3)
            child = order_crossover(p1, p2)
            swap_mutation(child, mutation_rate)
            next_population.append(child)

        population = next_population
    return history

def generate_single_plot(teams: list, num_staffeln: int, dist_matrix: dict, title: str, filename: str):
    """Aggregiert die Datenpunkte und erstellt den statistischen Plot."""
    print(f"\nGeneriere Plot: {title}...")
    plt.figure(figsize=(10, 6))

    for idx, rate in enumerate(MUTATION_TESTS):
        print(f"  -> Teste {rate*100}% Mutation ({RUNS_PER_SETTING} Runs)...")
        runs_data = []
        for run in range(RUNS_PER_SETTING):
            runs_data.append(run_experiment_history(teams, num_staffeln, dist_matrix, rate))

        runs_array = np.array(runs_data)
        mean_history = np.mean(runs_array, axis=0)
        std_history = np.std(runs_array, axis=0)
        generations_x = range(len(mean_history))

        plt.plot(generations_x, mean_history, label=LABELS[idx], color=COLORS[idx], linewidth=2.0)
        plt.fill_between(generations_x, mean_history - std_history, mean_history + std_history, color=COLORS[idx], alpha=0.15)

    plt.title(title, fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Generationen", fontsize=12)
    plt.ylabel("Ökologischer Fußabdruck (Gesamtkilometer)", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(loc="upper right", fontsize=11)

    # Y-Achse deutsch formatieren
    ax = plt.gca()
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',').replace(',', '.')))

    plt.tight_layout()
    output_path = os.path.join(DATA_DIR, filename)
    plt.savefig(output_path, dpi=300)
    plt.close() # Schließt das Fenster sauber, damit der nächste Plot frisch startet
    print(f"ERFOLG: Gespeichert unter {filename}")

def main():
    print("=== EA Konvergenz-Evaluation (Einzelplots) ===")
    print("Hinweis: Dauert lange...\n")
    dist_matrix, kk_teams, kl_teams = load_data()

    # 1. Kreisklasse - Szenario A
    generate_single_plot(
        kk_teams, 12, dist_matrix,
        "Konvergenz Kreisklasse (Szenario A: 12 Staffeln)",
        "konvergenz_szenario_a_kk.png"
    )

    # 2. Kreisklasse - Szenario B
    generate_single_plot(
        kk_teams, 11, dist_matrix,
        "Konvergenz Kreisklasse (Szenario B: 11 Staffeln)",
        "konvergenz_szenario_b_kk.png"
    )

    # 3. Kreisliga - (Gilt für A und B, da beide 8 Staffeln haben)
    generate_single_plot(
        kl_teams, 8, dist_matrix,
        "Konvergenz Kreisliga (8 Staffeln)",
        "konvergenz_kl.png"
    )

    print("\nALLE PLOTS ERFOLGREICH GENERIERT!")

if __name__ == "__main__":
    main()
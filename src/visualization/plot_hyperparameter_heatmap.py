"""
Umfassende Hyperparameter-Sensitivitätsanalyse (3D-Grid-Search).

Untersucht simultan drei Dimensionen: Populationsgröße, Elitismus und Mutationsrate.
Visualisiert die Ergebnisse als Facet-Grid (mehrere Heatmaps), um das globale
Degradations- und Konvergenzverhalten des Algorithmus zu dokumentieren.
"""

import os
import sys
import copy
import random
import numpy as np
import matplotlib.pyplot as plt

# =============================================================================
# PFAD-KONFIGURATION & IMPORTS
# =============================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
EA_DIR = os.path.join(SRC_DIR, "ea")

sys.path.append(EA_DIR)
from ea_optimizer import (
    load_data, calculate_fitness, tournament_selection,
    order_crossover, swap_mutation
)

# =============================================================================
# EXHAUSTIVE EXPERIMENT-KONFIGURATION (Rechenintensiv!)
# =============================================================================
TEST_GENERATIONS = 1500  # Volle Laufzeit für echte Ergebnisse
TEST_RUNS = 3  # 3 Durchläufe pro Setting für statistische Stabilität

# Der dreidimensionale Suchraum (3 x 3 x 3 = 27 Kombinationen)
MUTATION_RATES = [0.10, 0.30, 0.50]
POPULATION_SIZES = [20, 50, 100]
ELITISM_RATES = [0.0, 0.1, 0.2]


def run_mini_ea(teams: list, num_staffeln: int, dist_matrix: dict,
                pop_size: int, elitism_rate: float, mutation_rate: float) -> float:
    """Führt einen EA-Durchlauf mit den übergebenen Parametern aus."""
    population = []
    for _ in range(pop_size):
        ind = copy.deepcopy(teams)
        random.shuffle(ind)
        population.append(ind)

    best_overall = float('inf')

    for gen in range(TEST_GENERATIONS):
        pop_with_fitness = [(ind, calculate_fitness(ind, num_staffeln, dist_matrix)) for ind in population]
        pop_with_fitness.sort(key=lambda x: x[1])

        current_best = pop_with_fitness[0][1]
        if current_best < best_overall:
            best_overall = current_best

        elite_count = int(pop_size * elitism_rate)
        next_population = [ind for ind, fit in pop_with_fitness[:elite_count]]

        while len(next_population) < pop_size:
            p1 = tournament_selection(pop_with_fitness, k=3)
            p2 = tournament_selection(pop_with_fitness, k=3)
            child = order_crossover(p1, p2)
            swap_mutation(child, mutation_rate)
            next_population.append(child)

        population = next_population

    return best_overall


def main():
    print("=== Starte exhaustive Hyperparameter 3D Grid-Search ===")
    total_runs = len(POPULATION_SIZES) * len(ELITISM_RATES) * len(MUTATION_RATES) * TEST_RUNS
    print(f"Warnung: {total_runs} Durchläufe geplant. Dies kann 1-2 Stunden dauern!\n")

    dist_matrix, _, kl_teams = load_data()
    # Test an der Kreisliga (8 Staffeln), da exakter Vergleich
    num_staffeln = 8

    # 3D Matrix: [Population][Elitismus][Mutation]
    results = np.zeros((len(POPULATION_SIZES), len(ELITISM_RATES), len(MUTATION_RATES)))

    current_run = 1
    for k, mut_rate in enumerate(MUTATION_RATES):
        print(f"\n--- Teste Mutationsraum: {mut_rate * 100:.0f} % ---")
        for i, pop_size in enumerate(POPULATION_SIZES):
            for j, elitism in enumerate(ELITISM_RATES):
                print(
                    f"[{current_run}/{total_runs // TEST_RUNS}] Pop={pop_size:3d} | Elitismus={elitism:.1f} | Mut={mut_rate:.1f} ... ",
                    end="", flush=True)

                run_results = []
                for run in range(TEST_RUNS):
                    res = run_mini_ea(kl_teams, num_staffeln, dist_matrix, pop_size, elitism, mut_rate)
                    run_results.append(res)

                avg_result = np.mean(run_results)
                results[i, j, k] = avg_result
                print(f"Ø {avg_result:,.0f} km")
                current_run += 1

    # =============================================================================
    # PLOT GENERIERUNG (Multi-Heatmap Facet-Grid)
    # =============================================================================
    print("\nGeneriere komplexes Facet-Grid...")

    # Gemeinsame Skalierung für alle Heatmaps, damit die Farben vergleichbar bleiben
    vmin = np.min(results)
    vmax = np.max(results)

    fig, axes = plt.subplots(1, len(MUTATION_RATES), figsize=(16, 6), sharey=True)
    fig.suptitle("Umfassende Hyperparameter-Sensitivitätsanalyse (3D-Suchraum)", fontsize=16, fontweight='bold', y=1.02)

    for k, mut_rate in enumerate(MUTATION_RATES):
        ax = axes[k]
        # Slice der 3D-Matrix für diese spezielle Mutationsrate
        data_slice = results[:, :, k]

        im = ax.imshow(data_slice, cmap='RdYlGn_r', aspect='auto', vmin=vmin, vmax=vmax)

        ax.set_title(f"Mutationsrate: {mut_rate * 100:.0f} %", fontsize=13, pad=10)
        ax.set_xticks(np.arange(len(ELITISM_RATES)))
        ax.set_xticklabels([f"{x * 100:.0f} %" for x in ELITISM_RATES])
        ax.set_xlabel("Elitism-Rate", fontsize=11)

        if k == 0:
            ax.set_yticks(np.arange(len(POPULATION_SIZES)))
            ax.set_yticklabels(POPULATION_SIZES)
            ax.set_ylabel("Populationsgröße", fontsize=12)

        # Werte in die Felder schreiben
        for i in range(len(POPULATION_SIZES)):
            for j in range(len(ELITISM_RATES)):
                val = data_slice[i, j]
                # Kontrastfarbe: Weiß für dunkle Farben, Schwarz für die Mitte
                text_color = "white" if val < vmin + ((vmax - vmin) * 0.2) or val > vmax - (
                            (vmax - vmin) * 0.2) else "black"
                ax.text(j, i, f"{val:,.0f}", ha="center", va="center", color=text_color, fontweight='bold', fontsize=10)

    # Gemeinsame Colorbar rechts neben allen Plots
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    cbar = fig.colorbar(im, cax=cbar_ax)
    cbar.set_label('Ökologischer Fußabdruck (Gesamtkilometer)', rotation=270, labelpad=20, fontsize=12)

    # Subtitel / Legende
    plt.figtext(0.5, 0.01, "Grün = Hervorragende Konvergenz | Rot = Vorzeitige Stagnation / Schlechtes Ergebnis",
                ha="center", fontsize=11, style='italic')

    # Layout anpassen, damit nichts überlappt
    plt.subplots_adjust(left=0.08, right=0.90, bottom=0.15, top=0.88, wspace=0.1)

    output_path = os.path.join(DATA_DIR, "eval_hyperparameter_3D_heatmap.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nGigantisches Facet-Grid erfolgreich gespeichert unter: {output_path}")


if __name__ == "__main__":
    main()
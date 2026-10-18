"""
Tracking der Constraint-Verletzungen (Penalty-Abbau).
Dokumentiert, wie schnell der EA unzulässige Lösungen (vereinsinterne Duelle) aus der Population eliminiert.
"""

import os
import sys
import copy
import random

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
EA_DIR = os.path.join(SRC_DIR, "ea")
sys.path.append(EA_DIR)

from ea_optimizer import (
    load_data, tournament_selection, order_crossover,
    swap_mutation, POPULATION_SIZE, ELITISM_RATE
)

def count_internal_duels(teams: list, staffel_sizes: list) -> int:
    """Zählt die Anzahl der vereinsinternen Duelle in einem Spielplan basierend auf Staffelkapazitäten."""
    duels = 0
    start_idx = 0
    for size in staffel_sizes:
        staffel_teams = teams[start_idx : start_idx + size]
        start_idx += size
        base_clubs = []
        for team in staffel_teams:
            base_name = ''.join([char for char in team if not char.isdigit()]).strip().casefold()
            base_clubs.append(base_name)
        duels += len(base_clubs) - len(set(base_clubs))
    return duels

def main():
    print("Führe erweiterten Penalty-Tracker-Lauf durch...\n")
    dist_matrix, kk_teams, _, kk_capacities, _ = load_data()

    population = []
    for _ in range(POPULATION_SIZE):
        ind = copy.deepcopy(kk_teams)
        random.shuffle(ind)
        population.append(ind)

    milestones = [0, 10, 25, 50, 100, 250, 500]
    print("=" * 80)
    print(f"{' PENALTY ABBAU: Vereinsinterne Duelle (Weiche Restriktion)':^80}")
    print("=" * 80)
    print(f"{'Generation':<15} | {'Bestes Individuum':>20} | {'Population (Durchschnitt)':>30}")
    print("-" * 80)

    for gen in range(501):
        pop_with_penalties = [(ind, count_internal_duels(ind, kk_capacities)) for ind in population]
        pop_with_penalties.sort(key=lambda x: x[1])
        best_penalty_count = pop_with_penalties[0][1]
        total_duels = sum(p[1] for p in pop_with_penalties)
        avg_duels = total_duels / POPULATION_SIZE

        if gen in milestones:
            print(f"{gen:<15} | {best_penalty_count:>20} | {avg_duels:>30.2f}")

        if gen == 500:
            break

        elite_count = max(1, int(POPULATION_SIZE * ELITISM_RATE))
        next_population = [ind for ind, fit in pop_with_penalties[:elite_count]]

        while len(next_population) < POPULATION_SIZE:
            p1 = tournament_selection(pop_with_penalties, k=3)
            p2 = tournament_selection(pop_with_penalties, k=3)
            child = order_crossover(p1, p2)
            swap_mutation(child, 0.1)
            next_population.append(child)

        population = next_population

    print("-" * 80)

if __name__ == "__main__":
    main()
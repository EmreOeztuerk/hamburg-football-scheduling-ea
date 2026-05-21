"""
Evolutionärer Algorithmus zur Lösung des regionalen Clustering-Problems.

Das Modul führt die algorithmische Optimierung der Staffeleinteilung durch.
Es werden zwei Lösungsräume evaluiert:
Szenario A: Erhalt der bestehenden Ligenstrukturen (feste Staffelanzahl).
Szenario B: Neuausrichtung der Kapazitäten gemäß sportlichem Regelwerk.
"""

import csv
import os
import random
import copy

# Pfadkonfiguration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

MATRIX_CSV = os.path.join(DATA_DIR, "distance_matrix.csv")
TEAMS_CSV = os.path.join(DATA_DIR, "hamburg_vereine_geocoded_final.csv")

# EA-Parameter
POPULATION_SIZE = 50
GENERATIONS = 1500
MUTATION_RATE = 0.5
ELITISM_RATE = 0.1
PENALTY_KM = 5000.0

def load_data() -> tuple[dict, list, list]:
    dist_matrix = {}
    with open(MATRIX_CSV, mode='r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')
        header = next(reader)
        for row in reader:
            team_name = row[0]
            dist_matrix[team_name] = {}
            for idx, val in enumerate(row[1:], start=1):
                target_team = header[idx]
                dist_matrix[team_name][target_team] = float(val)

    kk_teams, kl_teams = [], []
    with open(TEAMS_CSV, mode='r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)
        for row in reader:
            if len(row) < 4 or row[2] == "NICHT GEFUNDEN":
                continue
            staffel, team = row[0], row[1]
            if "KK" in staffel:
                kk_teams.append(team)
            elif "KL" in staffel:
                kl_teams.append(team)
    return dist_matrix, kk_teams, kl_teams

def get_base_club_name(team_name: str) -> str:
    """Extrahiert den Basisvereinsnamen zur Identifikation interner Duelle."""
    return "".join([c for c in team_name if not c.isdigit()]).strip()

def calculate_fitness(individual: list, num_staffeln: int, dist_matrix: dict) -> float:
    """Zielfunktion (Fitness) der Optimierung."""
    teams_per_staffel = len(individual) // num_staffeln
    remainder = len(individual) % num_staffeln
    total_km = 0.0
    start_idx = 0

    for s in range(num_staffeln):
        size = teams_per_staffel + (1 if s < remainder else 0)
        staffel_teams = individual[start_idx : start_idx + size]
        start_idx += size

        base_clubs = [get_base_club_name(t) for t in staffel_teams]
        duplicates = len(base_clubs) - len(set(base_clubs))
        if duplicates > 0:
            total_km += duplicates * PENALTY_KM

        for i in range(len(staffel_teams)):
            for j in range(i + 1, len(staffel_teams)):
                t1, t2 = staffel_teams[i], staffel_teams[j]
                if t1 in dist_matrix and t2 in dist_matrix[t1]:
                    total_km += dist_matrix[t1][t2] * 2
    return total_km

def tournament_selection(population_with_fitness: list, k: int = 3) -> list:
    """Führt eine Turnierselektion für die Reproduktion durch."""
    tournament = random.sample(population_with_fitness, k)
    best_in_tournament = min(tournament, key=lambda x: x[1])
    return best_in_tournament[0]

def order_crossover(p1: list, p2: list) -> list:
    """Implementiert den Order Crossover (OX) Operator."""
    size = len(p1)
    start, end = sorted([random.randint(0, size - 1), random.randint(0, size - 1)])
    child = [None] * size
    child[start:end+1] = p1[start:end+1]

    p2_filtered = [team for team in p2 if team not in child]
    p2_idx = 0
    for i in range(size):
        if child[i] is None:
            child[i] = p2_filtered[p2_idx]
            p2_idx += 1
    return child

def swap_mutation(individual: list, rate: float):
    """Implementiert Swap-Mutation zur Exploration des Suchraums."""
    if random.random() < rate:
        idx1, idx2 = random.sample(range(len(individual)), 2)
        individual[idx1], individual[idx2] = individual[idx2], individual[idx1]

def run_evolution(teams: list, num_staffeln: int, dist_matrix: dict, label: str) -> tuple[float, list]:
    print(f"\nStarte Evolution für {label} ({num_staffeln} Staffeln)...")
    population = []
    for _ in range(POPULATION_SIZE):
        ind = copy.deepcopy(teams)
        random.shuffle(ind)
        population.append(ind)

    best_overall_fitness = float('inf')
    best_overall_individual = None

    for gen in range(GENERATIONS):
        pop_with_fitness = [(ind, calculate_fitness(ind, num_staffeln, dist_matrix)) for ind in population]
        pop_with_fitness.sort(key=lambda x: x[1])

        current_best = pop_with_fitness[0][1]
        if current_best < best_overall_fitness:
            best_overall_fitness = current_best
            best_overall_individual = pop_with_fitness[0][0]

        if gen % 300 == 0:
            print(f"  Generation {gen:4d} | Bester Wert: {current_best:,.2f} km")

        elite_count = int(POPULATION_SIZE * ELITISM_RATE)
        next_population = [ind for ind, fit in pop_with_fitness[:elite_count]]

        while len(next_population) < POPULATION_SIZE:
            p1 = tournament_selection(pop_with_fitness, k=3)
            p2 = tournament_selection(pop_with_fitness, k=3)
            child = order_crossover(p1, p2)
            swap_mutation(child, MUTATION_RATE)
            next_population.append(child)

        population = next_population

    print(f"-> Fertig! Bestes Ergebnis: {best_overall_fitness:,.2f} km")
    return best_overall_fitness, best_overall_individual

def calculate_optimal_staffeln(num_teams: int) -> int:
    """Bestimmt die optimale Kapazitätsauslastung."""
    return round(num_teams / 15.0)

def calculate_away_trips(num_teams: int, num_staffeln: int) -> int:
    """Bestimmt die Gesamtzahl der Auswärtsfahrten."""
    teams_per_staffel = num_teams // num_staffeln
    remainder = num_teams % num_staffeln
    total_trips = 0
    for s in range(num_staffeln):
        size = teams_per_staffel + (1 if s < remainder else 0)
        total_trips += size * (size - 1)
    return total_trips

def export_schedule_to_csv(kk_plan: list, kl_plan: list, num_kk: int, num_kl: int, filename: str):
    """Speichert die Lösungsmenge."""
    output_file = os.path.join(DATA_DIR, filename)
    with open(output_file, mode='w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(["Liga", "Staffel_Nr", "Vereinsname"])

        # KK Export
        teams_per_staffel_kk = len(kk_plan) // num_kk
        remainder_kk = len(kk_plan) % num_kk
        start_idx = 0
        for s in range(num_kk):
            size = teams_per_staffel_kk + (1 if s < remainder_kk else 0)
            staffel_teams = kk_plan[start_idx : start_idx + size]
            start_idx += size
            for team in staffel_teams:
                writer.writerow(["Kreisklasse", f"KK-Neu-{s+1:02d}", team])

        # KL Export
        teams_per_staffel_kl = len(kl_plan) // num_kl
        remainder_kl = len(kl_plan) % num_kl
        start_idx = 0
        for s in range(num_kl):
            size = teams_per_staffel_kl + (1 if s < remainder_kl else 0)
            staffel_teams = kl_plan[start_idx : start_idx + size]
            start_idx += size
            for team in staffel_teams:
                writer.writerow(["Kreisliga", f"KL-Neu-{s+1:02d}", team])
    print(f"\n=> Spielplan gespeichert unter: {filename}")

def main():
    print("=== HFV Spielplan Optimierung (SZENARIO-ANALYSE) ===")
    dist_matrix, kk_teams, kl_teams = load_data()

    BASELINE_KM = 42253.02 #Baseline aus baseline_calculator.py
    BASELINE_TRIPS = 3670
    avg_km_baseline = BASELINE_KM / BASELINE_TRIPS

    # SZENARIO A: 1:1 HFV-Struktur (Feste 12 KK, 8 KL)
    print("\n" + "#"*55)
    print(" SZENARIO A: 1:1 Vergleich (12 KK, 8 KL Staffeln)")
    print("#"*55)

    num_kk_a, num_kl_a = 12, 8
    best_kk_km_a, best_kk_plan_a = run_evolution(kk_teams, num_kk_a, dist_matrix, "Kreisklasse (Szen A)")
    best_kl_km_a, best_kl_plan_a = run_evolution(kl_teams, num_kl_a, dist_matrix, "Kreisliga (Szen A)")

    export_schedule_to_csv(best_kk_plan_a, best_kl_plan_a, num_kk_a, num_kl_a, "optimized_schedule_szenario_A.csv")
    total_ea_km_a = best_kk_km_a + best_kl_km_a

    trips_a_kk = calculate_away_trips(len(kk_teams), num_kk_a)
    trips_a_kl = calculate_away_trips(len(kl_teams), num_kl_a)
    total_trips_a = trips_a_kk + trips_a_kl
    avg_km_ea_a = total_ea_km_a / total_trips_a

    # SZENARIO B: Dynamische Ligenstruktur (Dynamische 14-16er Regel)
    print("\n" + "#"*55)
    print(" SZENARIO B: Konsolidierung (Regelkonforme Auffüllung)")
    print("#"*55)

    num_kk_b = calculate_optimal_staffeln(len(kk_teams))
    num_kl_b = calculate_optimal_staffeln(len(kl_teams))

    best_kk_km_b, best_kk_plan_b = run_evolution(kk_teams, num_kk_b, dist_matrix, "Kreisklasse (Szen B)")
    best_kl_km_b, best_kl_plan_b = run_evolution(kl_teams, num_kl_b, dist_matrix, "Kreisliga (Szen B)")

    export_schedule_to_csv(best_kk_plan_b, best_kl_plan_b, num_kk_b, num_kl_b, "optimized_schedule_szenario_B.csv")
    total_ea_km_b = best_kk_km_b + best_kl_km_b

    trips_b_kk = calculate_away_trips(len(kk_teams), num_kk_b)
    trips_b_kl = calculate_away_trips(len(kl_teams), num_kl_b)
    total_trips_b = trips_b_kk + trips_b_kl
    avg_km_ea_b = total_ea_km_b / total_trips_b

    # Ergebnisse beider Szenarien
    print("\n" + "=" * 65)
    print(" FINALER STATISTIK-REPORT (BEIDE SZENARIEN)")
    print("=" * 65)
    print(f"HFV BASELINE: {BASELINE_KM:,.2f} km bei {BASELINE_TRIPS} Fahrten (Ø {avg_km_baseline:.2f} km/Fahrt)\n")

    print("--- SZENARIO A: 1:1 HFV Ligenstruktur (12 KK, 8 KL) ---")
    print(f"Gesamtkilometer:  {total_ea_km_a:,.2f} km")
    print(f"Auswärtsfahrten:  {total_trips_a} (Gleiche Staffelanzahl)")
    print(f"Ø Fahrtstrecke:   {avg_km_ea_a:.2f} km/Fahrt")
    print(f"-> Absolute Ersparnis: {BASELINE_KM - total_ea_km_a:,.2f} km ({(BASELINE_KM - total_ea_km_a)/BASELINE_KM * 100:.2f} %)\n")

    print("--- SZENARIO B: Dynamische Ligenstruktur (14-16er Regel) ---")
    print(f"Gesamtkilometer:  {total_ea_km_b:,.2f} km")
    print(f"Auswärtsfahrten:  {total_trips_b} (Mehraufwand: +{total_trips_b - BASELINE_TRIPS} Fahrten)")
    print(f"Ø Fahrtstrecke:   {avg_km_ea_b:.2f} km/Fahrt")
    print(f"-> Relativer Effizienz-Gewinn pro Fahrt: {(avg_km_baseline - avg_km_ea_b)/avg_km_baseline * 100:.2f} %")
    print("=" * 65)

if __name__ == "__main__":
    main()
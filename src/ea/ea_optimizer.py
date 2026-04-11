"""
Evolutionärer Algorithmus - Hauptskript

Dieses Skript optimiert die Zuteilung der Hamburger Amateurvereine.
Es wendet "Hard Constraints" an, indem es Kreisklasse (KK) und
Kreisliga (KL) strikt voneinander trennt und separat optimiert.
"""

import csv
import os
import random
import copy

# --- PFAD-RESOLUTION ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
MATRIX_CSV = os.path.join(DATA_DIR, "distance_matrix.csv")
TEAMS_CSV = os.path.join(DATA_DIR, "hamburg_vereine_geocoded_final.csv")

# --- EA PARAMETER ---
POPULATION_SIZE = 50      # Anzahl der Spielpläne pro Generation
GENERATIONS = 2000         # Wie oft sich die Population fortpflanzt
MUTATION_RATE = 0.2       # 20% Chance für eine Mutation
ELITISM_RATE = 0.1        # Die besten 10% überleben ungetastet


def load_data() -> tuple[dict, list, list]:
    """Lädt die Matrix und teilt die Teams in KL und KK auf."""
    dist_matrix = {}

    # 1. Distanzmatrix laden
    with open(MATRIX_CSV, mode='r', encoding='utf-8-sig') as file:
        reader = csv.reader(file, delimiter=';')
        headers = next(reader)
        all_teams = headers[1:]

        for row in reader:
            team_a = row[0]
            dist_matrix[team_a] = {}
            for i, team_b in enumerate(all_teams):
                dist_matrix[team_a][team_b] = float(row[i+1])

    # 2. Ligen-Zugehörigkeit auslesen
    kk_teams = []
    kl_teams = []

    with open(TEAMS_CSV, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            team = row["Mannschaft"]
            if row["Breitengrad"] == "NICHT GEFUNDEN":
                continue # Überspringen, falls Daten fehlen

            if row["Staffel"].startswith("KK"):
                kk_teams.append(team)
            elif row["Staffel"].startswith("KL"):
                kl_teams.append(team)

    return dist_matrix, kk_teams, kl_teams


def split_into_staffeln(individual: list, num_staffeln: int) -> list:
    """
    Teilt eine Liste von Teams mathematisch korrekt in eine feste Anzahl
    von Staffeln auf. Verteilt den "Rest" fair.
    Beispiel: 160 Teams in 12 Staffeln -> 4 Staffeln mit 14, 8 Staffeln mit 13.
    """
    staffeln = []
    base_size = len(individual) // num_staffeln
    remainder = len(individual) % num_staffeln

    start = 0
    for i in range(num_staffeln):
        # Die ersten 'remainder' Staffeln bekommen ein Team mehr, damit es exakt aufgeht
        size = base_size + 1 if i < remainder else base_size
        staffeln.append(individual[start:start + size])
        start += size

    return staffeln


def calculate_fitness(individual: list, dist_matrix: dict, num_staffeln: int) -> float:
    """
    Berechnet die Gesamtkilometer + Vereinsstrafen (Penalties).
    """
    total_km = 0.0
    penalty = 0.0

    # Teams korrekt aufteilen
    staffeln = split_into_staffeln(individual, num_staffeln)

    for teams in staffeln:
        # 1. Distanzen berechnen
        for x in range(len(teams)):
            for y in range(x + 1, len(teams)):
                team_a = teams[x]
                team_b = teams[y]
                total_km += dist_matrix[team_a][team_b] * 2

        # 2. VEREINS-REGEL (Penalty System)
        # Wir prüfen, ob zwei Teams denselben "Stammverein" haben
        # Beispiel: "FC Elmshorn 1." und "FC Elmshorn 2." -> Stammverein ist "FC Elmshorn"
        stammvereine = []
        for t in teams:
            # Alles ab der Zahl am Ende abschneiden (z.B. " 2.")
            stamm = ''.join([i for i in t if not i.isdigit()]).strip().rstrip('.')
            stammvereine.append(stamm)

        # Wenn ein Stammverein doppelt in dieser Staffel ist, gibt es Strafe!
        for stamm in set(stammvereine):
            count = stammvereine.count(stamm)
            if count > 1:
                # 500 km Strafe für jedes zusätzliche Team desselben Vereins in der Staffel!
                penalty += (count - 1) * 500.0

    return total_km + penalty


def create_initial_population(teams: list) -> list:
    """Erstellt die allererste Generation."""
    population = []
    for _ in range(POPULATION_SIZE):
        individual = copy.deepcopy(teams)
        random.shuffle(individual)
        population.append(individual)
    return population


def crossover(parent1: list, parent2: list) -> list:
    """Order Crossover: Nimmt die Hälfte von P1 und füllt mit P2 auf."""
    half_point = len(parent1) // 2
    child = parent1[:half_point]
    child_set = set(child)

    for team in parent2:
        if team not in child_set:
            child.append(team)

    return child


def mutate(individual: list):
    """Swap-Mutation: Vertauscht zwei Vereine zufällig."""
    if random.random() < MUTATION_RATE:
        idx1 = random.randint(0, len(individual) - 1)
        idx2 = random.randint(0, len(individual) - 1)
        individual[idx1], individual[idx2] = individual[idx2], individual[idx1]


def run_evolution(teams: list, num_staffeln: int, dist_matrix: dict, liga_name: str) -> float:
    print(f"\n--- Starte Optimierung für {liga_name} ---")
    print(f"Teams: {len(teams)} | Exakte Staffeln: {num_staffeln}")

    population = create_initial_population(teams)
    best_fitness = float('inf')

    for generation in range(GENERATIONS):
        pop_with_fitness = [(ind, calculate_fitness(ind, dist_matrix, num_staffeln)) for ind in population]
        pop_with_fitness.sort(key=lambda x: x[1])

        current_best = pop_with_fitness[0][1]
        if current_best < best_fitness:
            best_fitness = current_best

        if generation % 25 == 0 or generation == GENERATIONS - 1:
            print(f"Generation {generation:3d} | Beste KM: {best_fitness:,.2f}".replace(",", "."))

        next_population = []
        elite_count = int(POPULATION_SIZE * ELITISM_RATE)

        for i in range(elite_count):
            next_population.append(pop_with_fitness[i][0])

        while len(next_population) < POPULATION_SIZE:
            p1 = random.choice(pop_with_fitness[:int(POPULATION_SIZE/2)])[0] # Bevorzuge bessere Hälfte
            p2 = random.choice(pop_with_fitness[:int(POPULATION_SIZE/2)])[0]

            child = crossover(p1, p2)
            mutate(child)
            next_population.append(child)

        population = next_population

    return best_fitness


def main():
    print("=== HFV Spielplan Optimierung ===")
    dist_matrix, kk_teams, kl_teams = load_data()

    # 1. Kreisklasse optimieren (12 Staffeln)
    best_kk_km = run_evolution(kk_teams, 12, dist_matrix, "Kreisklasse (KK)")

    # 2. Kreisliga optimieren (8 Staffeln)
    best_kl_km = run_evolution(kl_teams, 8, dist_matrix, "Kreisliga (KL)")

    # 3. Ergebnisse zusammenführen
    total_ea_km = best_kk_km + best_kl_km
    baseline_km = 39749.60 # Die Baseline, die wir vorhin berechnet haben

    print("\n" + "=" * 50)
    print("EVOLUTION ABGESCHLOSSEN!")
    print(f"Baseline (Echter HFV-Plan): {baseline_km:,.2f} km".replace(",", "."))
    print(f"EA Optimiert (Gesamt):      {total_ea_km:,.2f} km".replace(",", "."))
    print("-" * 50)

    ersparnis = baseline_km - total_ea_km
    prozent = (ersparnis / baseline_km) * 100

    if ersparnis > 0:
        print(f"ERFOLG! Ersparnis: {ersparnis:,.2f} km ({prozent:.1f} % weniger Fahrtweg!)".replace(",", "."))
    else:
        print("Der Algorithmus muss länger trainieren (mehr Generationen), um die Baseline zu schlagen.")
    print("=" * 50)


if __name__ == "__main__":
    main()
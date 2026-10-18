"""
Evolutionärer Algorithmus zur Lösung des regionalen Clustering-Problems.

Szenario A übernimmt die tatsächlichen Staffelkapazitäten aus der eingelesenen
Ist-Baseline. Szenario B verwendet neu berechnete, möglichst ausgeglichene
Staffelkapazitäten. Der Optimierer validiert Teamzuordnungen und Distanzdaten
vor bzw. während der Optimierung.
"""

import csv
import os
import random
from collections import Counter
from typing import Dict, List, Sequence, Tuple

# Pfadkonfiguration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

MATRIX_CSV = os.path.join(DATA_DIR, "distance_matrix.csv")
TEAMS_CSV = os.path.join(DATA_DIR, "hamburg_vereine_geocoded_final.csv")

# EA-Parameter
POPULATION_SIZE = 300
GENERATIONS = 5000
ELITISM_RATE = 0.05
PENALTY_KM = 5000.0

# Dynamische Mutationsraten
MUTATION_RATE_MIN = 0.10
MUTATION_RATE_MAX = 0.85
STAGNATION_LIMIT = 50
MUTATION_ADAPTATION_STEP = 0.15
TARGET_STAFFEL_SIZE = 15.0

# Referenzwert aus baseline_calculator.py; wird mit der Kapazitätsliste geprüft.
BASELINE_KM = 42253.02
EXPECTED_BASELINE_MATCHES = 3670


def _load_distance_matrix(path: str) -> Dict[str, Dict[str, float]]:
    """Liest die Distanzmatrix ein und prüft, dass Tabellenzeilen konsistent sind."""
    dist_matrix: Dict[str, Dict[str, float]] = {}
    with open(path, mode="r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file, delimiter=";")
        try:
            header = next(reader)
        except StopIteration as exc:
            raise ValueError(f"Die Distanzmatrix ist leer: {path}") from exc

        if len(header) < 2:
            raise ValueError("Die Distanzmatrix enthält keine Team-Spalten.")

        column_teams = header[1:]
        if len(column_teams) != len(set(column_teams)):
            raise ValueError("Die Distanzmatrix enthält doppelte Teamnamen im Spaltenkopf.")

        for line_number, row in enumerate(reader, start=2):
            if not row:
                continue
            if len(row) != len(header):
                raise ValueError(
                    f"Ungültige Zeilenlänge in {path}, Zeile {line_number}: "
                    f"erwartet {len(header)} Felder, erhalten {len(row)}."
                )
            team_name = row[0].strip()
            if not team_name:
                raise ValueError(f"Leerer Teamname in der Distanzmatrix, Zeile {line_number}.")
            if team_name in dist_matrix:
                raise ValueError(f"Doppelte Teamzeile in der Distanzmatrix: {team_name!r}")

            try:
                dist_matrix[team_name] = {
                    target_team: float(value)
                    for target_team, value in zip(column_teams, row[1:])
                }
            except ValueError as exc:
                raise ValueError(
                    f"Ungültiger Distanzwert in {path}, Zeile {line_number}."
                ) from exc

    row_teams = set(dist_matrix)
    header_set = set(column_teams)
    if row_teams != header_set:
        missing_rows = sorted(header_set - row_teams)
        extra_rows = sorted(row_teams - header_set)
        raise ValueError(
            "Zeilen- und Spaltennamen der Distanzmatrix stimmen nicht überein. "
            f"Fehlende Zeilen: {missing_rows[:10]}; zusätzliche Zeilen: {extra_rows[:10]}"
        )

    return dist_matrix


def load_data() -> Tuple[Dict[str, Dict[str, float]], List[str], List[str], List[int], List[int]]:
    """
    Lädt Distanzen und geokodierte Mannschaften.

    Die Staffelgrößen für Szenario A werden aus den ursprünglichen Staffelspalten
    des Team-CSV abgeleitet. Zeilen mit nicht gefundenen Koordinaten werden wie
    bisher ausgeschlossen; Kapazitäten beziehen sich deshalb auf genau den
    tatsächlich in dieser Optimierung verwendeten Datensatz.
    """
    dist_matrix = _load_distance_matrix(MATRIX_CSV)

    kk_by_staffel: Dict[str, List[str]] = {}
    kl_by_staffel: Dict[str, List[str]] = {}
    all_seen_teams: List[str] = []

    with open(TEAMS_CSV, mode="r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file, delimiter=";")
        try:
            next(reader)
        except StopIteration as exc:
            raise ValueError(f"Die Teamdatei ist leer: {TEAMS_CSV}") from exc

        for line_number, row in enumerate(reader, start=2):
            if len(row) < 4 or row[2].strip() == "NICHT GEFUNDEN":
                continue

            staffel = row[0].strip()
            team = row[1].strip()
            if not staffel or not team:
                raise ValueError(f"Leere Staffel oder Mannschaft in {TEAMS_CSV}, Zeile {line_number}.")

            if "KK" in staffel:
                kk_by_staffel.setdefault(staffel, []).append(team)
                all_seen_teams.append(team)
            elif "KL" in staffel:
                kl_by_staffel.setdefault(staffel, []).append(team)
                all_seen_teams.append(team)

    duplicates = [team for team, count in Counter(all_seen_teams).items() if count > 1]
    if duplicates:
        raise ValueError(
            "Die Teamdatei enthält doppelte Mannschaftsnamen in den verwendeten Ligen. "
            f"Beispiele: {duplicates[:15]}"
        )

    kk_teams = [team for teams in kk_by_staffel.values() for team in teams]
    kl_teams = [team for teams in kl_by_staffel.values() for team in teams]
    kk_baseline_capacities = [len(teams) for teams in kk_by_staffel.values()]
    kl_baseline_capacities = [len(teams) for teams in kl_by_staffel.values()]

    if not kk_teams or not kl_teams:
        raise ValueError(
            "Nach dem Filtern wurden keine Teams für eine oder beide Ligen gefunden. "
            "Bitte Teamdatei und Staffelbezeichnungen prüfen."
        )

    # Jede verwendete Mannschaft muss einen Eintrag in jeder benötigten Matrixzeile haben.
    used_teams = kk_teams + kl_teams
    missing_rows = sorted(set(used_teams) - set(dist_matrix))
    if missing_rows:
        raise ValueError(
            "Für Mannschaften fehlen Zeilen in der Distanzmatrix: "
            f"{missing_rows[:15]}"
        )

    missing_pairs = []
    for team in used_teams:
        row = dist_matrix[team]
        for other in used_teams:
            if team != other and other not in row:
                missing_pairs.append((team, other))
                if len(missing_pairs) >= 15:
                    break
        if len(missing_pairs) >= 15:
            break
    if missing_pairs:
        raise ValueError(
            "Die Distanzmatrix enthält nicht alle benötigten Team-Paare. "
            f"Beispiele: {missing_pairs}"
        )

    print(f"Eingelesen: {len(kk_teams)} Kreisklasse-Teams in {len(kk_baseline_capacities)} Ist-Staffeln.")
    print(f"Eingelesen: {len(kl_teams)} Kreisliga-Teams in {len(kl_baseline_capacities)} Ist-Staffeln.")
    print(f"Ist-Kapazitäten Kreisklasse: {kk_baseline_capacities}")
    print(f"Ist-Kapazitäten Kreisliga:  {kl_baseline_capacities}")

    return (
        dist_matrix,
        kk_teams,
        kl_teams,
        kk_baseline_capacities,
        kl_baseline_capacities,
    )


def get_base_club_name(team_name: str) -> str:
    """Extrahiert den Basisvereinsnamen zur Identifikation vereinsinterner Duelle."""
    return "".join(char for char in team_name if not char.isdigit()).strip().casefold()


def validate_capacities(teams: Sequence[str], staffel_sizes: Sequence[int], label: str) -> None:
    """Prüft, dass die Staffelkapazitäten positiv sind und exakt alle Teams abdecken."""
    if not staffel_sizes:
        raise ValueError(f"{label}: Es wurden keine Staffelkapazitäten definiert.")
    if any(not isinstance(size, int) or size < 1 for size in staffel_sizes):
        raise ValueError(f"{label}: Staffelkapazitäten müssen positive ganze Zahlen sein.")
    if sum(staffel_sizes) != len(teams):
        raise ValueError(
            f"{label}: Staffelkapazitäten summieren sich auf {sum(staffel_sizes)}, "
            f"aber es gibt {len(teams)} Mannschaften."
        )
    if len(teams) != len(set(teams)):
        duplicates = [team for team, count in Counter(teams).items() if count > 1]
        raise ValueError(f"{label}: Teamliste enthält Duplikate: {duplicates[:15]}")


def calculate_fitness(
    individual: Sequence[str],
    staffel_sizes: Sequence[int],
    dist_matrix: Dict[str, Dict[str, float]],
) -> float:
    """Berechnet die Gesamtfahrtstrecke einschließlich Penalty für Vereinsduelle."""
    if sum(staffel_sizes) != len(individual):
        raise ValueError("Die Kapazitäten passen nicht zur Länge des Individuums.")
    if len(individual) != len(set(individual)):
        raise ValueError("Fitnessberechnung abgebrochen: Individuum ist keine gültige Permutation.")

    total_km = 0.0
    start_idx = 0

    for size in staffel_sizes:
        staffel_teams = individual[start_idx : start_idx + size]
        start_idx += size

        base_clubs = [get_base_club_name(team) for team in staffel_teams]
        duplicates = len(base_clubs) - len(set(base_clubs))
        if duplicates > 0:
            total_km += duplicates * PENALTY_KM

        for i in range(len(staffel_teams)):
            for j in range(i + 1, len(staffel_teams)):
                team_a, team_b = staffel_teams[i], staffel_teams[j]
                try:
                    distance = dist_matrix[team_a][team_b]
                except KeyError as exc:
                    raise KeyError(
                        f"Distanz fehlt für Team-Paar {team_a!r} / {team_b!r}. "
                        "Die Fitness darf nicht durch ausgelassene Distanzen verfälscht werden."
                    ) from exc
                total_km += distance * 2

    return total_km


def tournament_selection(population_with_fitness: list, k: int = 3) -> list:
    """Wählt das fitteste Individuum aus einer zufällig zusammengestellten Gruppe."""
    tournament = random.sample(population_with_fitness, k)
    return min(tournament, key=lambda item: item[1])[0]


def order_crossover(p1: List[str], p2: List[str]) -> List[str]:
    """Kanonischer Order Crossover (OX1) mit zyklischem Auffüllen ab dem zweiten Schnittpunkt."""
    if len(p1) != len(p2):
        raise ValueError("OX1 benötigt Elternindividuen gleicher Länge.")
    if len(p1) != len(set(p1)) or len(p2) != len(set(p2)):
        raise ValueError("OX1 benötigt gültige Permutationen ohne doppelte Elemente.")
    if set(p1) != set(p2):
        raise ValueError("OX1 benötigt dieselbe Menge von Mannschaften in beiden Elternindividuen.")
    if not p1:
        return []

    size = len(p1)
    start, end = sorted(random.sample(range(size), 2)) if size > 1 else (0, 0)
    child: List[str | None] = [None] * size
    child[start : end + 1] = p1[start : end + 1]
    used = set(p1[start : end + 1])

    # OX1: Spender und freie Kindpositionen laufen beide zyklisch ab end + 1.
    write_idx = (end + 1) % size
    for offset in range(size):
        gene = p2[(end + 1 + offset) % size]
        if gene in used:
            continue
        while child[write_idx] is not None:
            write_idx = (write_idx + 1) % size
        child[write_idx] = gene
        used.add(gene)
        write_idx = (write_idx + 1) % size

    result = [gene for gene in child if gene is not None]
    if len(result) != size or len(set(result)) != size or set(result) != set(p1):
        raise RuntimeError("OX1 hat eine ungültige Permutation erzeugt.")
    return result


def swap_mutation(individual: List[str], current_rate: float) -> None:
    """Führt bei erfolgreicher Zufallsentscheidung eine permutationsbewahrende Swap-Mutation aus."""
    if len(individual) > 1 and random.random() < current_rate:
        idx1, idx2 = random.sample(range(len(individual)), 2)
        individual[idx1], individual[idx2] = individual[idx2], individual[idx1]


def run_evolution(
    teams: List[str],
    staffel_sizes: Sequence[int],
    dist_matrix: Dict[str, Dict[str, float]],
    label: str,
) -> Tuple[float, List[str]]:
    """Führt die Evolution für eine vorgegebene, feste Staffelkapazitätsliste aus."""
    validate_capacities(teams, staffel_sizes, label)
    print(f"\nStarte Evolution für {label} ({len(staffel_sizes)} Staffeln; Kapazitäten {list(staffel_sizes)})...")

    population: List[List[str]] = []
    for _ in range(POPULATION_SIZE):
        individual = list(teams)
        random.shuffle(individual)
        population.append(individual)

    best_overall_fitness = float("inf")
    best_overall_individual: List[str] | None = None
    current_mutation_rate = MUTATION_RATE_MIN
    stagnation_counter = 0

    for generation in range(GENERATIONS):
        pop_with_fitness = [
            (individual, calculate_fitness(individual, staffel_sizes, dist_matrix))
            for individual in population
        ]
        pop_with_fitness.sort(key=lambda item: item[1])
        current_best = pop_with_fitness[0][1]

        if current_best < best_overall_fitness:
            best_overall_fitness = current_best
            best_overall_individual = list(pop_with_fitness[0][0])
            stagnation_counter = 0
            current_mutation_rate = MUTATION_RATE_MIN
        else:
            stagnation_counter += 1

        if stagnation_counter > STAGNATION_LIMIT:
            current_mutation_rate = min(
                MUTATION_RATE_MAX,
                current_mutation_rate + MUTATION_ADAPTATION_STEP,
            )
            stagnation_counter = 0

        if generation % 300 == 0:
            print(
                f"  Generation {generation:4d} | Bester Wert: {current_best:,.2f} km "
                f"| Mutationsrate: {current_mutation_rate:.2f}"
            )

        elite_count = max(1, int(POPULATION_SIZE * ELITISM_RATE))
        next_population = [list(individual) for individual, _ in pop_with_fitness[:elite_count]]

        while len(next_population) < POPULATION_SIZE:
            parent1 = tournament_selection(pop_with_fitness, k=3)
            parent2 = tournament_selection(pop_with_fitness, k=3)
            child = order_crossover(parent1, parent2)
            swap_mutation(child, current_mutation_rate)
            next_population.append(child)

        population = next_population

    if best_overall_individual is None:
        raise RuntimeError(f"{label}: Es wurde kein bestes Individuum erzeugt.")

    # Sicherheitsprüfung der finalen Lösung
    if len(best_overall_individual) != len(set(best_overall_individual)) or set(best_overall_individual) != set(teams):
        raise RuntimeError(f"{label}: Die beste Lösung ist keine gültige Permutation der Eingangsteams.")
    print(f"-> Fertig! Bestes Ergebnis: {best_overall_fitness:,.2f} km")
    return best_overall_fitness, best_overall_individual


def calculate_optimal_staffeln(num_teams: int) -> int:
    """Bestimmt die Staffelanzahl für Szenario B anhand der Zielgröße von 15 Teams."""
    return max(1, round(num_teams / TARGET_STAFFEL_SIZE))


def build_balanced_capacities(num_teams: int, num_staffeln: int) -> List[int]:
    """Erzeugt möglichst gleich große Staffeln; die Kapazitäten summieren sich exakt zu num_teams."""
    if num_staffeln < 1 or num_staffeln > num_teams:
        raise ValueError("Ungültige Staffelanzahl für die Anzahl der Mannschaften.")
    base_size, remainder = divmod(num_teams, num_staffeln)
    return [base_size + (1 if idx < remainder else 0) for idx in range(num_staffeln)]


def calculate_away_trips(staffel_sizes: Sequence[int]) -> int:
    """Berechnet die Zahl der Auswärtsfahrten bei Hin- und Rückrunde als Summe s*(s-1)."""
    if any(size < 1 for size in staffel_sizes):
        raise ValueError("Staffelgrößen müssen positiv sein.")
    return sum(size * (size - 1) for size in staffel_sizes)


def export_schedule_to_csv(
    kk_plan: Sequence[str],
    kl_plan: Sequence[str],
    kk_staffel_sizes: Sequence[int],
    kl_staffel_sizes: Sequence[int],
    filename: str,
) -> None:
    """Exportiert eine finale Lösung mit genau den für den Lauf verwendeten Kapazitäten."""
    validate_capacities(kk_plan, kk_staffel_sizes, "CSV-Export Kreisklasse")
    validate_capacities(kl_plan, kl_staffel_sizes, "CSV-Export Kreisliga")
    output_file = os.path.join(DATA_DIR, filename)

    with open(output_file, mode="w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(["Liga", "Staffel_Nr", "Vereinsname"])

        for league_label, plan, capacities, prefix in (
            ("Kreisklasse", kk_plan, kk_staffel_sizes, "KK-Neu"),
            ("Kreisliga", kl_plan, kl_staffel_sizes, "KL-Neu"),
        ):
            start_idx = 0
            for staffel_idx, size in enumerate(capacities, start=1):
                staffel_teams = plan[start_idx : start_idx + size]
                start_idx += size
                for team in staffel_teams:
                    writer.writerow([league_label, f"{prefix}-{staffel_idx:02d}", team])

    print(f"\n=> Spielplan gespeichert unter: {filename}")


def main() -> None:
    print("=== HFV-Staffeleinteilung: Szenarioanalyse ===")
    (
        dist_matrix,
        kk_teams,
        kl_teams,
        kk_baseline_capacities,
        kl_baseline_capacities,
    ) = load_data()

    baseline_matches_from_capacities = (
        calculate_away_trips(kk_baseline_capacities)
        + calculate_away_trips(kl_baseline_capacities)
    )
    print(f"\nSpiele/Auswärtsfahrten laut eingelesenen Ist-Kapazitäten: {baseline_matches_from_capacities}")
    if baseline_matches_from_capacities != EXPECTED_BASELINE_MATCHES:
        print(
            "WARNUNG: Die aus der Teamdatei rekonstruierten Kapazitäten ergeben "
            f"{baseline_matches_from_capacities} Spiele, der bisher fest eingetragene "
            f"Baseline-Wert lautet aber {EXPECTED_BASELINE_MATCHES}. Prüfe, ob die CSV "
            "dieselben Mannschaften und Staffelstände wie baseline_calculator.py enthält. "
            "Die Kapazitätsstruktur in Szenario A wird aus der CSV übernommen; die Zahl "
            "der Baseline-Spiele muss vor der finalen Auswertung mit baseline_calculator.py "
            "abgeglichen werden."
        )

    baseline_avg_km = BASELINE_KM / baseline_matches_from_capacities

    # SZENARIO A: tatsächliche Staffelgrößen aus der eingelesenen Ist-Baseline.
    print("\n" + "#" * 65)
    print(" SZENARIO A: Erhalt der Ist-Kapazitäten")
    print("#" * 65)

    best_kk_km_a, best_kk_plan_a = run_evolution(
        kk_teams, kk_baseline_capacities, dist_matrix, "Kreisklasse (Szenario A)"
    )
    best_kl_km_a, best_kl_plan_a = run_evolution(
        kl_teams, kl_baseline_capacities, dist_matrix, "Kreisliga (Szenario A)"
    )
    export_schedule_to_csv(
        best_kk_plan_a,
        best_kl_plan_a,
        kk_baseline_capacities,
        kl_baseline_capacities,
        "optimized_schedule_szenario_A.csv",
    )

    total_km_a = best_kk_km_a + best_kl_km_a
    trips_a = calculate_away_trips(kk_baseline_capacities) + calculate_away_trips(kl_baseline_capacities)
    avg_km_a = total_km_a / trips_a
    if trips_a != baseline_matches_from_capacities:
        raise RuntimeError(
            "Szenario A hat nicht dieselbe Spielzahl wie die aus der Ist-Baseline "
            "rekonstruierte Staffelkapazität."
        )

    # SZENARIO B: möglichst ausgeglichene Staffelgrößen mit Zielmittel 15.
    print("\n" + "#" * 65)
    print(" SZENARIO B: Organisatorischer Kapazitätsausgleich")
    print("#" * 65)

    num_kk_b = calculate_optimal_staffeln(len(kk_teams))
    num_kl_b = calculate_optimal_staffeln(len(kl_teams))
    kk_capacities_b = build_balanced_capacities(len(kk_teams), num_kk_b)
    kl_capacities_b = build_balanced_capacities(len(kl_teams), num_kl_b)

    best_kk_km_b, best_kk_plan_b = run_evolution(
        kk_teams, kk_capacities_b, dist_matrix, "Kreisklasse (Szenario B)"
    )
    best_kl_km_b, best_kl_plan_b = run_evolution(
        kl_teams, kl_capacities_b, dist_matrix, "Kreisliga (Szenario B)"
    )
    export_schedule_to_csv(
        best_kk_plan_b,
        best_kl_plan_b,
        kk_capacities_b,
        kl_capacities_b,
        "optimized_schedule_szenario_B.csv",
    )

    total_km_b = best_kk_km_b + best_kl_km_b
    trips_b = calculate_away_trips(kk_capacities_b) + calculate_away_trips(kl_capacities_b)
    avg_km_b = total_km_b / trips_b

    print("\n" + "=" * 72)
    print(" FINALER STATISTIK-REPORT")
    print("=" * 72)
    print(
        f"Ist-Baseline: {BASELINE_KM:,.2f} km | {baseline_matches_from_capacities} Spiele/Auswärtsfahrten "
        f"| Ø {baseline_avg_km:.2f} km/Fahrt"
    )
    print(f"Szenario A:   {total_km_a:,.2f} km | {trips_a} Spiele/Auswärtsfahrten | Ø {avg_km_a:.2f} km/Fahrt")
    print(f"Distanzreduktion A: {(BASELINE_KM - total_km_a) / BASELINE_KM * 100:.2f} %")
    print(f"Szenario B:   {total_km_b:,.2f} km | {trips_b} Spiele/Auswärtsfahrten | Ø {avg_km_b:.2f} km/Fahrt")
    print(f"Zusätzliche Spiele/Fahrten B gegenüber Baseline: {trips_b - baseline_matches_from_capacities:+d}")
    print(f"Relative Reduktion der mittleren Fahrtstrecke B: {(baseline_avg_km - avg_km_b) / baseline_avg_km * 100:.2f} %")
    print("=" * 72)


if __name__ == "__main__":
    main()

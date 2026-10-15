import pytest
from ea.ea_optimizer import (
    get_base_club_name,
    order_crossover,
    swap_mutation,
    calculate_fitness,
    calculate_optimal_staffeln,
    calculate_away_trips,
    PENALTY_KM
)

def test_get_base_club_name():
    """Testet die Extraktion des Stammvereins zur Penalty-Prüfung."""
    assert get_base_club_name("FC Altona 93 2") == "FC Altona"
    assert get_base_club_name("Eimsbütteler TV I") == "Eimsbütteler TV I"
    assert get_base_club_name("FC St. Pauli 3") == "FC St. Pauli"

def test_order_crossover_validity(sample_teams):
    """Prüft, ob der Order-Crossover (OX) gültige Permutationen erzeugt."""
    parent1 = sample_teams.copy()
    parent2 = sample_teams[::-1]  # Umgekehrte Reihenfolge

    child = order_crossover(parent1, parent2)

    # 1. Länge muss identisch sein
    assert len(child) == len(parent1)
    # 2. Alle Teams müssen exakt einmal enthalten sein (keine Duplikate / Verluste)
    assert sorted(child) == sorted(parent1)

def test_swap_mutation_integrity(sample_teams):
    """Prüft, ob die Swap-Mutation die Elementmenge unverändert lässt."""
    individual = sample_teams.copy()
    # Mutation mit 100% Wahrscheinlichkeit erzwingen
    swap_mutation(individual, current_rate=1.0)

    assert len(individual) == len(sample_teams)
    assert sorted(individual) == sorted(sample_teams)

def test_calculate_fitness_without_penalty(sample_teams, mock_distance_matrix):
    """Testet die Fitnessberechnung bei zulässiger Verteilung (keine internen Duelle)."""
    # 8 Teams verteilt auf 2 Staffeln (je 4 Teams)
    # Staffel 1: Jeweils unterschiedliche Vereine
    # Staffel 2: Jeweils unterschiedliche Vereine
    valid_individual = [
        "Victoria 3", "GW Eimsbüttel 3", "Farmsen 1", "Bramfeld 2",
        "Victoria 4", "GW Eimsbüttel 4", "Farmsen 2", "Bramfeld 3"
    ]

    # Pro Staffel: 4 Teams -> 6 Paarungen -> Hin- & Rückspiel (12 Fahrten) @ 10 km = 120 km
    # 2 Staffeln = 240 km gesamt
    fitness = calculate_fitness(valid_individual, num_staffeln=2, dist_matrix=mock_distance_matrix)
    assert fitness == pytest.approx(240.0)


def test_calculate_fitness_with_penalties(sample_teams, mock_distance_matrix):
    """Testet, ob bei vereinsinternen Duellen die Strafkilometer korrekt aufgeschlagen werden."""
    # Staffel 1 (erste 4 Teams): Victoria 3 UND Victoria 4 -> 1 Penalty
    # Staffel 2 (zweite 4 Teams): GW Eimsbüttel 3 UND GW Eimsbüttel 4 -> 1 Penalty
    invalid_individual = [
        "Victoria 3", "Victoria 4", "Farmsen 1", "Bramfeld 2",
        "GW Eimsbüttel 3", "GW Eimsbüttel 4", "Farmsen 2", "Bramfeld 3"
    ]

    fitness = calculate_fitness(invalid_individual, num_staffeln=2, dist_matrix=mock_distance_matrix)
    # 240 km Basis-Distanz + 2 * PENALTY_KM (10.000) = 10.240 km
    expected_fitness = 240.0 + (2 * PENALTY_KM)

    assert fitness == pytest.approx(expected_fitness)

def test_capacity_and_trip_calculations():
    """Testet Hilfsfunktionen für Staffelgrößen und Auswärtsfahrten."""
    # 160 Teams / 15 = 10.67 -> gerundet 11 Staffeln
    assert calculate_optimal_staffeln(160) == 11
    # 8 Teams auf 2 Staffeln = 2 x (4 * 3) = 24 Auswärtsfahrten
    assert calculate_away_trips(num_teams=8, num_staffeln=2) == 24
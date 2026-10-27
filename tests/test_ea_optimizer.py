"""
Unit-Tests für den Evolutionären Algorithmus (ea_optimizer.py).
"""

import pytest
from src.ea.ea_optimizer import (
    get_base_club_name,
    order_crossover,
    swap_mutation,
    calculate_fitness,
    calculate_optimal_staffeln,
    calculate_away_trips,
    PENALTY_KM
)


def test_get_base_club_name():
    """Testet die Extraktion des Stammvereins zur Penalty-Prüfung (inkl. Casefolding)."""
    assert get_base_club_name("FC Altona 93 2") == "fc altona 93"


def test_order_crossover_validity():
    """Testet, ob der Order Crossover (OX1) eine gültige Permutation ohne Duplikate erzeugt."""
    p1 = ["A", "B", "C", "D", "E", "F"]
    p2 = ["F", "E", "D", "C", "B", "A"]
    child = order_crossover(p1, p2)
    assert len(child) == len(p1)
    assert set(child) == set(p1)


def test_swap_mutation_integrity():
    """Testet, ob die Swap-Mutation die Menge der Elemente unverändert lässt."""
    ind = ["A", "B", "C", "D", "E"]
    original = list(ind)
    swap_mutation(ind, current_rate=1.0)
    assert len(ind) == len(original)
    assert set(ind) == set(original)


def test_calculate_fitness_without_penalty(sample_teams, mock_distance_matrix):
    """Testet die Fitnessberechnung bei zulässiger Verteilung (keine internen Duelle)."""
    valid_individual = [
        "Victoria 3", "GW Eimsbüttel 3", "Farmsen 1", "Bramfeld 2",
        "Victoria 4", "GW Eimsbüttel 4", "Farmsen 2", "Bramfeld 3"
    ]

    # Pro Staffel: 4 Teams -> 6 Paarungen -> Hin- & Rückspiel (12 Fahrten) @ 10 km = 120 km
    # 2 Staffeln = 240 km gesamt
    fitness = calculate_fitness(valid_individual, staffel_sizes=[4, 4], dist_matrix=mock_distance_matrix)
    assert fitness == 240.0


def test_calculate_fitness_with_penalties(sample_teams, mock_distance_matrix):
    """Testet, ob bei vereinsinternen Duellen die Strafkilometer korrekt aufgeschlagen werden."""
    invalid_individual = [
        "Victoria 3", "Victoria 4", "Farmsen 1", "Bramfeld 2",
        "GW Eimsbüttel 3", "GW Eimsbüttel 4", "Farmsen 2", "Bramfeld 3"
    ]

    fitness = calculate_fitness(invalid_individual, staffel_sizes=[4, 4], dist_matrix=mock_distance_matrix)
    # 240 km Basisdistanz + 2 * PENALTY_KM
    expected_fitness = 240.0 + (2 * PENALTY_KM)
    assert fitness == expected_fitness


def test_capacity_and_trip_calculations():
    """Testet Hilfsfunktionen für Staffelgrößen und Auswärtsfahrten."""
    # Kreisklasse 2025/2026: 153 Teams / 15 = 10.2 -> gerundet 10 Staffeln
    assert calculate_optimal_staffeln(153) == 10

    # Kreisliga 2025/2026: 119 Teams / 15 = 7.93 -> gerundet 8 Staffeln
    assert calculate_optimal_staffeln(119) == 8

    # 8 Teams auf 2 Staffeln je 4 Teams -> [4, 4] -> 2 x (4 * 3) = 24 Auswärtsfahrten
    assert calculate_away_trips([4, 4]) == 24
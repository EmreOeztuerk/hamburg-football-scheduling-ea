"""
Unit-Tests für Geocoding-Klassifikation und OSRM-Distanzmatrix-Integrität.
"""

import os
import pytest
from geocoder.distance_matrix import is_south_of_elbe
from src.ea.ea_optimizer import _load_distance_matrix

MATRIX_PATH = os.path.join("data", "distance_matrix.csv")


def test_is_south_of_elbe():
    """Prüft die Geozonen-Trennlinie für Nord- vs. Süd-Hamburg."""
    # Harburg (Südlich der Elbe)
    assert is_south_of_elbe(lat=53.46, lon=9.98) is True
    # Eimsbüttel (Nördlich der Elbe)
    assert is_south_of_elbe(lat=53.58, lon=9.95) is False


def test_osrm_matrix_integrity():
    """
    Validiert die mathematischen Invarianten der OSRM-Distanzmatrix:
    1. Exakt 272 geocodierte Mannschaften
    2. Diagonalelemente d(i,i) = 0.0
    3. Symmetrie d(i,j) == d(j,i)
    4. Keine negativen Distanzwerte
    """
    if not os.path.exists(MATRIX_PATH):
        pytest.skip(f"Matrix-Datei {MATRIX_PATH} nicht vorhanden. Überspringe OSRM-Test.")

    matrix = _load_distance_matrix(MATRIX_PATH)
    teams = list(matrix.keys())

    # 1. Richtige Anzahl an Teams für die Saison 2025/2026
    assert len(teams) == 272, f"Erwartet wurden 272 Teams, erhalten: {len(teams)}"

    for team_a in teams:
        # 2. Selbst-Distanz muss 0 sein
        assert matrix[team_a][team_a] == 0.0, f"Diagonalelement für {team_a} ist nicht 0.0"

        for team_b in teams:
            dist_ab = matrix[team_a][team_b]
            dist_ba = matrix[team_b][team_a]

            # 3. Positivitätsbedingung
            assert dist_ab >= 0.0, f"Negative Distanz zwischen {team_a} und {team_b}"

            # 4. Symmetriebedingung
            assert pytest.approx(dist_ab, abs=1e-3) == dist_ba, (
                f"Asymmetrie in OSRM-Matrix zwischen {team_a} und {team_b}"
            )

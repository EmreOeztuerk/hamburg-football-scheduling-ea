import pytest

@pytest.fixture
def sample_teams():
    """Erstellt eine Test-Liste mit deinen gewünschten Vereinsnamen."""
    return [
        "Victoria 3",
        "Victoria 4",
        "GW Eimsbüttel 3",
        "GW Eimsbüttel 4",
        "Farmsen 1",
        "Farmsen 2",
        "Bramfeld 2",
        "Bramfeld 3"
    ]

@pytest.fixture
def mock_distance_matrix(sample_teams):
    """Erstellt eine symmetrische Test-Distanzmatrix für alle sample_teams."""
    matrix = {t: {} for t in sample_teams}
    for t1 in sample_teams:
        for t2 in sample_teams:
            if t1 == t2:
                matrix[t1][t2] = 0.0
            else:
                matrix[t1][t2] = 10.0
    return matrix
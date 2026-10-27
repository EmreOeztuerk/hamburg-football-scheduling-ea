"""
Batch-Runner für die stochastische Evaluation (N = 30 Läufe pro Szenario).
Führt exakt 30 unabhängige Läufe aus, protokolliert alle statistischen Kennzahlen
sowie die Konvergenzhistorie des Rekordlaufs (für plot_convergence.py) in einer JSON-Datei
und speichert den besten Spielplan als CSV ab.
"""

import os
import random
import time
import json
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

from src.ea.ea_optimizer import (
    run_evolution,
    _load_distance_matrix
)

# Pfad-Setup ausgehend von src/ea/
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
MATRIX_PATH = os.path.join(DATA_DIR, "distance_matrix.csv")
TEAMS_PATH = os.path.join(DATA_DIR, "hamburg_vereine_geocoded_final.csv")


def single_run(run_id: int, seed: int, teams: list, staffel_sizes: list, dist_matrix: dict, szenario: str = "A"):
    """Führt einen einzelnen Lauf aus, misst die Laufzeit und fängt Verlaufshistorien ab."""
    random.seed(seed)
    np.random.seed(seed)

    start_time = time.time()

    # Aufruf der Evolution
    result = run_evolution(
        teams=teams,
        staffel_sizes=staffel_sizes,
        dist_matrix=dist_matrix,
        label=f"Szenario_{szenario}_Run_{run_id}"
    )

    elapsed = time.time() - start_time

    # Robuste Zuordnung der Rückgabewerte aus run_evolution:
    # run_evolution liefert: (best_fitness, best_individual, history_fitness, history_mutation)
    history_fitness = []
    history_mutation = []

    if isinstance(result, (tuple, list)):
        best_fitness = result[0]
        best_individual = result[1] if len(result) > 1 else []
        if len(result) >= 3:
            history_fitness = result[2]
        if len(result) >= 4:
            history_mutation = result[3]
    else:
        best_fitness = result
        best_individual = []

    # Falls best_fitness fälschlicherweise noch in einer Liste verpackt ist:
    if isinstance(best_fitness, (tuple, list)):
        best_fitness = best_fitness[-1]

    return {
        "run_id": run_id,
        "seed": seed,
        "fitness_km": round(float(best_fitness), 2),
        "execution_time_sec": round(elapsed, 2),
        "individual": best_individual,
        "history_fitness": history_fitness,
        "history_mutation": history_mutation
    }

def run_batch_count(szenario: str, num_runs: int = 30, max_workers: int = 4):
    """
    Führt exakt N unabhängige Läufe für ein Szenario aus, wertet die Statistik aus
    und sichert die Konvergenzhistorie des Rekordlaufs für spätere Plots.
    """
    print("\n" + "=" * 65)
    print(f" STARTE BATCH-OPTIMIERUNG: SZENARIO {szenario} ({num_runs} Läufe auf {max_workers} Cores)")
    print("=" * 65)

    dist_matrix = _load_distance_matrix(MATRIX_PATH)
    all_teams_df = pd.read_csv(TEAMS_PATH, sep=";", encoding="utf-8-sig")

    # Filtert alle Kreisklassen-Teams (KK)
    kk_teams = all_teams_df[all_teams_df["Staffel"].str.startswith("KK")]["Mannschaft"].tolist()

    if szenario == "A":
        # Szenario A: Ist-Kapazitäten (12 Staffeln)
        staffel_sizes = [11] + [12] * 4 + [13] * 4 + [14] * 3
    else:
        # Szenario B: Ausgeglichen (10 Staffeln: 3x16, 7x15)
        staffel_sizes = [16, 16, 16, 15, 15, 15, 15, 15, 15, 15]

    results = []
    start_time_batch = time.time()

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i in range(num_runs):
            run_id = i + 1
            seed = 1000 + run_id * 37
            f = executor.submit(single_run, run_id, seed, kk_teams, staffel_sizes, dist_matrix, szenario)
            futures.append(f)

        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            print(f"[SZN {szenario}] Lauf #{res['run_id']}/{num_runs} beendet: "
                  f"Fitness = {res['fitness_km']} km | Dauer = {res['execution_time_sec']}s (Seed: {res['seed']})")

    # Sortieren nach Fitness (bestes Ergebnis an Index 0)
    results.sort(key=lambda x: x["fitness_km"])
    best_run = results[0]
    worst_run = results[-1]

    all_fitness = [r["fitness_km"] for r in results]
    all_times = [r["execution_time_sec"] for r in results]

    avg_fitness = float(np.mean(all_fitness))
    std_fitness = float(np.std(all_fitness))
    avg_time = float(np.mean(all_times))

    print("\n" + "-" * 50)
    print(f" FAZIT SZENARIO {szenario} ({num_runs} Läufe absolviert):")
    print(f" -> Bestes Ergebnis:     {best_run['fitness_km']} km (Lauf #{best_run['run_id']}, Seed {best_run['seed']})")
    print(f" -> Schlechtestes Ergeb.: {worst_run['fitness_km']} km")
    print(f" -> Durchschn. Fitness:  {avg_fitness:.2f} km (± {std_fitness:.2f} km)")
    print(f" -> Durchschn. Laufzeit: {avg_time:.2f} Sekunden pro Lauf")
    print("-" * 50)

    # 1. Besten Spielplan als CSV abspeichern
    output_csv = os.path.join(DATA_DIR, f"optimized_schedule_szenario_{szenario}.csv")
    _export_schedule_to_csv(best_run["individual"], staffel_sizes, all_teams_df, output_csv)

    # 2. JSON-Protokoll inklusive der Konvergenzhistorie DES BESTEN LAUFS speichern
    summary_log = {
        "szenario": szenario,
        "total_runs_completed": num_runs,
        "total_duration_minutes": round((time.time() - start_time_batch) / 60, 2),
        "best_fitness_km": best_run["fitness_km"],
        "worst_fitness_km": worst_run["fitness_km"],
        "mean_fitness_km": round(avg_fitness, 2),
        "std_dev_km": round(std_fitness, 2),
        "avg_execution_time_sec": round(avg_time, 2),
        "best_seed": best_run["seed"],
        "best_run_id": best_run["run_id"],
        # Konvergenzverlauf des Rekordlaufs für plot_convergence.py
        "best_run_convergence_history": best_run["history_fitness"],
        "best_run_mutation_history": best_run["history_mutation"],
        # Einzelergebnisse aller 30 Läufe (ohne große Genom-Vektoren)
        "all_runs_detailed": [
            {
                "run_id": r["run_id"],
                "seed": r["seed"],
                "fitness_km": r["fitness_km"],
                "execution_time_sec": r["execution_time_sec"]
            }
            for r in results
        ]
    }

    log_path = os.path.join(DATA_DIR, f"batch_summary_szenario_{szenario}.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(summary_log, f, indent=4, ensure_ascii=False)

    print(f"✓ Bester Spielplan gespeichert: {output_csv}")
    print(f"✓ Statistik & Rekord-Historie gespeichert: {log_path}\n")


def _export_schedule_to_csv(individual: list, staffel_sizes: list, teams_df: pd.DataFrame, output_path: str):
    """Formatiert den besten Spielplan und speichert ihn als CSV."""
    rows = []
    idx = 0
    for staffel_nr, size in enumerate(staffel_sizes, 1):
        staffel_teams = individual[idx:idx + size]
        idx += size
        for team in staffel_teams:
            rows.append({
                "Mannschaft": team,
                "assigned_staffel": f"Kreisklasse Staffel {staffel_nr:02d}"
            })

    export_df = pd.DataFrame(rows)
    final_df = export_df.merge(teams_df, on="Mannschaft", how="left")
    final_df.to_csv(output_path, index=False, encoding="utf-8-sig", sep=";")


if __name__ == "__main__":
    RUNS_PER_SCENARIO = 30  # Statistische Standard-Stichprobengröße (N=30)
    MAX_CORES = 4          # Anzahl paralleler CPU-Kerne

    print("==================================================")
    print("   START BATCH-OPTIMIERUNG (N = 30 Läufe pro Szenario)")
    print("==================================================")

    # 1. Szenario A durchrechnen
    run_batch_count("A", num_runs=RUNS_PER_SCENARIO, max_workers=MAX_CORES)

    # 2. Szenario B durchrechnen
    run_batch_count("B", num_runs=RUNS_PER_SCENARIO, max_workers=MAX_CORES)

    print("\n==================================================")
    print("✓ ALLE 60 LÄUFE ERFOLGREICH BEENDET UND PROTOKOLLIERT!")
    print("==================================================")
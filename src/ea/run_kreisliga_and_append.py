import csv
import json
import multiprocessing as mp
import os
import random
import time
from typing import Dict, List, Tuple

import pandas as pd

# Importiert die Kernfunktionen direkt aus deiner ea_optimizer.py
from src.ea.ea_optimizer import (
    _load_distance_matrix,
    export_schedule_to_csv,
    run_evolution,
)


def append_kreisliga_to_existing_csv(
    best_individual: list,
    staffel_sizes: list,
    teams_df: pd.DataFrame,
    csv_path: str,
):
    """Formatiert den besten Kreisliga-Spielplan und fügt ihn unten an die

    bestehende Szenario-CSV an (ohne die Kreisklassen-Einträge zu
    überschreiben).
    """
    rows = []
    idx = 0
    for staffel_nr, size in enumerate(staffel_sizes, 1):
        staffel_teams = best_individual[idx : idx + size]
        idx += size
        for team in staffel_teams:
            rows.append({
                "Mannschaft": team,
                "assigned_staffel": f"Kreisliga Staffel {staffel_nr:02d}",
            })

    kl_df = pd.DataFrame(rows).merge(teams_df, on="Mannschaft", how="left")

    if os.path.exists(csv_path):
        existing_df = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig")
        # Alte Kreisliga-Einträge entfernen, um Duplikate bei erneuten Läufen zu vermeiden
        existing_filtered = existing_df[
            ~existing_df["assigned_staffel"]
            .astype(str)
            .str.startswith("Kreisliga")
        ]
        final_df = pd.concat([existing_filtered, kl_df], ignore_index=True)
    else:
        final_df = kl_df

    final_df.to_csv(csv_path, index=False, sep=";", encoding="utf-8-sig")
    print(
        f"✓ Kreisliga-Einstaffelung erfolgreich an {csv_path} angehängt!"
        f" (Gesamt-Teams in CSV: {len(final_df)})"
    )


def _worker_run(args: Tuple) -> Tuple[int, int, float, List[str], float]:
    """Worker-Funktion für parallele Ausführung über multiprocessing."""
    run_idx, seed, teams, staffel_sizes, dist_matrix, label = args

    # Deterministic Seed setzen
    random.seed(seed)

    start_time = time.time()
    best_fit, best_ind = run_evolution(
        teams=teams,
        staffel_sizes=staffel_sizes,
        dist_matrix=dist_matrix,
        label=f"{label}_Run_{run_idx}",
    )
    duration = time.time() - start_time

    return run_idx, seed, best_fit, best_ind, duration


def execute_kl_batch(
    teams: List[str],
    staffel_sizes: List[int],
    dist_matrix: Dict[str, Dict[str, float]],
    szenario_name: str,
    num_runs: int = 30,
    n_cores: int = 4,
    output_json: str = None,
):
    """Führt N unabhängige Evolutionsläufe für die Kreisliga aus."""
    print(
        f"\n================================================================="
    )
    print(
        f" STARTE BATCH-OPTIMIERUNG: {szenario_name} ({num_runs} Läufe auf"
        f" {n_cores} Cores)"
    )
    print(
        f"================================================================="
    )

    base_seeds = [1037 + i * 37 for i in range(num_runs)]
    tasks = [
        (
            i + 1,
            base_seeds[i],
            teams,
            staffel_sizes,
            dist_matrix,
            szenario_name,
        )
        for i in range(num_runs)
    ]

    all_results = []
    best_overall_fitness = float("inf")
    best_overall_individual = None

    if n_cores > 1:
        with mp.Pool(processes=n_cores) as pool:
            results = pool.map(_worker_run, tasks)
    else:
        results = [_worker_run(t) for t in tasks]

    for run_idx, seed, best_fit, best_ind, duration in results:
        all_results.append({
            "run": run_idx,
            "seed": seed,
            "best_fitness_km": round(best_fit, 2),
            "duration_sec": round(duration, 2),
        })

        print(
            f"[{szenario_name}] Lauf #{run_idx}/{num_runs} beendet: Fitness ="
            f" {best_fit:.2f} km | Dauer = {duration:.2f}s (Seed: {seed})"
        )

        if best_fit < best_overall_fitness:
            best_overall_fitness = best_fit
            best_overall_individual = best_ind

    fitness_values = [r["best_fitness_km"] for r in all_results]
    durations = [r["duration_sec"] for r in all_results]

    summary = {
        "szenario": szenario_name,
        "num_runs": num_runs,
        "best_overall_fitness_km": min(fitness_values),
        "worst_overall_fitness_km": max(fitness_values),
        "mean_fitness_km": round(pd.Series(fitness_values).mean(), 2),
        "std_fitness_km": round(pd.Series(fitness_values).std(), 2),
        "mean_duration_sec": round(pd.Series(durations).mean(), 2),
        "runs_detail": all_results,
    }

    if output_json:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=4, ensure_ascii=False)
        print(f"✓ Statistik & Protokoll gespeichert unter: {output_json}")

    return best_overall_individual, summary


def main():
    BASE_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    DATA_DIR = os.path.join(BASE_DIR, "data")

    # Distanzmatrix einlesen
    matrix_csv = os.path.join(DATA_DIR, "distance_matrix.csv")
    dist_matrix = _load_distance_matrix(matrix_csv)

    # Teams einlesen & auf Kreisliga (KL) filtern
    teams_csv = os.path.join(DATA_DIR, "hamburg_vereine_geocoded_final.csv")
    all_teams_df = pd.read_csv(teams_csv, sep=";", encoding="utf-8-sig")

    kl_teams_df = all_teams_df[
        all_teams_df["Staffel"].str.startswith("KL")
    ].copy()
    kl_teams = kl_teams_df["Mannschaft"].tolist()

    print(f"Gefundene Kreisliga-Teams: {len(kl_teams)}")

    # Kapazitäten für 119 Kreisliga-Teams (8 Staffeln: 7x15 + 1x14)
    staffel_sizes_A = [15, 15, 15, 15, 15, 15, 15, 14]
    staffel_sizes_B = [15, 15, 15, 15, 15, 15, 15, 14]

    # Pfade zu den Gesamt-CSVs (wo aktuell schon die Kreisklasse drin steht)
    csv_szn_a = os.path.join(DATA_DIR, "optimized_schedule_szenario_A.csv")
    csv_szn_b = os.path.join(DATA_DIR, "optimized_schedule_szenario_B.csv")

    # Pfade zu den neuen Kreisliga-JSONs
    json_szn_a = os.path.join(
        DATA_DIR, "batch_summary_kreisliga_szenario_A.json"
    )
    json_szn_b = os.path.join(
        DATA_DIR, "batch_summary_kreisliga_szenario_B.json"
    )

    # 1. SZENARIO A (Kreisliga)
    best_ind_a, _ = execute_kl_batch(
        teams=kl_teams,
        staffel_sizes=staffel_sizes_A,
        dist_matrix=dist_matrix,
        szenario_name="Kreisliga_Szenario_A",
        num_runs=30,
        n_cores=4,
        output_json=json_szn_a,
    )
    append_kreisliga_to_existing_csv(
        best_ind_a, staffel_sizes_A, kl_teams_df, csv_szn_a
    )

    # 2. SZENARIO B (Kreisliga)
    best_ind_b, _ = execute_kl_batch(
        teams=kl_teams,
        staffel_sizes=staffel_sizes_B,
        dist_matrix=dist_matrix,
        szenario_name="Kreisliga_Szenario_B",
        num_runs=30,
        n_cores=4,
        output_json=json_szn_b,
    )
    append_kreisliga_to_existing_csv(
        best_ind_b, staffel_sizes_B, kl_teams_df, csv_szn_b
    )

    print("\n==================================================")
    print("✓ KREISLIGA ERFOLGREICH OPTIMIERT UND ANGEHÄNGT!")
    print("==================================================")


if __name__ == "__main__":
    main()
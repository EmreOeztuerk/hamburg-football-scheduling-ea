"""
Generiert ein Boxplot-Diagramm mit Einzelpunkten (Jitter-Overlay)
zur Visualisierung der stochastischen Ergebnissicherheit über 30 GA-Läufe.
"""

import json
import os
import matplotlib.pyplot as plt
import numpy as np

# =============================================================================
# PFAD-KONFIGURATION
# =============================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

FILES = {
    "KK Szenario A": os.path.join(DATA_DIR, "batch_summary_szenario_A.json"),
    "KK Szenario B": os.path.join(DATA_DIR, "batch_summary_szenario_B.json"),
    "KL Szenario A": os.path.join(DATA_DIR, "batch_summary_kreisliga_szenario_A.json"),
    "KL Szenario B": os.path.join(DATA_DIR, "batch_summary_kreisliga_szenario_B.json"),
}

plot_data = []
labels = [
    "Kreisklasse\nSzenario A",
    "Kreisklasse\nSzenario B",
    "Kreisliga\nSzenario A",
    "Kreisliga\nSzenario B",
]

for label, filepath in FILES.items():
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Datei nicht gefunden: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "all_runs_detailed" in data:
        fitnesses = [r["fitness_km"] for r in data["all_runs_detailed"]]
    elif "runs_detail" in data:
        fitnesses = [r["best_fitness_km"] for r in data["runs_detail"]]

    plot_data.append(fitnesses)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linestyle": "--",
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

fig, ax = plt.subplots(figsize=(10, 5))
colors = ["#0072B2", "#D55E00", "#009E73", "#CC79A7"]

bp = ax.boxplot(
    plot_data,
    patch_artist=True,
    labels=labels,
    boxprops=dict(linewidth=1.2),
    capprops=dict(linewidth=1.2),
    whiskerprops=dict(linewidth=1.2),
    flierprops=dict(
        marker="o", markerfacecolor="#e63946", markersize=4, alpha=0.6
    ),
    medianprops=dict(color="black", linewidth=1.5),
)

for patch, color in zip(bp["boxes"], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

ax.set_title(
    "Stochastische Ergebnissicherheit über 30 unabhängige GA-Läufe",
    fontsize=13,
    fontweight="bold",
    pad=15,
)
ax.set_ylabel("Gesamtkilometer (Minimierte Fitness)", fontsize=11)
ax.yaxis.set_major_formatter(
    plt.FuncFormatter(lambda x, p: f"{int(x):,}".replace(",", "."))
)

# Punkte-Overlay (Jitter) für volle Transparenz der 30 Läufe
for i, d in enumerate(plot_data, start=1):
    x = np.random.normal(i, 0.04, size=len(d))
    ax.plot(x, d, "o", color="black", alpha=0.35, markersize=3.5)

plt.tight_layout()
output_img = os.path.join(DATA_DIR, "eval_stochastic_stability_30runs.png")
plt.savefig(output_img, dpi=300)
print(f"✓ Grafik erfolgreich gespeichert unter: {output_img}")
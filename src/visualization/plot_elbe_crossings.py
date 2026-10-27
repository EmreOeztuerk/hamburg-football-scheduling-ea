"""
Analyse der verkehrstechnischen Nadelöhre (Elbüberquerungen).
"""

import os
import pandas as pd
import matplotlib.pyplot as plt

# PLOT-DESIGN (Globales Setup)
ACADEMIC_COLORS = ['#0072B2', '#E69F00', '#009E73', '#D55E00', '#CC79A7', '#56B4E9']

plt.rcParams.update({
    # Farbpalette global setzen
    'axes.prop_cycle': plt.cycler(color=ACADEMIC_COLORS),
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    # Rahmen entfernen
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': True,
    'grid.alpha': 0.25,
    'grid.linestyle': '--',
    'axes.titlesize': 13,
    'axes.titleweight': 'bold',
    'axes.labelsize': 11,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.frameon': False,
    'legend.fontsize': 10,
    'figure.figsize': (9, 6),
    'savefig.dpi': 300,
    'savefig.bbox': 'tight'
})

# Pfadkonfiguration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

GEO_CSV = os.path.join(DATA_DIR, "hamburg_vereine_geocoded_final.csv")
SCHEDULE_A_CSV = os.path.join(DATA_DIR, "optimized_schedule_szenario_A.csv")
SCHEDULE_B_CSV = os.path.join(DATA_DIR, "optimized_schedule_szenario_B.csv")

LABELS = ['Baseline\n(Ist-Zustand)', 'Szenario A\n(Struktur-Erhalt)', 'Szenario B\n(Kapazitätsausgleich)']


def read_csv_robust(filepath: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(filepath, sep=';', encoding='utf-8-sig')
        if len(df.columns) <= 1:
            df = pd.read_csv(filepath, sep=',', encoding='utf-8-sig')
    except Exception:
        df = pd.read_csv(filepath, sep=None, engine='python', encoding='utf-8-sig')
    return df


def is_south_of_elbe(lat: float, lon: float) -> bool:
    lat_river = -0.2 * (lon - 10.05) + 53.50
    return lat < lat_river


def load_geodata() -> dict:
    df = read_csv_robust(GEO_CSV)
    cols = [str(c).strip().lower() for c in df.columns]
    df.columns = cols

    lat_cols = [c for c in cols if 'lat' in c or 'breite' in c]
    lon_cols = [c for c in cols if 'lon' in c or 'laenge' in c or 'länge' in c]
    team_cols = [c for c in cols if 'mann' in c or 'team' in c or 'verein' in c]
    staffel_cols = [c for c in cols if 'staffel' in c]

    lat_name = lat_cols[0] if lat_cols else df.columns[2]
    lon_name = lon_cols[0] if lon_cols else df.columns[3]
    team_name_col = team_cols[0] if team_cols else df.columns[1]
    staffel_name_col = staffel_cols[0] if staffel_cols else df.columns[0]

    team_geo = {}
    for _, row in df.iterrows():
        t_name = str(row[team_name_col]).strip()
        try:
            lat_val = float(str(row[lat_name]).replace(',', '.'))
            lon_val = float(str(row[lon_name]).replace(',', '.'))
            team_geo[t_name] = {
                "baseline_staffel": str(row[staffel_name_col]).strip(),
                "lat": lat_val,
                "lon": lon_val
            }
        except (ValueError, TypeError):
            continue
    return team_geo


def load_schedule_dict(filepath: str, is_baseline: bool = False) -> dict:
    if not os.path.exists(filepath):
        return {}

    df = read_csv_robust(filepath)
    cols = [str(c).strip().lower() for c in df.columns]
    df.columns = cols

    team_cols = [c for c in cols if 'mann' in c or 'team' in c or 'verein' in c]
    team_name_col = team_cols[0] if team_cols else df.columns[0]

    if is_baseline:
        staffel_cols = [c for c in cols if 'staffel' in c]
        staffel_name_col = staffel_cols[0] if staffel_cols else df.columns[0]
    else:
        staffel_cols = [c for c in cols if 'assign' in c or 'szenario' in c or 'staffel' in c]
        staffel_name_col = staffel_cols[0] if staffel_cols else df.columns[1]

    staffeln = {}
    for _, row in df.iterrows():
        team = str(row[team_name_col]).strip()
        staffel = str(row[staffel_name_col]).strip()

        if staffel not in staffeln:
            staffeln[staffel] = []
        staffeln[staffel].append(team)

    return staffeln


def count_crossings(staffeln_dict: dict, team_geo: dict) -> int:
    total_crossings = 0
    for staffel, teams in staffeln_dict.items():
        # Nur Teams berücksichtigen, für die wir Geodaten haben
        valid_teams = [t for t in teams if t in team_geo]

        for i in range(len(valid_teams)):
            for j in range(i + 1, len(valid_teams)):
                t1, t2 = valid_teams[i], valid_teams[j]
                south1 = is_south_of_elbe(team_geo[t1]["lat"], team_geo[t1]["lon"])
                south2 = is_south_of_elbe(team_geo[t2]["lat"], team_geo[t2]["lon"])

                if south1 != south2:
                    total_crossings += 2

    return total_crossings


def format_change_text(scen_name: str, crossings: int, baseline: int) -> str:
    if baseline == 0:
        return f"{scen_name}: {crossings} Fahrten"
    diff = ((baseline - crossings) / baseline) * 100
    if diff >= 0:
        return f"{scen_name} reduziert Überquerungen um {diff:.1f} %"
    else:
        return f"{scen_name} steigt um {abs(diff):.1f} %"


def main():
    print("Starte Analyse der Nadelöhr-Auslastung (Elbüberquerungen)...")
    team_geo = load_geodata()

    baseline_staffeln = load_schedule_dict(GEO_CSV, is_baseline=True)
    crossings_baseline = count_crossings(baseline_staffeln, team_geo)

    schedule_a = load_schedule_dict(SCHEDULE_A_CSV, is_baseline=False)
    crossings_a = count_crossings(schedule_a, team_geo)

    schedule_b = load_schedule_dict(SCHEDULE_B_CSV, is_baseline=False)
    crossings_b = count_crossings(schedule_b, team_geo)

    print(f"HFV Baseline (Ist-Zustand): {crossings_baseline} Überquerungen")
    print(f"Szenario A (EA Optimiert):  {crossings_a} Überquerungen")
    print(f"Szenario B (Konsolidiert):  {crossings_b} Überquerungen")

    # Plot Generierung
    values = [crossings_baseline, crossings_a, crossings_b]

    plt.figure(figsize=(9, 6))
    bars = plt.bar(LABELS, values, color=ACADEMIC_COLORS[:3], width=0.6)

    max_v = max(values) if max(values) > 0 else 100
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval + (max_v * 0.02),
                 f"{int(yval)} Fahrten", ha='center', va='bottom', fontsize=11, fontweight='bold')

    plt.title("Auslastung städtischer Nadelöhre (Elbüberquerungen pro Saison)", fontsize=14, fontweight='bold', pad=15)
    plt.ylabel("Anzahl der Flussüberquerungen (Hin- & Rückspiel)", fontsize=12)
    plt.ylim(0, max_v * 1.15)

    if crossings_baseline > 0:
        text_a = format_change_text("Szenario A", crossings_a, crossings_baseline)
        text_b = format_change_text("Szenario B", crossings_b, crossings_baseline)
        info_text = f"Veränderung des Verkehrsaufkommens am Elbtunnel / Elbbrücken:\n{text_a} | {text_b}"
        plt.figtext(0.5, 0.02, info_text, ha="center", fontsize=10, style='italic', color='gray')

    plt.subplots_adjust(bottom=0.15)
    output_path = os.path.join(DATA_DIR, "eval_elbe_crossings.png")
    plt.savefig(output_path, dpi=300)
    print(f"\n✓ Plot erfolgreich gespeichert unter: {output_path}")


if __name__ == "__main__":
    main()
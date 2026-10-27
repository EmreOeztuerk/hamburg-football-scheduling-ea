"""
Visualisierung der Algorithmusergebnisse mit konvexen Hüllen.
"""

import os
import re
import random
import folium
import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull
from branca.element import Template, MacroElement

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

TEAMS_GEO_CSV = os.path.join(DATA_DIR, "hamburg_vereine_geocoded_final.csv")

SCENARIOS = [
    {
        "input": os.path.join(DATA_DIR, "optimized_schedule_szenario_A.csv"),
        "output": os.path.join(DATA_DIR, "hamburg_ea_optimized_map_szenario_A.html"),
        "title": "Szenario A (Struktur-Erhalt)"
    },
    {
        "input": os.path.join(DATA_DIR, "optimized_schedule_szenario_B.csv"),
        "output": os.path.join(DATA_DIR, "hamburg_ea_optimized_map_szenario_B.html"),
        "title": "Szenario B (Kapazitäts-Limit)"
    }
]

COLORS = [
    '#e6194B', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
    '#911eb4', '#42d4f4', '#f032e6', '#bfef45', '#fabed4',
    '#469990', '#dcbeff', '#9A6324', '#fffac8', '#800000',
    '#aaffc3', '#808000', '#ffd8b1', '#000075', '#a9a9a9'
]


def read_csv_robust(filepath: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(filepath, sep=';', encoding='utf-8-sig')
        if len(df.columns) <= 1:
            df = pd.read_csv(filepath, sep=',', encoding='utf-8-sig')
    except Exception:
        df = pd.read_csv(filepath, sep=None, engine='python', encoding='utf-8-sig')
    return df


def get_color_for_staffel(staffel_name: str) -> str:
    match = re.search(r'\d+', staffel_name)
    if not match:
        return COLORS[0]
    num = int(match.group())
    if "KK" in staffel_name or "Kreisklasse" in staffel_name:
        idx = num - 1
    elif "KL" in staffel_name or "Kreisliga" in staffel_name:
        idx = 11 + num
    else:
        idx = 0
    return COLORS[idx % len(COLORS)]


def load_geodata() -> dict:
    df = read_csv_robust(TEAMS_GEO_CSV)
    cols = [str(c).strip().lower() for c in df.columns]
    df.columns = cols

    lat_cols = [c for c in cols if 'lat' in c or 'breite' in c]
    lon_cols = [c for c in cols if 'lon' in c or 'laenge' in c or 'länge' in c]
    team_cols = [c for c in cols if 'mann' in c or 'team' in c or 'verein' in c]

    lat_name = lat_cols[0] if lat_cols else df.columns[2]
    lon_name = lon_cols[0] if lon_cols else df.columns[3]
    team_name_col = team_cols[0] if team_cols else df.columns[1]

    coords = {}
    for _, row in df.iterrows():
        t_name = str(row[team_name_col]).strip()
        try:
            lat_val = float(str(row[lat_name]).replace(',', '.'))
            lon_val = float(str(row[lon_name]).replace(',', '.'))
            coords[t_name] = (lat_val, lon_val)
        except (ValueError, TypeError):
            continue
    return coords


def generate_map_for_scenario(scenario: dict, coords: dict):
    if not os.path.exists(scenario["input"]):
        print(f"⚠ Datei nicht gefunden: {scenario['input']}")
        return

    df = read_csv_robust(scenario["input"])
    cols = [str(c).strip().lower() for c in df.columns]
    df.columns = cols

    team_cols = [c for c in cols if 'mann' in c or 'team' in c or 'verein' in c]
    staffel_cols = [c for c in cols if 'assign' in c or 'staffel' in c]

    team_name_col = team_cols[0] if team_cols else df.columns[0]
    staffel_name_col = staffel_cols[0] if staffel_cols else df.columns[1]

    staffeln = {}
    for _, row in df.iterrows():
        team = str(row[team_name_col]).strip()
        staffel = str(row[staffel_name_col]).strip()
        if staffel not in staffeln:
            staffeln[staffel] = []
        staffeln[staffel].append(team)

    m = folium.Map(
        location=[53.5511, 9.9937],
        zoom_start=11,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ"
    )

    legend_items = []
    for staffel_name, teams in sorted(staffeln.items()):
        staffel_color = get_color_for_staffel(staffel_name)
        legend_items.append((staffel_name, staffel_color))
        fg = folium.FeatureGroup(name=f"{staffel_name} (EA)")
        points_for_hull = []

        for team in teams:
            if team in coords:
                lat, lon = coords[team]
                j_lat = random.uniform(-0.0003, 0.0003)
                j_lon = random.uniform(-0.0003, 0.0003)
                f_lat, f_lon = lat + j_lat, lon + j_lon
                points_for_hull.append([f_lat, f_lon])

                folium.CircleMarker(
                    location=[f_lat, f_lon],
                    radius=6,
                    tooltip=f"<b>{team}</b><br>{scenario['title']}: {staffel_name}",
                    color="black",
                    weight=1,
                    fill=True,
                    fill_color=staffel_color,
                    fill_opacity=0.9
                ).add_to(fg)

        if len(points_for_hull) >= 3:
            pts = np.array(points_for_hull)
            try:
                hull = ConvexHull(pts)
                hull_pts = pts[hull.vertices].tolist()
                folium.Polygon(
                    locations=hull_pts,
                    color=staffel_color,
                    weight=2,
                    fill=True,
                    fill_color=staffel_color,
                    fill_opacity=0.15,
                    tooltip=f"{staffel_name} Cluster"
                ).add_to(fg)
            except Exception:
                pass

        fg.add_to(m)

    folium.LayerControl().add_to(m)

    legend_html = f'''
    {{% macro html(this, kwargs) %}}
    <div style="
        position: fixed; bottom: 50px; left: 50px; width: 220px; height: auto; 
        max-height: 60vh; overflow-y: auto; background-color: rgba(255, 255, 255, 0.95);
        border: 2px solid grey; z-index: 9999; font-size: 13px; padding: 10px; 
        border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.3); font-family: Arial, sans-serif;
        ">
        <h4 style="margin-top: 0; margin-bottom: 10px; font-size: 14px; font-weight: bold;">{scenario["title"]}</h4>
        <div style="display: flex; flex-direction: column; gap: 4px;">
    '''
    for name, color in legend_items:
        legend_html += f'''
            <div style="display: flex; align-items: center;">
                <span style="background-color: {color}; width: 12px; height: 12px; border-radius: 50%; display: inline-block; border: 1px solid black; margin-right: 8px;"></span>
                <span style="font-size: 11px;">{name}</span>
            </div>
        '''
    legend_html += '''
        </div>
    </div>
    {% endmacro %}
    '''
    macro = MacroElement()
    macro._template = Template(legend_html)
    m.get_root().add_child(macro)

    m.save(scenario["output"])
    print(f"✓ Geovisualisierung abgeschlossen: {scenario['output']}")


def main():
    coords = load_geodata()
    for scenario in SCENARIOS:
        generate_map_for_scenario(scenario, coords)


if __name__ == "__main__":
    main()
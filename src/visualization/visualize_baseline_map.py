"""
Visualisierung der tatsächlichen HFV-Baseline (Ist-Zustand).
Liest die ursprünglichen HFV-Staffeln direkt aus 'hamburg_vereine_geocoded_final.csv'
und zeichnet die echten Ist-Cluster inklusive konvexer Hüllen (Polygone).
Verwendet Esri Light Gray Canvas für eine saubere, helle Hintergrundkarte.
"""

import csv
import os
import re
import random
import folium
import numpy as np
from scipy.spatial import ConvexHull
from branca.element import Template, MacroElement

# Pfadkonfiguration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

INPUT_GEO_CSV = os.path.join(DATA_DIR, "hamburg_vereine_geocoded_final.csv")
OUTPUT_HTML = os.path.join(DATA_DIR, "hamburg_baseline_map.html")

# Eindeutige Farbpalette für die HFV-Ist-Staffeln
COLORS = [
    '#e6194B', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
    '#911eb4', '#42d4f4', '#f032e6', '#bfef45', '#fabed4',
    '#469990', '#dcbeff', '#9A6324', '#fffac8', '#800000',
    '#aaffc3', '#808000', '#ffd8b1', '#000075', '#a9a9a9'
]

def get_color_for_staffel(staffel_name: str) -> str:
    """Deterministische Farbzuordnung für die HFV-Ist-Staffeln."""
    match = re.search(r'\d+', staffel_name)
    if not match:
        return COLORS[0]
    num = int(match.group())
    if "KK" in staffel_name:
        idx = num - 1
    elif "KL" in staffel_name:
        idx = 11 + num
    else:
        idx = 0
    return COLORS[idx % len(COLORS)]

def main():
    print("=== Generiere Geovisualisierung der HFV Ist-Baseline ===")
    if not os.path.exists(INPUT_GEO_CSV):
        print(f"FEHLER: Datei nicht gefunden: {INPUT_GEO_CSV}")
        return

    staffeln = {}
    coords = {}

    # 1. Ursprüngliche HFV-Staffeln und Geodaten aus der Basis-CSV laden
    with open(INPUT_GEO_CSV, mode='r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader, None)  # Header überspringen
        for row in reader:
            if len(row) >= 4 and row[2] != "NICHT GEFUNDEN":
                staffel = row[0].strip()
                team = row[1].strip()
                try:
                    lat = float(row[2])
                    lon = float(row[3])
                except ValueError:
                    continue

                coords[team] = (lat, lon)
                staffeln.setdefault(staffel, []).append(team)

    print(f"Geladen: {len(staffeln)} HFV-Ist-Staffeln mit {len(coords)} Mannschaften.")

    # 2. Folium Karte mit Esri Light Gray Canvas initialisieren
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
        fg = folium.FeatureGroup(name=f"{staffel_name} (Ist)")
        points_for_hull = []

        for team in teams:
            if team in coords:
                lat, lon = coords[team]
                jitter_lat = random.uniform(-0.0003, 0.0003)
                jitter_lon = random.uniform(-0.0003, 0.0003)
                final_lat, final_lon = lat + jitter_lat, lon + jitter_lon
                points_for_hull.append([final_lat, final_lon])

                folium.CircleMarker(
                    location=[final_lat, final_lon],
                    radius=6,
                    tooltip=f"<b>{team}</b><br>HFV Baseline: {staffel_name}",
                    color="black",
                    weight=1,
                    fill=True,
                    fill_color=staffel_color,
                    fill_opacity=0.9
                ).add_to(fg)

        # Konvexe Hülle (Convex Hull Polygon) für die Ist-Staffel zeichnen
        if len(points_for_hull) >= 3:
            points_arr = np.array(points_for_hull)
            try:
                hull = ConvexHull(points_arr)
                hull_points = points_arr[hull.vertices].tolist()
                folium.Polygon(
                    locations=hull_points,
                    color=staffel_color,
                    weight=2,
                    fill=True,
                    fill_color=staffel_color,
                    fill_opacity=0.15,
                    tooltip=f"{staffel_name} Gebiet (Ist)"
                ).add_to(fg)
            except Exception:
                pass

        fg.add_to(m)

    folium.LayerControl().add_to(m)

    # Legende einbinden
    legend_html = '''
    {% macro html(this, kwargs) %}
    <div style="
        position: fixed; bottom: 50px; left: 50px; width: 180px; height: auto; 
        max-height: 60vh; overflow-y: auto; background-color: rgba(255, 255, 255, 0.9);
        border: 2px solid grey; z-index: 9999; font-size: 14px; padding: 10px; 
        border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.3); font-family: Arial, sans-serif;
        ">
        <h4 style="margin-top: 0; margin-bottom: 10px; font-size: 14px;">HFV Baseline (Ist)</h4>
        <div style="display: flex; flex-direction: column; gap: 5px;">
    '''
    for name, color in legend_items:
        legend_html += f'''
            <div style="display: flex; align-items: center;">
                <span style="background-color: {color}; width: 12px; height: 12px; border-radius: 50%; display: inline-block; border: 1px solid black; margin-right: 8px;"></span>
                <span style="font-size: 12px;">{name}</span>
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

    m.save(OUTPUT_HTML)
    print(f"Baseline-Visualisierung erfolgreich gespeichert unter: {OUTPUT_HTML}")

if __name__ == "__main__":
    main()
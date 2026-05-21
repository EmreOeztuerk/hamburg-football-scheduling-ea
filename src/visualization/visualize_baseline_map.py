"""
Visualisierung der Ist-Struktur (Baseline).

Erzeugt eine Georeferenzierungskarte mit deterministischer Farbzuordnung
und Jittering zur Vermeidung von Overplotting-Artefakten.
"""

import csv
import os
import re
import random
import folium
from branca.element import Template, MacroElement

# Pfadkonfiguration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

TEAMS_GEO_CSV = os.path.join(DATA_DIR, "hamburg_vereine_geocoded_final.csv")
MAP_OUTPUT = os.path.join(DATA_DIR, "hamburg_hfv_baseline_map.html")

# Palette mit 20 distinkten HEX-Codes für maximale Unterscheidbarkeit
COLORS = ['#e6194B', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
          '#911eb4', '#42d4f4', '#f032e6', '#bfef45', '#fabed4',
          '#469990', '#dcbeff', '#9A6324', '#fffac8', '#800000',
          '#aaffc3', '#808000', '#ffd8b1', '#000075', '#a9a9a9']

def get_color_for_staffel(staffel_name: str) -> str:
    """
    Implementiert eine deterministische Farbkodierung.
    Stellt sicher, dass Staffeln der Kreisklasse und Kreisliga
    kategorisch getrennte Farbräume verwenden.
    """
    match = re.search(r'\d+', staffel_name)
    if not match:
        return COLORS[0]

    num = int(match.group())

    # Kreisklasse (KK): Nutzt die Farb-Indizes 0 bis 11
    if "KK" in staffel_name:
        idx = num - 1
    # Kreisliga (KL): Nutzt die Farb-Indizes 12 bis 19
    elif "KL" in staffel_name:
        idx = 11 + num
    else:
        idx = 0

    # Fallback-Sicherung gegen IndexError
    if idx >= len(COLORS):
        idx = idx % len(COLORS)

    return COLORS[idx]

def generate_baseline_map():
    staffeln = {}

    # Einlesen der Geodaten
    with open(TEAMS_GEO_CSV, mode='r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)
        for row in reader:
            if len(row) < 4 or row[2] == "NICHT GEFUNDEN":
                continue

            staffel_name, team_name, lat, lon = row[0], row[1], float(row[2]), float(row[3])

            if staffel_name not in staffeln:
                staffeln[staffel_name] = []
            staffeln[staffel_name].append((team_name, lat, lon))

    # Initialisierung der Basiskarte
    m = folium.Map(location=[53.5511, 9.9937], zoom_start=11, tiles="CartoDB positron")
    legend_items = []

    # Karten-Layer aufbauen
    for staffel_name in sorted(staffeln.keys()):
        teams = staffeln[staffel_name]
        staffel_color = get_color_for_staffel(staffel_name)
        legend_items.append((staffel_name, staffel_color))

        fg = folium.FeatureGroup(name=f"{staffel_name} (Original)")
        for team_name, lat, lon in teams:

            # Stochastisches Jittering zur visuellen Trennung redundanter Koordinaten
            jitter_lat = random.uniform(-0.0003, 0.0003)
            jitter_lon = random.uniform(-0.0003, 0.0003)

            folium.CircleMarker(
                location=[lat + jitter_lat, lon + jitter_lon],
                radius=8,
                tooltip=f"<b>{team_name}</b><br>Original: {staffel_name}",
                color="black",
                weight=1,
                fill=True,
                fill_color=staffel_color,
                fill_opacity=0.8
            ).add_to(fg)
        fg.add_to(m)

    folium.LayerControl().add_to(m)

    # HTML-Struktur der Legende
    legend_html = '''
    {% macro html(this, kwargs) %}
    <div style="
        position: fixed; 
        bottom: 50px; left: 50px; width: 160px; height: auto; 
        max-height: 60vh; overflow-y: auto;
        background-color: rgba(255, 255, 255, 0.9);
        border: 2px solid grey; z-index: 9999; font-size: 14px;
        padding: 10px; border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
        font-family: Arial, sans-serif;
        ">
        <h4 style="margin-top: 0; margin-bottom: 10px;">Ist-Struktur</h4>
        <div style="display: flex; flex-direction: column; gap: 5px;">
    '''

    for name, color in legend_items:
        legend_html += f'''
            <div style="display: flex; align-items: center;">
                <span style="background-color: {color}; width: 12px; height: 12px; border-radius: 50%; display: inline-block; border: 1px solid black; margin-right: 8px;"></span>
                <span>{name}</span>
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

    m.save(MAP_OUTPUT)
    print(f"Geovisualisierung der Baseline abgeschlossen: {MAP_OUTPUT}")

if __name__ == "__main__":
    generate_baseline_map()
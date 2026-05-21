"""
Visualisierung der Algorithmusergebnisse.

Liest die generierten Cluster beider Szenarien aus und transformiert sie
in interaktive Karten-Layer. Verwendet dieselbe deterministische
Farbkodierung wie die Baseline-Visualisierung für konsistente Vergleiche.
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

# Identische Farbpalette wie in der Baseline-Visualisierung
COLORS = ['#e6194B', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
          '#911eb4', '#42d4f4', '#f032e6', '#bfef45', '#fabed4',
          '#469990', '#dcbeff', '#9A6324', '#fffac8', '#800000',
          '#aaffc3', '#808000', '#ffd8b1', '#000075', '#a9a9a9']

def get_color_for_staffel(staffel_name: str) -> str:
    """
    Implementiert eine deterministische Farbkodierung.
    Stellt sicher, dass z.B. KK-01 (Baseline) und KK-Opt-01 (EA)
    die exakt identische Farbe erhalten, während Ligen (KK vs. KL)
    strikt voneinander getrennt bleiben.
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

def load_geodata() -> dict:
    """Extrahiert die Basis-Koordinaten aus dem Geocoding-Export."""
    coords = {}
    with open(TEAMS_GEO_CSV, mode='r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)
        for row in reader:
            if len(row) >= 4 and row[2] != "NICHT GEFUNDEN":
                coords[row[1]] = (float(row[2]), float(row[3]))
    return coords

def generate_map_for_scenario(scenario: dict, coords: dict):
    """Generiert die HTML-Karte für ein spezifisches Evaluationsszenario."""
    if not os.path.exists(scenario["input"]):
        return

    staffeln = {}
    with open(scenario["input"], mode='r', encoding='utf-8-sig') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)
        for row in reader:
            staffel, team = row[1], row[2]
            if staffel not in staffeln:
                staffeln[staffel] = []
            staffeln[staffel].append(team)

    m = folium.Map(location=[53.5511, 9.9937], zoom_start=11, tiles="CartoDB positron")
    legend_items = []

    for staffel_name, teams in sorted(staffeln.items()):
        staffel_color = get_color_for_staffel(staffel_name)
        legend_items.append((staffel_name, staffel_color))

        fg = folium.FeatureGroup(name=f"{staffel_name} (EA)")
        for team in teams:
            if team in coords:
                lat, lon = coords[team]

                # Stochastisches Jittering
                jitter_lat = random.uniform(-0.0003, 0.0003)
                jitter_lon = random.uniform(-0.0003, 0.0003)

                folium.CircleMarker(
                    location=[lat + jitter_lat, lon + jitter_lon],
                    radius=8,
                    tooltip=f"<b>{team}</b><br>{scenario['title']}: {staffel_name}",
                    color="black",
                    weight=1,
                    fill=True,
                    fill_color=staffel_color,
                    fill_opacity=0.8
                ).add_to(fg)
        fg.add_to(m)

    folium.LayerControl().add_to(m)

    # HTML-Struktur der Legende
    legend_html = f'''
    {{% macro html(this, kwargs) %}}
    <div style="
        position: fixed; bottom: 50px; left: 50px; width: 180px; height: auto; 
        max-height: 60vh; overflow-y: auto; background-color: rgba(255, 255, 255, 0.9);
        border: 2px solid grey; z-index: 9999; font-size: 14px; padding: 10px; 
        border-radius: 5px; box-shadow: 2px 2px 5px rgba(0,0,0,0.3); font-family: Arial, sans-serif;
        ">
        <h4 style="margin-top: 0; margin-bottom: 10px; font-size: 14px;">{scenario["title"]}</h4>
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

    m.save(scenario["output"])
    print(f"Geovisualisierung abgeschlossen: {scenario['output']}")

def main():
    print("Initialisiere Kartengenerierung für Algorithmusergebnisse.")
    coords = load_geodata()

    for scenario in SCENARIOS:
        generate_map_for_scenario(scenario, coords)

    print("Alle Visualisierungen erfolgreich verarbeitet.")

if __name__ == "__main__":
    main()
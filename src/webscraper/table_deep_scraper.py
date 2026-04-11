"""
Tabellen-Deep-Scraper für fussball.de.

Dieses Skript geht direkt in die Staffeltabellen, extrahiert dort die direkten
Links zu den Mannschaftsprofilen und liest auf diesen Profilen die Adressen aus.
Inklusive Anti-Duplikat-Speicher und ohne Deprecation-Warnings.
"""

import requests
from bs4 import BeautifulSoup
import time
import csv
import os
import re

# --- PFAD-RESOLUTION ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
OUTPUT_CSV = os.path.join(DATA_DIR, "hamburg_vereine_addresses_final.csv")

# Deine Liste der Tabellen-URLs
URLS = [
    "https://www.fussball.de/spieltagsuebersicht/kk-01-kreisebene-hamburg-kreisklasse-herren-saison2526-hamburg/-/staffel/02TESB8NIG00000EVS5489BTVTLPPK10-G#!/section/table/",
    "https://www.fussball.de/spieltagsuebersicht/kk-02-kreisebene-hamburg-kreisklasse-herren-saison2526-hamburg/-/staffel/02TESB8NP0000003VS5489BTVTLPPK10-G#!/section/table/",
    "https://www.fussball.de/spieltagsuebersicht/kk-03-kreisebene-hamburg-kreisklasse-herren-saison2526-hamburg/-/staffel/02TESB8NV000000EVS5489BTVTLPPK10-G#!/section/table/",
    "https://www.fussball.de/spieltagsuebersicht/kk-04-kreisebene-hamburg-kreisklasse-herren-saison2526-hamburg/-/staffel/02TESB8O5G00000AVS5489BTVTLPPK10-G#!/section/table/",
    "https://www.fussball.de/spieltagsuebersicht/kk-05-kreisebene-hamburg-kreisklasse-herren-saison2526-hamburg/-/staffel/02TESB8OBS00000EVS5489BTVTLPPK10-G#!/section/table/",
    "https://www.fussball.de/spieltagsuebersicht/kk-06-kreisebene-hamburg-kreisklasse-herren-saison2526-hamburg/-/staffel/02TESB8OHS00000EVS5489BTVTLPPK10-G#!/section/table/",
    "https://www.fussball.de/spieltagsuebersicht/kk-07-kreisebene-hamburg-kreisklasse-herren-saison2526-hamburg/-/staffel/02TESB8ONS00000EVS5489BTVTLPPK10-G#!/section/table/",
    "https://www.fussball.de/spieltagsuebersicht/kk-08-kreisebene-hamburg-kreisklasse-herren-saison2526-hamburg/-/staffel/02TESB8OTO00000EVS5489BTVTLPPK10-G#!/section/table/",
    "https://www.fussball.de/spieltagsuebersicht/kk-09-kreisebene-hamburg-kreisklasse-herren-saison2526-hamburg/-/staffel/02TLKR3K44000004VS5489BUVUPJS9JR-G#!/section/table/",
    "https://www.fussball.de/spieltagsuebersicht/kk-10-kreisebene-hamburg-kreisklasse-herren-saison2526-hamburg/-/staffel/02TLKU14TK000003VS5489BUVUPJS9JR-G#!/section/table/",
    "https://www.fussball.de/spieltagsuebersicht/kk-11-kreisebene-hamburg-kreisklasse-herren-saison2526-hamburg/-/staffel/02TLKUAA3K000004VS5489BUVUPJS9JR-G#!/section/table/",
    "https://www.fussball.de/spieltagsuebersicht/kk-12-kreisebene-hamburg-kreisklasse-herren-saison2526-hamburg/-/staffel/02TLKUEF10000004VS5489BUVUPJS9JR-G#!/section/table/",
    "https://www.fussball.de/spieltagsuebersicht/kl-01-kreisebene-hamburg-kreisliga-herren-saison2526-hamburg/-/staffel/02TESB4EBK00000CVS5489BTVTLPPK10-G#!/section/table/",
    "https://www.fussball.de/spieltagsuebersicht/kl-02-kreisebene-hamburg-kreisliga-herren-saison2526-hamburg/-/staffel/02TESB4EIO00000EVS5489BTVTLPPK10-G#!/section/table/",
    "https://www.fussball.de/spieltagsuebersicht/kl-03-kreisebene-hamburg-kreisliga-herren-saison2526-hamburg/-/staffel/02TESB4EPG00000DVS5489BTVTLPPK10-G#!/section/table/",
    "https://www.fussball.de/spieltagsuebersicht/kl-04-kreisebene-hamburg-kreisliga-herren-saison2526-hamburg/-/staffel/02TESB4EV400000EVS5489BTVTLPPK10-G#!/section/table/",
    "https://www.fussball.de/spieltagsuebersicht/kl-05-kreisebene-hamburg-kreisliga-herren-saison2526-hamburg/-/staffel/02TESB4F4S00000EVS5489BTVTLPPK10-G#!/section/table/",
    "https://www.fussball.de/spieltagsuebersicht/kl-06-kreisebene-hamburg-kreisliga-herren-saison2526-hamburg/-/staffel/02TESB4FB800000EVS5489BTVTLPPK10-G#!/section/table/",
    "https://www.fussball.de/spieltagsuebersicht/kl-07-kreisebene-hamburg-kreisliga-herren-saison2526-hamburg/-/staffel/02TESB4FGO00000EVS5489BTVTLPPK10-G#!/section/table/",
    "https://www.fussball.de/spieltagsuebersicht/kl-08-kreisebene-hamburg-kreisliga-herren-saison2526-hamburg/-/staffel/02TESB4FMK00000EVS5489BTVTLPPK10-G#!/section/table/"
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7'
}

def extract_address_from_profile(session, profile_url: str) -> str:
    """Lädt das Mannschaftsprofil und sucht nach PLZ + Ort."""
    try:
        if profile_url.startswith('//'):
            profile_url = "https:" + profile_url
        elif profile_url.startswith('/'):
            profile_url = "https://www.fussball.de" + profile_url

        res = session.get(profile_url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.content, 'html.parser')

        regex_pattern = re.compile(r'\d{5}\s+[A-Za-zäöüß]+')

        # WICHTIG: 'string=' statt 'text=' behebt die Deprecation Warning!
        address_blocks = soup.find_all(string=regex_pattern)

        for block in address_blocks:
            if block and block.parent and block.parent.parent:
                parent_text = block.parent.parent.get_text(separator=', ', strip=True)
                if re.search(r'\d{5}', parent_text):
                    clean_address = re.sub(r'\s+', ' ', parent_text).replace(' ,', ',')
                    return clean_address

        return "NICHT GEFUNDEN (Keine Adresse auf Profilseite)"
    except Exception as e:
        return f"FEHLER beim Profilaufruf"


def main():
    print("=== fussball.de Direkter Tabellen-Scraper ===")
    session = requests.Session()

    # Gedächtnis für bereits gefundene Mannschaften
    seen_teams = set()

    with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8-sig') as out_file:
        writer = csv.writer(out_file, delimiter=';')
        writer.writerow(["Staffel", "Mannschaft", "Adresse"])

        for url in URLS:
            staffel_name = url.split('/')[4].split('-')[0:2]
            staffel_label = "-".join(staffel_name).upper()

            print(f"\n--- Lade Staffel {staffel_label} ---")

            try:
                response = session.get(url, headers=HEADERS, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')

                club_divs = soup.find_all('div', class_='club-name')

                for div in club_divs:
                    team_name = div.get_text().strip()
                    if not team_name:
                        continue

                    # Überspringen, wenn wir diese Mannschaft schon haben!
                    if team_name in seen_teams:
                        continue

                    # Zum Gedächtnis hinzufügen
                    seen_teams.add(team_name)

                    link_tag = div.find('a')
                    if not link_tag:
                        link_tag = div.find_parent('a')
                    if not link_tag:
                        parent_td = div.find_parent('td')
                        if parent_td:
                            link_tag = parent_td.find('a')

                    if link_tag and link_tag.has_attr('href'):
                        profile_url = link_tag['href']
                        print(f"Suche: {team_name}... ", end="", flush=True)

                        time.sleep(2.5)
                        adresse = extract_address_from_profile(session, profile_url)

                        if "NICHT GEFUNDEN" in adresse or "FEHLER" in adresse:
                            print(adresse)
                        else:
                            print("GEFUNDEN!")

                        writer.writerow([staffel_label, team_name, adresse])
                    else:
                        print(f"Suche: {team_name}... KEIN PROFLLINK IN TABELLE")
                        writer.writerow([staffel_label, team_name, "NICHT GEFUNDEN (Kein Profillink)"])

            except Exception as e:
                print(f"Fehler beim Laden der Tabelle {staffel_label}: {e}")

    print(f"\nFertig! Die exakten Adressen wurden gespeichert unter:\n{OUTPUT_CSV}")

if __name__ == "__main__":
    main()
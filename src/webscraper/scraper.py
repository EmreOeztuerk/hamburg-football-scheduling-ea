import requests
from bs4 import BeautifulSoup
import time
import csv
import os

# Liste der URLs
urls = [
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

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Ordner erstellen
output_dir = "data"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

csv_path = os.path.join(output_dir, "hamburg_vereine_raw.csv")


def scrape_staffel(url):
    # Extrahiert den Namen der Staffel aus der URL für die CSV-Spalte
    staffel_name = url.split('/')[4].split('-')[0:2]
    staffel_label = "-".join(staffel_name).upper()  # z.B. KK-01

    print(f"Scrape: {staffel_label}...")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        club_divs = soup.find_all('div', class_='club-name')
        teams = [div.get_text().strip() for div in club_divs if div.get_text().strip()]
        return staffel_label, teams
    except Exception as e:
        print(f"Fehler bei {url}: {e}")
        return staffel_label, []


# Datei schreiben mit UTF-8-SIG für korrekte Umlaute in Excel
try:
    with open(csv_path, mode='w', newline='', encoding='utf-8-sig') as file:
        # Delimiter auf Semikolon für deutsches Excel
        writer = csv.writer(file, delimiter=';')
        writer.writerow(["Staffel", "Vereinsname"])

        for url in urls:
            label, teams = scrape_staffel(url)
            for team in teams:
                writer.writerow([label, team])

            print(f"-> {len(teams)} Vereine in {label} gefunden.")
            time.sleep(1)  # Kurze Pause gegen Sperren

except PermissionError:
    print("FEHLER: Die Datei ist noch in Excel geöffnet! Bitte schließen und erneut versuchen.")

print(f"\nFertig! Die Datei mit korrekten Umlauten liegt hier: {csv_path}")
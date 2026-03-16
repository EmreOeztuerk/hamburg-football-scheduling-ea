import os
import time
import re
import pandas as pd
import undetected_chromedriver as uc
from bs4 import BeautifulSoup


class HFVScraper:
    def __init__(self):
        options = uc.ChromeOptions()
        # undetected_chromedriver hilft gegen Bot-Sperren
        self.driver = uc.Chrome(options=options)
        self.driver.maximize_window()

    def clean_club_name(self, raw_name):
        """
        Extrahiert den Stammverein.
        Beispiel: 'SV Barmbek 2.' -> 'SV Barmbek'
        """
        # Entfernt Zusätze wie 1., 2., I, II, III am Ende des Namens
        # Nutzt Regex, um Zahlen oder römische Ziffern am Ende zu finden
        clean = re.sub(r'\s+(\d+\.|[IVX]+)$', '', raw_name.strip())
        return clean

    def get_staffel_data(self, url_list):
        all_results = []

        for url in url_list:
            print(f"\nLade Staffel-Übersicht: {url}")
            try:
                self.driver.get(url)
                # Zeit für manuelles Cookie-Klicken (nur beim ersten Mal nötig)
                time.sleep(8)

                soup = BeautifulSoup(self.driver.page_source, 'html.parser')

                # Suche gezielt nach den Tabellenzellen der Mannschaften
                cells = soup.find_all('td', class_='cl-table-teams')

                staffel_teams = []
                for cell in cells:
                    name = cell.get_text(strip=True)
                    if name and name not in staffel_teams:
                        staffel_teams.append(name)

                print(f"Gefundene Teams in dieser Staffel: {len(staffel_teams)}")

                for team in staffel_teams:
                    all_results.append({
                        "staffel_url": url,
                        "mannschaft_name": team,
                        "stammverein": self.clean_club_name(team)
                    })
            except Exception as e:
                print(f"Fehler beim Laden von {url}: {e}")

        return all_results

    def close(self):
        self.driver.quit()


if __name__ == "__main__":
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
        "https://www.fussball.de/spieltagsuebersicht/kk-12-kreisebene-hamburg-kreisklasse-herren-saison2526-hamburg/-/staffel/02TLKUEF10000004VS5489BUVUPJS9JR-G#!/section/table/"
    ]

    scraper = HFVScraper()
    try:
        results = scraper.get_staffel_data(urls)

        if results:
            df = pd.DataFrame(results)
            # Speichern im Daten-Ordner
            df.to_csv("teams_basis_geputzt.csv", index=False, encoding='utf-8-sig')
            print(f"\nErfolg: {len(df)} Mannschaften gespeichert.")
            print(df.head(10))  # Zeige die ersten 10 zur Kontrolle
    finally:
        scraper.close()
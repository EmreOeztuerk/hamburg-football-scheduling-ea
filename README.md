# Evolutionäre Optimierung der Sportstättenplanung (Hamburg) ⚽️🤖

Dieses Repository enthält den Prototyp für meine Bachelorarbeit am Department Informatik der HAW Hamburg unter der Betreuung von Prof. Dr.-Ing. Christian Lins.

Das System nutzt Evolutionäre Algorithmen (EA), um hochkomplexe Ressourcenkonflikte bei der Spielzeitplanung auf Hamburger Sportanlagen automatisiert und fair zu lösen.

# 📋 Problemstellung
In Hamburg teilen sich oft bis zu 20 Mannschaften eine einzige Sportanlage. Während der Hamburger Fußball-Verband (HFV) die regionalen Staffeln festlegt, obliegt die konkrete Zeit- und Platzverteilung den Vereinen. Manuelle Planungen führen oft zu:

- Ressourcenkonflikten: Unzulässige Doppelbelegungen von Plätzen.

- Logistikproblemen: Ineffiziente Verteilung von Kabinen und Schiedsrichtern.

- Unfairness: Bevorzugung oder Benachteiligung bestimmter Teams bei attraktiven Anstoßzeiten.

# 🚀 Lösungsansatz
Dieses Projekt implementiert eine End-to-End-Pipeline:

1. Data Acquisition: Automatisierter Web-Scraper für fussball.de mittels Selenium.

2. Preprocessing: Geocoding von Adressdaten (Nominatim API) zur Distanzberechnung.

3. Optimization: Ein evolutionärer Algorithmus zur Lösung des Resource-Constrained Project Scheduling Problems (RCPSP).

4. Evaluation: Vergleich der generierten Pläne mit manuellen Referenzplänen hinsichtlich Konfliktfreiheit und Zeitwünschen.

# 🛠 Tech Stack
- Language: Python 3.12

- Scraping: BeautifulSoup

- Geodata: OpenStreetMap/Nominatim

- Data Handling: Pandas, NumPy

# 📖 Wissenschaftlicher Hintergrund
Die theoretische Basis bildet die Modellierung von Harten Constraints (z. B. Platzbelegung) und Weichen Constraints (z. B. bevorzugte Anstoßzeiten) innerhalb einer Fitnessfunktion. Das Ziel ist es, durch evolutionäre Operatoren (Mutation/Selektion) eine valide und optimierte Lösung im NP-schweren Suchraum zu finden.

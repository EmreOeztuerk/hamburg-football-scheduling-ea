# Evolutionäre Optimierung der Staffeleinteilung im Hamburger Amateurfußball

Dieses Repository enthält den Prototyp und die Evaluationsskripte für die Bachelorarbeit von **Emre Öztürk** am Department Informatik der HAW Hamburg unter der Betreuung von Prof. Dr.-Ing. Christian Lins und Prof. Dr. Olaf Zukunft.

Das System nutzt einen **Genetischen Algorithmus (GA)**, um das regionale Partitionierungsproblem (*Capacitated Clustering Problem*, CCP) bei der Staffeleinteilung im Hamburger Amateurfußball automatisiert zu lösen. Ziel ist es, die kumulierten Fahrtstrecken für Auswärtsfahrten zu minimieren und somit den $\text{CO}_2\text{e}$-Fußabdruck des Amateursports nachhaltig zu reduzieren.

---

##  Problemstellung

Die traditionelle manuelle Staffeleinteilung durch Sportverbände basiert primär auf organisatorischer Erfahrung und führt häufig zu geografisch ineffizienten Konstellationen:
* **Hohe Fahrstrecken:** Teams müssen für Auswärtsspiele unnötig weite Strecken durch das Hamburger Stadtgebiet und das Umland zurücklegen.
* **Erhöhter $\text{CO}_2\text{e}$-Ausstoß:** Vermeidbare Fahrzeugkilometer belasten die Umwelt sowie die Vereinskassen.
* **Vereinsinterne Duelle:** Ohne gezielte Restriktionsprüfung treffen zweite und dritte Mannschaften desselben Vereins in derselben Staffel aufeinander.

---

##  Lösungsansatz & Systemarchitektur

Das entwickelte *Decision Support System* (DSS) implementiert eine vollständig automatisierte Daten- und Optimierungs-Pipeline:

1. **Data Acquisition:** Automatisierter Web-Scraper für `fussball.de` (via BeautifulSoup) zur Erfassung der HFV-Ist-Baseline (Kreisklasse & Kreisliga, 280 Mannschaften der Spielzeit 2025/2026).
2. **Geocoding & Routing:**
   * Geokodierung der Spielstätten-Adressen über die **Nominatim API** (OpenStreetMap).
   * Berechnung einer exakten straßenbasierten Distanzmatrix über die **Open Source Routing Machine (OSRM)**.
3. **Evolutionäre Optimierung:**
   * Lösung des *Capacitated Clustering Problems* (CCP) mittels Genetischem Algorithmus.
   * **Permutationsbasierte Kodierung:** Garantiert die strukturelle Einhaltung der Staffelkapazitäten.
   * **Penalty-Mechanismus:** Dynamisches Strafgewicht ($W = 50000\text{ km}$) zur verlässlichen Vermeidung vereinsinterner Duelle.
4. **Evaluation & Ökologische Bilanzierung:**
   * Benchmark zwischen der Ist-Baseline und zwei Optimierungsszenarien (Szenario A: Kapazitäts-Erhalt; Szenario B: Ausgeglichene Staffelgrößen).
   * Quantifizierung der Distanzgewinne und Umrechnung in $\text{CO}_2\text{e}$-Minderungen (UBA-Emissionsfaktor).

---

##  Tech Stack

* **Programmiersprache:** Python 3.12
* **Web Scraping:** BeautifulSoup4, Requests
* **Geodaten & Routing:** OpenStreetMap (Nominatim API), OSRM (Open Source Routing Machine)
* **Data Handling & Pipeline:** Pandas, NumPy
* **Analyse & Visualisierung:** Matplotlib, Seaborn

---

##  Zentrale Ergebnisse

| Szenario | Gesamtfahrtstrecke (km) | Einsparung vs. Baseline | $\text{CO}_2\text{e}$-Reduktion (Saison) |
| :--- | :---: | :---: | :---: |
| **Ist-Baseline (HFV)** | 39.768,93 km | — | — |
| **Szenario A (Struktur-Erhalt)** | **37.860,02 km** | **-4,80 %** (-1.908,91 km) | **-1.756 kg $\text{CO}_2\text{e}$** (-1,76 t) |
| **Szenario B (Kapa-Ausgleich)** | **40.264,90 km** | **-9,12 %** (ø km/Fahrt)* | *(10,46 km vs. 11,51 km/Sp.)* |

---

##  Wissenschaftlicher Hintergrund

Das Zuordnungsproblem wird als **Capacitated Clustering Problem (CCP)** modelliert. Die Fitnessfunktion minimiert die Summe aller Hin- und Rückfahrtdistanzen der Auswärtsfahrten unter Berücksichtigung von harten Kapazitätsvorgaben und weichen Nebenbedingungen. Der Algorithmus kombiniert Elitismus ($5\,\%$), Crossover-Operatoren sowie gezielte Mutationen (Swap-Mutation), um im NP-schweren Lösungsraum hochwertige Näherungsoptima zu finden.

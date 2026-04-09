# Entities

Diese Seite listet die von der Integration angelegten Entities.

## Globale Entities

| Typ   | Entity-Name | Standard aktiv | Beschreibung |
|-------|-------------|----------------|--------------|
| Sensor | Gesamt-Einspeiseleistung | Ja | Gesamte zugewiesene Entladeleistung aller Batterien (W). |
| Sensor | Ziel-Gesamtleistung | Ja | Ziel-Entladeleistung nach Anwendung des Gesamtlimits (W). |
| Sensor | Durchschnittlicher SoC | Ja | Kapazitätsgewichteter Durchschnitts-SoC der gültigen Batterien (%). |
| Sensor | Lastleistung | Nein | Aktuelle Last aus Sicht der Integration (W). |
| Sensor | Summe Maximalleistung | Nein | Summe aller Batterie-Limits (W). |
| Sensor | Effektive Ziel-Leistung | Nein | Ziel nach Anwendung der Summenbegrenzung (W). |
| Bild | Sigmoid-Kurve | Nein | Visualisierung der aktuellen Sigmoid-Kurve basierend auf Ø-SoC und den Reglern. |
| Zahl | Maximale Gesamtleistung | Ja | Maximale Gesamt-Entladeleistung (W). |
| Zahl | Maximale Leistung je Batterie | Ja | Standardlimit pro Batterie (W). |
| Zahl | Sigmoid-Steigung | Ja | Wie stark hohe SoC bevorzugt werden. |
| Zahl | Sigmoid-Mittenoffset | Ja | Verschiebt den SoC-Gleichgewichtspunkt (%). |
| Zahl | Prioritätsschwelle hoher SoC | Ja | Batterien ab dieser SoC werden zuerst genutzt (%). |

## Batterie-Entities

| Typ   | Entity-Name | Standard aktiv | Beschreibung |
|-------|-------------|----------------|--------------|
| Sensor | Einspeiseleistung | Ja | Zugeteilte Entladeleistung der Batterie (W). |
| Sensor | Anteil | Ja | Anteil der Batterie an der Gesamteinspeisung (%). |
| Sensor | Kapazität (berechnet) | Nein | Umgerechnete Batteriekapazität in Wh. |
| Sensor | Min-SoC-Schwelle (berechnet) | Nein | Mindest-SoC-Schwelle für die Freigabe (%). |
| Sensor | Rohgewicht | Nein | Gewichtung vor der Limitierung. |
| Schalter | Batterie aktiviert | Ja | Schalter zum Ein- oder Ausschliessen der Batterie. |
| Zahl | Leistungsgrenze | Nein | Optionales Batterie-Limit (W). In der Entity Registry aktivieren; mit 0 deaktivieren. |

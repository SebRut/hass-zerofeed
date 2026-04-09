# Entities

Diese Seite listet die von der Integration angelegten Entities.

## Globale Entities

| Typ   | Entity-Name | Standard aktiv | Beschreibung |
|-------|-------------|----------------|--------------|
| Sensor | Gesamt-Einspeiseleistung | Ja | Gesamte zugewiesene Entladeleistung aller Batterien (W). |
| Sensor | Ziel-Gesamtleistung | Ja | Ziel-Entladeleistung nach Anwendung des Gesamtlimits (W). |
| Sensor | Durchschnittlicher SoC | Ja | Kapazitaetsgewichteter Durchschnitts-SoC der gueltigen Batterien (%). |
| Zahl | Maximale Gesamtleistung | Ja | Maximale Gesamt-Entladeleistung (W). |
| Zahl | Maximale Leistung je Batterie | Ja | Standardlimit pro Batterie (W). |
| Zahl | Sigmoid-Steigung | Ja | Wie stark hohe SoC bevorzugt werden. |
| Zahl | Sigmoid-Mittenoffset | Ja | Verschiebt den SoC-Gleichgewichtspunkt (%). |
| Zahl | Prioritaetsschwelle hoher SoC | Ja | Batterien ab dieser SoC werden zuerst genutzt (%). |

## Batterie-Entities

| Typ   | Entity-Name | Standard aktiv | Beschreibung |
|-------|-------------|----------------|--------------|
| Sensor | Einspeiseleistung | Ja | Zugeteilte Entladeleistung der Batterie (W). |
| Sensor | Anteil | Ja | Anteil der Batterie an der Gesamteinspeisung (%). |
| Zahl | Leistungsgrenze | Nein | Optionales Batterie-Limit (W). In der Entity Registry aktivieren; mit 0 deaktivieren. |

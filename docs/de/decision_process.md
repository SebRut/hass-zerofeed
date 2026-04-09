# Wie ZeroFeed die Ziel-Last bestimmt

## Zielverhalten

- Aktuelle Hauslast möglichst durch Batterie-Entladung abdecken.
- Gesamt- und Batterie-Limits einhalten.
- Höhere SoC zuerst nutzen, damit volle Batterien mehr beitragen.
- Optional nur die sehr vollen Batterien priorisieren (High-SoC-Priorität).

## Was du konfigurierst

Eingaben
- Systemlast-Leistungssensor (W oder kW).
- Batterie-SoC-Sensor (%).
- Batterie-Kapazitätssensor (Wh oder kWh).
- Optionale Batterie-Min-SoC-Schwelle (%).

Regler in der UI
- Maximale Gesamtleistung: maximale Gesamt-Entladeleistung.
- Maximale Leistung je Batterie: maximale Leistung pro Batterie.
- Sigmoid-Steigung: wie stark hohe SoC bevorzugt werden (höher = stärker).
- Sigmoid-Mittenoffset: verschiebt den SoC-Gleichgewichtspunkt.
- Prioritätsschwelle hoher SoC: Batterien ab dieser SoC werden zuerst genutzt.

## So entscheidet das System (einfach erklärt)

1. Aktuelle Last lesen und durch das Gesamtlimit begrenzen. Das ist die Ziel-Entladeleistung.
2. Pro Batterie prüfen: SoC und Kapazität müssen gültig sein. Wenn eine Min-SoC-Schwelle gesetzt ist und die Batterie darunter liegt, wird sie übersprungen.
3. Höhere SoC werden bevorzugt, über eine weiche [Sigmoid-Kurve](https://de.wikipedia.org/wiki/Sigmoidfunktion).
4. Die Ziel-Last wird auf die Batterien verteilt, ohne die maximale Leistung pro Batterie zu überschreiten.
5. Wenn die Prioritätsschwelle hoher SoC gesetzt ist und Batterien darüber liegen:
   - Zuerst nur diese High-SoC-Batterien nutzen.
   - Falls die Ziel-Last nicht erreicht wird, den Rest auf andere Batterien verteilen.

## Häufige Fragen

Wie mache ich den Anstieg gleichmäßiger?
- Sigmoid-Steigung reduzieren, dann steigt die Bevorzugung langsamer an.

Ich will, dass volle Batterien mehr leisten.
- Sigmoid-Steigung erhöhen oder Prioritätsschwelle hoher SoC setzen (z. B. 90%).

Was bedeutet "Gleichgewichtspunkt"?
- Das ist der SoC, ab dem eine Batterie als neutral bewertet wird. Ein positiver Offset bevorzugt höhere SoC, ein negativer Offset nutzt niedrigere SoC früher.

Ich will eine gleichmäßigere Verteilung.
- Sigmoid-Steigung senken und einen negativen Sigmoid-Mittenoffset prüfen.

Ich will zuerst nur sehr volle Batterien entladen.
- Prioritätsschwelle hoher SoC setzen (z. B. 90%). Andere werden nur genutzt, wenn das Ziel sonst nicht erreicht wird.

Warum entlädt eine Batterie gar nicht?
- Min-SoC-Schwelle und aktuellen SoC prüfen. Auf oder unter der Schwelle wird sie übersprungen.

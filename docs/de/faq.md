# FAQ

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

Wie begrenze ich eine Batterie stärker als die anderen?
- In der Entity Registry die "Leistungsgrenze" der Batterie aktivieren und einen Wert in W setzen. Mit 0 wird die Begrenzung deaktiviert.

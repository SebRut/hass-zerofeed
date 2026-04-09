# How ZeroFeed decides target load

## What it tries to do

- Match your current house load with battery discharge.
- Respect total and per-battery limits.
- Prefer higher SoC batteries, so fuller batteries do more of the work.
- Optionally prioritize only the very full batteries first (high SoC priority).

## What you configure

Inputs
- System load power sensor (W or kW).
- Per-battery SoC sensor (%).
- Per-battery capacity sensor (Wh or kWh).
- Optional per-battery minimum SoC threshold (%).

Tuning knobs in the UI
- Total max power: total discharge cap for all batteries combined.
- Per-battery max power: cap for each battery.
- Sigmoid steepness: how strongly fuller batteries are preferred (higher = stronger).
- Sigmoid center offset: shifts the "balance point" up or down.
- High SoC priority threshold: if set, batteries at/above this SoC are used first.
- Max power override (battery-specific, optional): lower cap for a specific battery if enabled.

Per-battery toggle
- Battery enabled: include or exclude a battery from allocation.

## How it decides

1. Read your current load and cap it at the total max power. This becomes the target discharge power.
2. For each battery, check if SoC and capacity are valid. If a min SoC is set and the battery is at or below it, that battery is skipped.
3. Prefer higher SoC batteries using a smooth curve ([sigmoid](https://en.wikipedia.org/wiki/Sigmoid_function)).
4. Distribute the target across batteries, never exceeding the per-battery max power for any battery.
5. If the High SoC priority threshold is set and any batteries are above it:
   - Allocate only among those high-SoC batteries first.
   - If they cannot cover the target, the remaining power spills over to the other batteries.

# Entities

This page lists the entities created by the integration.

## Global entities

| Type   | Entity name | Default enabled | Description |
|--------|-------------|-----------------|-------------|
| Sensor | Total feed-in power | Yes | Total allocated discharge power across all batteries (W). |
| Sensor | Target total power | Yes | Target discharge power after the total max power cap (W). |
| Sensor | Average SoC | Yes | Capacity-weighted average SoC across valid batteries (%). |
| Sensor | Load power | No | Current load as seen by the integration (W). |
| Sensor | Sum max power | No | Sum of all per-battery caps (W). |
| Sensor | Effective target power | No | Target after applying the sum of caps (W). |
| Image | Sigmoid curve | No | Visualizes the current sigmoid curve based on avg SoC and the tuning controls. |
| Number | Total max power | Yes | Total discharge cap for all batteries combined (W). |
| Number | Per-battery max power | Yes | Default per-battery cap (W). |
| Number | Sigmoid steepness | Yes | How strongly higher SoC is preferred. |
| Number | Sigmoid center offset | Yes | Shifts the SoC balance point up or down (%). |
| Number | High SoC priority threshold | Yes | If set, batteries at/above this SoC are used first (%). |

## Per-battery entities

| Type   | Entity name | Default enabled | Description |
|--------|-------------|-----------------|-------------|
| Sensor | Feed-in power | Yes | Allocated discharge power for the battery (W). |
| Sensor | Share | Yes | Battery share of total feed-in (%). |
| Sensor | Capacity (computed) | No | Converted battery capacity in Wh. |
| Sensor | Min SoC threshold (computed) | No | Minimum SoC threshold used for eligibility (%). |
| Sensor | Raw weight | No | Weight used for allocation before caps. |
| Switch | Battery enabled | Yes | Toggle to include or exclude the battery from allocations. |
| Number | Max power override | No | Optional per-battery cap (W). Enable in the Entity Registry; set to 0 to disable. |

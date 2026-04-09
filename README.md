# hass-zerofeed

Home Assistant custom integration that allocates an expected battery feed-in (discharge power) across multiple batteries to cover a target power (usually your current load).

Disclaimer
- This repository (integration code and documentation) is mostly AI-generated and should be reviewed carefully before you rely on it for anything safety- or cost-critical.

What it does
- You configure a `system load` power sensor and, per battery, a `SoC` sensor (%) and a `capacity` sensor (Wh/kWh).
- Optional per-battery inputs:
  - `min SoC threshold` entity (%): if the battery SoC is at/below this value, it is treated as unable to discharge (0 W)
- The integration computes a total target feed-in (clamped by min/max) and splits it across batteries:
  - base weight: relative capacity
  - modifier: sigmoid around the (capacity-weighted) average SoC, so batteries above average contribute more
- It exposes the expected feed-in per battery (W) as sensors and exposes tunables as `number` entities.

Quick test (Docker)
1. `docker compose up`
2. Open Home Assistant at `http://localhost:8123`
3. Use the included demo entities (`input_number.*` + `sensor.*`) and add the `ZeroFeed` integration via Settings -> Devices & services -> Add integration.

Files of interest
- Integration code: `custom_components/zerofeed/`
- Demo HA config for Docker: `config/configuration.yaml`
- Docker: `compose.yaml`
- Docs (EN): `docs/decision_process.md`
- Docs (DE): `docs/de/decision_process.md`

Notes
- This integration only *calculates* expected allocations; it does not control inverters.
- Units:
  - load: W or kW
  - SoC: %
  - capacity: Wh or kWh (used for weighting)

Controls (numbers)
- Total max power (W)
- Per-battery max power (shared across all batteries) (W)
- Sigmoid steepness + center offset

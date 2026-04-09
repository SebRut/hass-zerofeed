# AGENTS.md

Project: Home Assistant custom integration `zerofeed`.

Purpose
- Compute per-battery discharge allocations to cover load without exceeding limits.
- Expose sensors and number controls for runtime tuning.

Key paths
- Integration code: `custom_components/zerofeed/`
- Config/Options flow: `custom_components/zerofeed/config_flow.py`
- Coordinator logic (allocation): `custom_components/zerofeed/coordinator.py`
- Sensors: `custom_components/zerofeed/sensor.py`
- Number controls: `custom_components/zerofeed/number.py`
- Constants: `custom_components/zerofeed/const.py`
- Translations: `custom_components/zerofeed/strings.json`, `custom_components/zerofeed/translations/*.json`

Runtime controls (Number entities)
- total_max_w: cap for total discharge power.
- per_battery_max_w: per-battery cap.
- sigmoid_k: weight steepness for SoC-based allocation.
- sigmoid_center_offset: SoC offset applied to average SoC center.
- high_soc_threshold: if >0, batteries at/above threshold are prioritized first.

Allocation summary
- Valid batteries require numeric SoC/capacity and optional min SoC threshold.
- Compute sigmoid weights based on SoC vs average + offset.
- Allocate power with caps; if high_soc_threshold > 0, prioritize those batteries, then spill over.

Editing notes
- Use ASCII when editing files.
- Keep translations in sync for new UI strings.

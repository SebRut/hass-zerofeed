from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import slugify

from .const import (
    CONF_BATTERIES,
    CONF_BATTERY_ID,
    CONF_BATTERY_NAME,
    CONF_CAPACITY_ENTITY,
    CONF_LOAD_ENTITY,
    CONF_MIN_SOC_ENTITY,
    CONF_SOC_ENTITY,
    CTRL_PER_BATTERY_MAX_W,
    CTRL_HIGH_SOC_THRESHOLD,
    CTRL_SIGMOID_CENTER_OFFSET,
    CTRL_SIGMOID_K,
    CTRL_TOTAL_MAX_W,
    DEFAULT_HIGH_SOC_THRESHOLD,
    DEFAULT_PER_BATTERY_MAX_W,
    DEFAULT_SIGMOID_CENTER_OFFSET,
    DEFAULT_SIGMOID_K,
    DEFAULT_TOTAL_MAX_W,
    DOMAIN,
)
from .helpers import clamp, energy_to_wh, power_to_w, read_numeric_state, sigmoid

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class BatteryConfig:
    battery_id: str
    name: str
    soc_entity: str
    capacity_entity: str
    min_soc_entity: str | None


def _unique_battery_id(existing: set[str], name: str) -> str:
    base = slugify(name) or "battery"
    candidate = base
    i = 2
    while candidate in existing:
        candidate = f"{base}_{i}"
        i += 1
    existing.add(candidate)
    return candidate


class ZerofeedCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=10),
        )
        self.entry = entry

        # Allow options flow to override initial config without recreating the entry.
        self.load_entity: str = entry.options.get(CONF_LOAD_ENTITY, entry.data[CONF_LOAD_ENTITY])
        self._batteries_raw: list[dict] = entry.options.get(CONF_BATTERIES, entry.data.get(CONF_BATTERIES, []))

        # Defaults; number entities will override these at runtime.
        self.controls: dict[str, float] = {
            CTRL_TOTAL_MAX_W: DEFAULT_TOTAL_MAX_W,
            CTRL_PER_BATTERY_MAX_W: DEFAULT_PER_BATTERY_MAX_W,
            CTRL_SIGMOID_K: DEFAULT_SIGMOID_K,
            CTRL_SIGMOID_CENTER_OFFSET: DEFAULT_SIGMOID_CENTER_OFFSET,
            CTRL_HIGH_SOC_THRESHOLD: DEFAULT_HIGH_SOC_THRESHOLD,
        }

        existing: set[str] = set()
        batteries: list[BatteryConfig] = []
        for b in self._batteries_raw:
            if b.get(CONF_BATTERY_ID):
                battery_id = b[CONF_BATTERY_ID]
                existing.add(battery_id)
            else:
                battery_id = _unique_battery_id(existing, b.get(CONF_BATTERY_NAME, "battery"))
            batteries.append(
                BatteryConfig(
                    battery_id=battery_id,
                    name=b.get(CONF_BATTERY_NAME, battery_id),
                    soc_entity=b[CONF_SOC_ENTITY],
                    capacity_entity=b[CONF_CAPACITY_ENTITY],
                    min_soc_entity=b.get(CONF_MIN_SOC_ENTITY),
                )
            )

        self.batteries = batteries

    def set_control_value(self, key: str, value: float) -> None:
        self.controls[key] = float(value)

    def iter_entity_ids(self) -> Iterable[str]:
        yield self.load_entity
        for b in self.batteries:
            yield b.soc_entity
            yield b.capacity_entity
            if b.min_soc_entity:
                yield b.min_soc_entity

    async def _async_update_data(self) -> dict:
        load_entity = self.load_entity
        load_state = read_numeric_state(self.hass, load_entity)
        if load_state.value is None:
            raise UpdateFailed(f"Load entity has no numeric state: {load_entity}")

        load_w = max(0.0, power_to_w(load_state.value, load_state.unit))

        total_max_w = max(0.0, float(self.controls.get(CTRL_TOTAL_MAX_W, DEFAULT_TOTAL_MAX_W)))
        target_total_w = clamp(load_w, 0.0, total_max_w)

        sigmoid_k = float(self.controls.get(CTRL_SIGMOID_K, DEFAULT_SIGMOID_K))
        center_offset = float(self.controls.get(CTRL_SIGMOID_CENTER_OFFSET, DEFAULT_SIGMOID_CENTER_OFFSET))
        high_soc_threshold = clamp(
            float(self.controls.get(CTRL_HIGH_SOC_THRESHOLD, DEFAULT_HIGH_SOC_THRESHOLD)),
            0.0,
            100.0,
        )

        battery_data: dict[str, dict] = {}
        valid: list[tuple[BatteryConfig, float, float]] = []

        for b in self.batteries:
            soc_state = read_numeric_state(self.hass, b.soc_entity)
            cap_state = read_numeric_state(self.hass, b.capacity_entity)
            soc = soc_state.value
            cap = cap_state.value
            min_soc_threshold: float | None = None
            if b.min_soc_entity:
                min_soc_state = read_numeric_state(self.hass, b.min_soc_entity)
                if min_soc_state.value is not None:
                    # Threshold is configured as percent.
                    min_soc_threshold = clamp(float(min_soc_state.value), 0.0, 100.0)

            if soc is None or cap is None:
                battery_data[b.battery_id] = {
                    "name": b.name,
                    "valid": False,
                    "soc": soc,
                    "capacity_wh": None,
                    "min_soc_threshold": min_soc_threshold,
                    "min_soc_entity": b.min_soc_entity,
                    "feedin_w": None,
                    "share": None,
                    "raw_weight": None,
                }
                continue

            soc = clamp(float(soc), 0.0, 100.0)
            cap_wh = energy_to_wh(float(cap), cap_state.unit)
            if cap_wh <= 0:
                battery_data[b.battery_id] = {
                    "name": b.name,
                    "valid": False,
                    "soc": soc,
                    "capacity_wh": cap_wh,
                    "min_soc_threshold": min_soc_threshold,
                    "min_soc_entity": b.min_soc_entity,
                    "feedin_w": None,
                    "share": None,
                    "raw_weight": None,
                }
                continue

            # If a min-SoC entity is configured but not available, fail safe: don't allocate.
            if b.min_soc_entity and min_soc_threshold is None:
                battery_data[b.battery_id] = {
                    "name": b.name,
                    "valid": False,
                    "soc": soc,
                    "capacity_wh": cap_wh,
                    "min_soc_threshold": None,
                    "min_soc_entity": b.min_soc_entity,
                    "feedin_w": None,
                    "share": None,
                    "raw_weight": None,
                }
                continue

            # If SoC is at/below threshold, battery is treated as not able to discharge.
            if min_soc_threshold is not None and soc <= min_soc_threshold + 1e-9:
                battery_data[b.battery_id] = {
                    "name": b.name,
                    "valid": False,
                    "soc": soc,
                    "capacity_wh": cap_wh,
                    "min_soc_threshold": min_soc_threshold,
                    "min_soc_entity": b.min_soc_entity,
                    "feedin_w": 0.0,
                    "share": 0.0,
                    "raw_weight": 0.0,
                }
                continue

            valid.append((b, soc, cap_wh))
            battery_data[b.battery_id] = {
                "name": b.name,
                "valid": True,
                "soc": soc,
                "capacity_wh": cap_wh,
                "min_soc_threshold": min_soc_threshold,
                "min_soc_entity": b.min_soc_entity,
            }

        if not valid:
            # No valid batteries: keep target visible, but allocations are unknown/zero.
            return {
                "load_w": load_w,
                "target_total_w": target_total_w,
                "total_feedin_w": 0.0,
                "avg_soc": None,
                "controls": {
                    "total_max_w": total_max_w,
                    "per_battery_max_w": float(self.controls.get(CTRL_PER_BATTERY_MAX_W, DEFAULT_PER_BATTERY_MAX_W)),
                    "sigmoid_k": sigmoid_k,
                    "sigmoid_center_offset": center_offset,
                    "high_soc_threshold": high_soc_threshold,
                },
                "batteries": battery_data,
            }

        total_capacity = sum(cap_wh for _, _, cap_wh in valid)
        avg_soc = sum(soc * cap_wh for _, soc, cap_wh in valid) / total_capacity

        raw_weights: dict[str, float] = {}
        for b, soc, cap_wh in valid:
            # Center around the average SoC (plus optional user offset).
            x = sigmoid_k * (soc - (avg_soc + center_offset))
            raw = cap_wh * sigmoid(x)
            raw_weights[b.battery_id] = max(0.0, raw)

        # Allocation constraints.
        per_batt_max: dict[str, float] = {}
        per_battery_max_w = max(0.0, float(self.controls.get(CTRL_PER_BATTERY_MAX_W, DEFAULT_PER_BATTERY_MAX_W)))
        for b, _, _ in valid:
            per_batt_max[b.battery_id] = per_battery_max_w

        sum_max = sum(per_batt_max.values())
        effective_target = min(target_total_w, sum_max)

        allocations: dict[str, float] = {b.battery_id: 0.0 for b, _, _ in valid}

        headroom = {bid: per_batt_max[bid] for bid in allocations}
        if high_soc_threshold > 0.0:
            priority_ids = {
                b.battery_id for b, soc, _ in valid if soc >= high_soc_threshold
            }
        else:
            priority_ids = set()

        if priority_ids:
            priority_caps = {
                bid: headroom[bid] if bid in priority_ids else 0.0 for bid in allocations
            }
            _distribute_with_caps(allocations, effective_target, raw_weights, priority_caps)
            remaining = effective_target - sum(allocations.values())
            if remaining > 1e-6:
                spillover_caps = {
                    bid: max(0.0, headroom[bid] - allocations[bid])
                    if bid not in priority_ids
                    else 0.0
                    for bid in allocations
                }
                _distribute_with_caps(allocations, remaining, raw_weights, spillover_caps)
        else:
            _distribute_with_caps(allocations, effective_target, raw_weights, headroom)

        total_feedin = sum(allocations.values())
        if total_feedin > 0:
            shares = {bid: allocations[bid] / total_feedin for bid in allocations}
        else:
            shares = {bid: 0.0 for bid in allocations}

        for bid, alloc in allocations.items():
            # Keep computation precision in coordinator data; entities can round for display.
            battery_data[bid]["feedin_w"] = float(alloc)
            battery_data[bid]["share"] = float(shares[bid])
            battery_data[bid]["raw_weight"] = float(raw_weights.get(bid, 0.0))

        return {
            "load_w": load_w,
            "target_total_w": target_total_w,
            "total_feedin_w": float(total_feedin),
            "avg_soc": float(avg_soc),
            "controls": {
                "total_max_w": total_max_w,
                "per_battery_max_w": per_battery_max_w,
                "sigmoid_k": sigmoid_k,
                "sigmoid_center_offset": center_offset,
                "high_soc_threshold": high_soc_threshold,
                "sum_max_w": sum_max,
                "effective_target_w": effective_target,
            },
            "batteries": battery_data,
        }


def _distribute_with_caps(
    allocations: dict[str, float],
    target: float,
    weights: dict[str, float],
    caps: dict[str, float],
) -> None:
    """Distribute `target` across allocations, proportional to weights, capped by `caps`.

    `caps` is the *additional* amount each battery is allowed to receive (headroom).
    """
    if target <= 0:
        return

    remaining = target
    remaining_caps = {bid: max(0.0, cap) for bid, cap in caps.items()}

    for _ in range(len(allocations) + 2):
        free = [bid for bid, cap in remaining_caps.items() if cap > 1e-9]
        if not free or remaining <= 1e-6:
            return

        weight_sum = sum(max(0.0, weights.get(bid, 0.0)) for bid in free)
        if weight_sum <= 0:
            # Fallback to equal distribution if all weights are zero.
            remaining_start = remaining
            per = remaining_start / len(free)
            for bid in free:
                add = min(per, remaining_caps[bid])
                allocations[bid] += add
                remaining_caps[bid] -= add
                remaining -= add
            continue

        remaining_start = remaining
        added_total = 0.0
        for bid in free:
            w = max(0.0, weights.get(bid, 0.0))
            if w <= 0:
                continue
            add = min(remaining_start * (w / weight_sum), remaining_caps[bid])
            allocations[bid] += add
            remaining_caps[bid] -= add
            added_total += add
        remaining -= added_total

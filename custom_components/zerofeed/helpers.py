from __future__ import annotations

import math
from dataclasses import dataclass

from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant


@dataclass(frozen=True)
class NumericState:
    value: float | None
    unit: str | None


def read_numeric_state(hass: HomeAssistant, entity_id: str) -> NumericState:
    """Read an entity state as float + unit; returns value=None if unavailable/non-numeric."""
    state = hass.states.get(entity_id)
    if state is None:
        return NumericState(None, None)

    unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
    try:
        value = float(state.state)
    except (TypeError, ValueError):
        return NumericState(None, unit)

    if math.isnan(value) or math.isinf(value):
        return NumericState(None, unit)
    return NumericState(value, unit)


def power_to_w(value: float, unit: str | None) -> float:
    if unit == "kW":
        return value * 1000.0
    return value


def energy_to_wh(value: float, unit: str | None) -> float:
    if unit == "kWh":
        return value * 1000.0
    return value


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def sigmoid(x: float) -> float:
    # Numerically stable sigmoid.
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


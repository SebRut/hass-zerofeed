from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CTRL_PER_BATTERY_MAX_W,
    CTRL_SIGMOID_CENTER_OFFSET,
    CTRL_SIGMOID_K,
    CTRL_TOTAL_MAX_W,
    DEFAULT_PER_BATTERY_MAX_W,
    DEFAULT_SIGMOID_CENTER_OFFSET,
    DEFAULT_SIGMOID_K,
    DEFAULT_TOTAL_MAX_W,
    DOMAIN,
)
from .coordinator import ZerofeedCoordinator


@dataclass(frozen=True)
class NumberSpec:
    key: str
    translation_key: str
    unit: str | None
    min_value: float
    max_value: float
    step: float
    default: float
    icon: str | None = None
    mode: NumberMode = NumberMode.SLIDER


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ZerofeedCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    specs: list[NumberSpec] = [
        NumberSpec(
            key=CTRL_TOTAL_MAX_W,
            translation_key="total_max_power",
            unit="W",
            min_value=0.0,
            max_value=4000.0,
            step=25.0,
            default=DEFAULT_TOTAL_MAX_W,
            icon="mdi:arrow-collapse-down",
        ),
        NumberSpec(
            key=CTRL_PER_BATTERY_MAX_W,
            translation_key="per_battery_max_power",
            unit="W",
            min_value=0.0,
            max_value=4000.0,
            step=25.0,
            default=DEFAULT_PER_BATTERY_MAX_W,
            icon="mdi:battery-high",
        ),
        NumberSpec(
            key=CTRL_SIGMOID_K,
            translation_key="sigmoid_steepness",
            unit=None,
            min_value=0.0,
            max_value=2.0,
            step=0.01,
            default=DEFAULT_SIGMOID_K,
            icon="mdi:sigma",
            # Steepness is typically tuned by typing specific values; a slider is awkward at 0.01 steps.
            mode=NumberMode.BOX,
        ),
        NumberSpec(
            key=CTRL_SIGMOID_CENTER_OFFSET,
            translation_key="sigmoid_center_offset",
            unit="%",
            min_value=-50.0,
            max_value=50.0,
            step=0.1,
            default=DEFAULT_SIGMOID_CENTER_OFFSET,
            icon="mdi:axis-arrow",
            mode=NumberMode.BOX,
        ),
    ]

    async_add_entities([ZerofeedControlNumber(coordinator, entry, s) for s in specs])


class ZerofeedControlNumber(CoordinatorEntity[ZerofeedCoordinator], RestoreEntity, NumberEntity):
    _attr_should_poll = False

    def __init__(self, coordinator: ZerofeedCoordinator, entry: ConfigEntry, spec: NumberSpec) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self.spec = spec

        self._attr_has_entity_name = True
        self._attr_translation_key = spec.translation_key
        self._attr_unique_id = f"{entry.entry_id}_{spec.key}"
        self._attr_native_unit_of_measurement = spec.unit
        self._attr_native_min_value = spec.min_value
        self._attr_native_max_value = spec.max_value
        self._attr_native_step = spec.step
        self._attr_icon = spec.icon
        self._attr_mode = spec.mode

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="ZeroFeed",
        )

        self._attr_native_value = spec.default

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                self._attr_native_value = float(last.state)
            except (TypeError, ValueError):
                self._attr_native_value = self.spec.default
        else:
            self._attr_native_value = self.spec.default

        self.coordinator.set_control_value(self.spec.key, float(self._attr_native_value))
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_set_native_value(self, value: float) -> None:
        # Keep steepness easy to reason about and stable in the UI (2 decimals).
        if self.spec.key == CTRL_SIGMOID_K:
            value = round(float(value), 2)
        else:
            value = float(value)

        self._attr_native_value = value
        self.coordinator.set_control_value(self.spec.key, value)
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CTRL_HIGH_SOC_THRESHOLD
from .coordinator import ZerofeedCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ZerofeedCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[BinarySensorEntity] = [
        ZerofeedHighPriorityDischargeSensor(coordinator, entry),
    ]

    async_add_entities(entities)


class ZerofeedHighPriorityDischargeSensor(CoordinatorEntity[ZerofeedCoordinator], BinarySensorEntity):
    _attr_translation_key = "high_priority_discharge_active"
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_has_entity_name = True

    def __init__(self, coordinator: ZerofeedCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_high_priority_discharge_active"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="ZeroFeed",
        )

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None

        controls = self.coordinator.data.get("controls") or {}
        high_soc_threshold = controls.get(CTRL_HIGH_SOC_THRESHOLD, 0.0)

        # High priority discharge is active if:
        # 1. Threshold is configured (> 0)
        # 2. At least one valid battery has SoC >= threshold
        if high_soc_threshold <= 0.0:
            return False

        batteries = self.coordinator.data.get("batteries") or {}
        for battery_data in batteries.values():
            if battery_data.get("valid") and battery_data.get("soc") is not None:
                if battery_data["soc"] >= high_soc_threshold:
                    return True

        return False

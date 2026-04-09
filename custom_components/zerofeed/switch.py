from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BatteryConfig, ZerofeedCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ZerofeedCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[SwitchEntity] = [
        ZerofeedBatteryEnabledSwitch(coordinator, entry, b) for b in coordinator.batteries
    ]
    async_add_entities(entities)


class ZerofeedBatteryEnabledSwitch(
    CoordinatorEntity[ZerofeedCoordinator],
    RestoreEntity,
    SwitchEntity,
):
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: ZerofeedCoordinator, entry: ConfigEntry, battery: BatteryConfig) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self.battery = battery

        self._attr_has_entity_name = True
        self._attr_translation_key = "battery_enabled"
        self._attr_unique_id = f"{entry.entry_id}_{battery.battery_id}_enabled"
        self._attr_icon = "mdi:battery-check"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id, battery.battery_id)},
            name=f"ZeroFeed {battery.name}",
            via_device=(DOMAIN, entry.entry_id),
        )

        self._attr_is_on = True

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None:
            if last.state == "off":
                self._attr_is_on = False
            elif last.state == "on":
                self._attr_is_on = True
        self.coordinator.set_battery_disabled(self.battery.battery_id, not self._attr_is_on)
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    @property
    def is_on(self) -> bool:
        return not self.coordinator.is_battery_disabled(self.battery.battery_id)

    async def async_turn_on(self, **kwargs) -> None:
        self._attr_is_on = True
        self.coordinator.set_battery_disabled(self.battery.battery_id, False)
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        self._attr_is_on = False
        self.coordinator.set_battery_disabled(self.battery.battery_id, True)
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

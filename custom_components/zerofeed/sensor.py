from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ZerofeedCoordinator


@dataclass(frozen=True)
class _BatteryRef:
    battery_id: str
    name: str


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ZerofeedCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[SensorEntity] = [
        ZerofeedTotalFeedinSensor(coordinator, entry),
        ZerofeedTargetSensor(coordinator, entry),
        ZerofeedAvgSocSensor(coordinator, entry),
    ]

    for b in coordinator.batteries:
        bref = _BatteryRef(battery_id=b.battery_id, name=b.name)
        entities.append(ZerofeedBatteryFeedinSensor(coordinator, entry, bref))
        entities.append(ZerofeedBatteryShareSensor(coordinator, entry, bref))

    async_add_entities(entities)


class _ZerofeedBaseSensor(CoordinatorEntity[ZerofeedCoordinator], SensorEntity):
    def __init__(self, coordinator: ZerofeedCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="ZeroFeed",
        )


class ZerofeedTotalFeedinSensor(_ZerofeedBaseSensor):
    _attr_translation_key = "total_feedin_power"
    _attr_unique_id = "total_feedin_power"
    _attr_native_unit_of_measurement = "W"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ZerofeedCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_total_feedin_power"

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        # Display-friendly rounding only; coordinator keeps full precision.
        return round(float(self.coordinator.data.get("total_feedin_w")), 1)

    @property
    def extra_state_attributes(self) -> dict:
        if not self.coordinator.data:
            return {}
        return {
            "load_w": self.coordinator.data.get("load_w"),
            "target_total_w": self.coordinator.data.get("target_total_w"),
            **(self.coordinator.data.get("controls") or {}),
        }


class ZerofeedTargetSensor(_ZerofeedBaseSensor):
    _attr_translation_key = "target_total_power"
    _attr_native_unit_of_measurement = "W"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ZerofeedCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_target_total_power"

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        return round(float(self.coordinator.data.get("target_total_w")), 1)


class ZerofeedAvgSocSensor(_ZerofeedBaseSensor):
    _attr_translation_key = "average_soc"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ZerofeedCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_average_soc"

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        val = self.coordinator.data.get("avg_soc")
        return None if val is None else round(float(val), 1)


class _ZerofeedBatteryBaseSensor(CoordinatorEntity[ZerofeedCoordinator], SensorEntity):
    def __init__(self, coordinator: ZerofeedCoordinator, entry: ConfigEntry, battery: _BatteryRef) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self.battery = battery
        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id, battery.battery_id)},
            name=f"ZeroFeed {battery.name}",
            via_device=(DOMAIN, entry.entry_id),
        )

    @property
    def _battery_data(self) -> dict | None:
        if not self.coordinator.data:
            return None
        return (self.coordinator.data.get("batteries") or {}).get(self.battery.battery_id)


class ZerofeedBatteryFeedinSensor(_ZerofeedBatteryBaseSensor):
    _attr_translation_key = "feedin_power"
    _attr_native_unit_of_measurement = "W"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ZerofeedCoordinator, entry: ConfigEntry, battery: _BatteryRef) -> None:
        super().__init__(coordinator, entry, battery)
        self._attr_unique_id = f"{entry.entry_id}_{battery.battery_id}_feedin_power"

    @property
    def native_value(self) -> float | None:
        data = self._battery_data
        if not data:
            return None
        val = data.get("feedin_w")
        return None if val is None else round(float(val), 1)

    @property
    def extra_state_attributes(self) -> dict:
        data = self._battery_data
        if not data:
            return {}
        return {
            "soc": data.get("soc"),
            "capacity_wh": data.get("capacity_wh"),
            "min_soc_threshold": data.get("min_soc_threshold"),
            "min_soc_entity": data.get("min_soc_entity"),
            "disabled": data.get("disabled"),
            "raw_weight": data.get("raw_weight"),
            "share": data.get("share"),
            "valid": data.get("valid"),
        }


class ZerofeedBatteryShareSensor(_ZerofeedBatteryBaseSensor):
    _attr_translation_key = "share"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: ZerofeedCoordinator, entry: ConfigEntry, battery: _BatteryRef) -> None:
        super().__init__(coordinator, entry, battery)
        self._attr_unique_id = f"{entry.entry_id}_{battery.battery_id}_share"

    @property
    def native_value(self) -> float | None:
        data = self._battery_data
        if not data or data.get("share") is None:
            return None
        return round(float(data["share"]) * 100.0, 1)

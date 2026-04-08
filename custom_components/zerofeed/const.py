from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "zerofeed"

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.NUMBER]

CONF_LOAD_ENTITY = "load_entity"
CONF_BATTERIES = "batteries"
CONF_BATTERY_ID = "id"
CONF_BATTERY_NAME = "name"
CONF_SOC_ENTITY = "soc_entity"
CONF_CAPACITY_ENTITY = "capacity_entity"
CONF_MIN_SOC_ENTITY = "min_soc_entity"

# Control keys (backed by NumberEntity states).
CTRL_TOTAL_MAX_W = "total_max_w"
CTRL_PER_BATTERY_MAX_W = "per_battery_max_w"
CTRL_SIGMOID_K = "sigmoid_k"
CTRL_SIGMOID_CENTER_OFFSET = "sigmoid_center_offset"

DEFAULT_TOTAL_MAX_W = 4000.0
DEFAULT_PER_BATTERY_MAX_W = 2000.0
DEFAULT_SIGMOID_K = 0.25
DEFAULT_SIGMOID_CENTER_OFFSET = 0.0

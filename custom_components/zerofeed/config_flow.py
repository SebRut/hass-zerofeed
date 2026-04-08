from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.selector import selector
from homeassistant.util import slugify

from .const import (
    CONF_BATTERIES,
    CONF_BATTERY_ID,
    CONF_BATTERY_NAME,
    CONF_CAPACITY_ENTITY,
    CONF_LOAD_ENTITY,
    CONF_MIN_SOC_ENTITY,
    CONF_SOC_ENTITY,
    DOMAIN,
)


class ZerofeedConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._load_entity: str | None = None
        self._batteries: list[dict] = []

    def _unit_ok(self, entity_id: str, allowed: set[str]) -> bool:
        """Return True if the entity exists and its unit_of_measurement is in allowed."""
        state = self.hass.states.get(entity_id)
        if state is None:
            return False
        unit = state.attributes.get("unit_of_measurement")
        return unit in allowed

    async def async_step_user(self, user_input: dict | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            load_entity = user_input[CONF_LOAD_ENTITY]
            if not self._unit_ok(load_entity, {"W", "kW"}):
                errors[CONF_LOAD_ENTITY] = "invalid_load_unit"
            else:
                self._load_entity = load_entity
                return await self.async_step_battery()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LOAD_ENTITY): selector(
                        {
                            "entity": {
                                "multiple": False,
                                "domain": ["sensor", "input_number", "number"],
                            }
                        }
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_battery(self, user_input: dict | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_BATTERY_NAME].strip()
            soc_entity = user_input[CONF_SOC_ENTITY]
            capacity_entity = user_input[CONF_CAPACITY_ENTITY]
            min_soc_entity = user_input.get(CONF_MIN_SOC_ENTITY)
            add_another = user_input.get("add_another", False)

            if not self._unit_ok(soc_entity, {"%"}):
                errors[CONF_SOC_ENTITY] = "invalid_soc_unit"
            if not self._unit_ok(capacity_entity, {"Wh", "kWh"}):
                errors[CONF_CAPACITY_ENTITY] = "invalid_capacity_unit"
            if min_soc_entity and not self._unit_ok(min_soc_entity, {"%"}):
                errors[CONF_MIN_SOC_ENTITY] = "invalid_min_soc_unit"
            if errors:
                min_soc_field = (
                    vol.Optional(CONF_MIN_SOC_ENTITY, default=min_soc_entity)
                    if min_soc_entity
                    else vol.Optional(CONF_MIN_SOC_ENTITY)
                )
                return self.async_show_form(
                    step_id="battery",
                    data_schema=vol.Schema(
                        {
                            vol.Required(CONF_BATTERY_NAME, default=name): str,
                            vol.Required(CONF_SOC_ENTITY): selector(
                                {
                                    "entity": {
                                        "multiple": False,
                                        "domain": ["sensor", "input_number", "number"],
                                    }
                                }
                            ),
                            vol.Required(CONF_CAPACITY_ENTITY): selector(
                                {
                                    "entity": {
                                        "multiple": False,
                                        "domain": ["sensor", "input_number", "number"],
                                    }
                                }
                            ),
                            min_soc_field: selector(
                                {
                                    "entity": {
                                        "multiple": False,
                                        "domain": ["sensor", "input_number", "number"],
                                    }
                                }
                            ),
                            vol.Optional("add_another", default=add_another): bool,
                        }
                    ),
                    errors=errors,
                )

            existing_ids = {b[CONF_BATTERY_ID] for b in self._batteries}
            base_id = slugify(name) or "battery"
            battery_id = base_id
            i = 2
            while battery_id in existing_ids:
                battery_id = f"{base_id}_{i}"
                i += 1

            self._batteries.append(
                {
                    CONF_BATTERY_ID: battery_id,
                    CONF_BATTERY_NAME: name,
                    CONF_SOC_ENTITY: soc_entity,
                    CONF_CAPACITY_ENTITY: capacity_entity,
                    **({CONF_MIN_SOC_ENTITY: min_soc_entity} if min_soc_entity else {}),
                }
            )

            if add_another:
                return await self.async_step_battery()

            return self.async_create_entry(
                title="ZeroFeed",
                data={
                    CONF_LOAD_ENTITY: self._load_entity,
                    CONF_BATTERIES: self._batteries,
                },
            )

        return self.async_show_form(
            step_id="battery",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_BATTERY_NAME): str,
                    vol.Required(CONF_SOC_ENTITY): selector(
                        {
                            "entity": {
                                "multiple": False,
                                "domain": ["sensor", "input_number", "number"],
                            }
                        }
                    ),
                    vol.Required(CONF_CAPACITY_ENTITY): selector(
                        {
                            "entity": {
                                "multiple": False,
                                "domain": ["sensor", "input_number", "number"],
                            }
                        }
                    ),
                    vol.Optional(CONF_MIN_SOC_ENTITY): selector(
                        {
                            "entity": {
                                "multiple": False,
                                "domain": ["sensor", "input_number", "number"],
                            }
                        }
                    ),
                    vol.Optional("add_another", default=False): bool,
                }
            ),
            errors=errors,
            description_placeholders={"count": str(len(self._batteries) + 1)},
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return ZerofeedOptionsFlowHandler(config_entry)


class ZerofeedOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        # HA exposes a read-only `config_entry` property on OptionsFlow, so keep our own reference.
        self._entry = config_entry
        self._selected_battery_id: str | None = None

    def _unit_ok(self, entity_id: str, allowed: set[str]) -> bool:
        state = self.hass.states.get(entity_id)
        if state is None:
            return False
        unit = state.attributes.get("unit_of_measurement")
        return unit in allowed

    def _current_batteries(self) -> list[dict]:
        return list(self._entry.options.get(CONF_BATTERIES, self._entry.data.get(CONF_BATTERIES, [])))

    async def async_step_init(self, user_input: dict | None = None):
        return await self.async_step_menu()

    async def async_step_menu(self, user_input: dict | None = None):
        return self.async_show_menu(
            step_id="menu",
            menu_options=["change_load", "add_battery", "edit_battery"],
        )

    async def async_step_change_load(self, user_input: dict | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            load_entity = user_input[CONF_LOAD_ENTITY]
            if not self._unit_ok(load_entity, {"W", "kW"}):
                errors[CONF_LOAD_ENTITY] = "invalid_load_unit"
            else:
                options = dict(self._entry.options)
                options[CONF_LOAD_ENTITY] = load_entity
                return self.async_create_entry(title="", data=options)

        current = self._entry.options.get(CONF_LOAD_ENTITY, self._entry.data[CONF_LOAD_ENTITY])
        return self.async_show_form(
            step_id="change_load",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LOAD_ENTITY, default=current): selector(
                        {
                            "entity": {
                                "multiple": False,
                                "domain": ["sensor", "input_number", "number"],
                            }
                        }
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_add_battery(self, user_input: dict | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input[CONF_BATTERY_NAME].strip()
            soc_entity = user_input[CONF_SOC_ENTITY]
            capacity_entity = user_input[CONF_CAPACITY_ENTITY]
            min_soc_entity = user_input.get(CONF_MIN_SOC_ENTITY)

            if not self._unit_ok(soc_entity, {"%"}):
                errors[CONF_SOC_ENTITY] = "invalid_soc_unit"
            if not self._unit_ok(capacity_entity, {"Wh", "kWh"}):
                errors[CONF_CAPACITY_ENTITY] = "invalid_capacity_unit"
            if min_soc_entity and not self._unit_ok(min_soc_entity, {"%"}):
                errors[CONF_MIN_SOC_ENTITY] = "invalid_min_soc_unit"
            if errors:
                return self.async_show_form(
                    step_id="add_battery",
                    data_schema=_battery_schema(
                        name=name,
                        soc_entity=soc_entity,
                        capacity_entity=capacity_entity,
                        min_soc_entity=min_soc_entity,
                    ),
                    errors=errors,
                )

            batteries = self._current_batteries()
            existing_ids = {b.get(CONF_BATTERY_ID) for b in batteries if b.get(CONF_BATTERY_ID)}

            base_id = slugify(name) or "battery"
            battery_id = base_id
            i = 2
            while battery_id in existing_ids:
                battery_id = f"{base_id}_{i}"
                i += 1

            batteries.append(
                {
                    CONF_BATTERY_ID: battery_id,
                    CONF_BATTERY_NAME: name,
                    CONF_SOC_ENTITY: soc_entity,
                    CONF_CAPACITY_ENTITY: capacity_entity,
                    **({CONF_MIN_SOC_ENTITY: min_soc_entity} if min_soc_entity else {}),
                }
            )

            options = dict(self._entry.options)
            options[CONF_BATTERIES] = batteries
            return self.async_create_entry(title="", data=options)

        return self.async_show_form(
            step_id="add_battery",
            data_schema=_battery_schema(),
            errors=errors,
        )

    async def async_step_edit_battery(self, user_input: dict | None = None):
        batteries = self._current_batteries()
        choices = {b.get(CONF_BATTERY_ID, ""): b.get(CONF_BATTERY_NAME, b.get(CONF_BATTERY_ID, "")) for b in batteries}
        choices = {k: v for k, v in choices.items() if k}

        if not choices:
            return self.async_abort(reason="no_batteries")

        if user_input is not None:
            self._selected_battery_id = user_input["battery_id"]
            return await self.async_step_edit_battery_settings()

        return self.async_show_form(
            step_id="edit_battery",
            data_schema=vol.Schema({vol.Required("battery_id"): vol.In(choices)}),
        )

    async def async_step_edit_battery_settings(self, user_input: dict | None = None):
        batteries = self._current_batteries()
        bid = self._selected_battery_id
        battery = next((b for b in batteries if b.get(CONF_BATTERY_ID) == bid), None)
        if not bid or not battery:
            return self.async_abort(reason="battery_not_found")

        errors: dict[str, str] = {}
        if user_input is not None:
            name = user_input[CONF_BATTERY_NAME].strip()
            soc_entity = user_input[CONF_SOC_ENTITY]
            capacity_entity = user_input[CONF_CAPACITY_ENTITY]
            min_soc_entity = user_input.get(CONF_MIN_SOC_ENTITY)

            if not name:
                errors[CONF_BATTERY_NAME] = "required"
            if not self._unit_ok(soc_entity, {"%"}):
                errors[CONF_SOC_ENTITY] = "invalid_soc_unit"
            if not self._unit_ok(capacity_entity, {"Wh", "kWh"}):
                errors[CONF_CAPACITY_ENTITY] = "invalid_capacity_unit"
            if min_soc_entity and not self._unit_ok(min_soc_entity, {"%"}):
                errors[CONF_MIN_SOC_ENTITY] = "invalid_min_soc_unit"

            if not errors:
                battery = {
                    **battery,
                    CONF_BATTERY_NAME: name,
                    CONF_SOC_ENTITY: soc_entity,
                    CONF_CAPACITY_ENTITY: capacity_entity,
                }
                if min_soc_entity:
                    battery[CONF_MIN_SOC_ENTITY] = min_soc_entity
                else:
                    battery.pop(CONF_MIN_SOC_ENTITY, None)

                new_batteries = [battery if b.get(CONF_BATTERY_ID) == bid else b for b in batteries]
                options = dict(self._entry.options)
                options[CONF_BATTERIES] = new_batteries
                return self.async_create_entry(title="", data=options)

        return self.async_show_form(
            step_id="edit_battery_settings",
            data_schema=_battery_schema(
                name=battery.get(CONF_BATTERY_NAME),
                soc_entity=battery.get(CONF_SOC_ENTITY),
                capacity_entity=battery.get(CONF_CAPACITY_ENTITY),
                min_soc_entity=battery.get(CONF_MIN_SOC_ENTITY),
            ),
            errors=errors,
        )


def _battery_schema(
    name: str | None = None,
    soc_entity: str | None = None,
    capacity_entity: str | None = None,
    min_soc_entity: str | None = None,
) -> vol.Schema:
    soc_sel = selector(
        {
            "entity": {
                "multiple": False,
                "domain": ["sensor", "input_number", "number"],
            }
        }
    )
    cap_sel = selector(
        {
            "entity": {
                "multiple": False,
                "domain": ["sensor", "input_number", "number"],
            }
        }
    )
    min_soc_sel = selector(
        {
            "entity": {
                "multiple": False,
                "domain": ["sensor", "input_number", "number"],
            }
        }
    )

    # Note: entity selectors can't be filtered by unit in the UI, so we validate units on submit.
    name_key = vol.Required(CONF_BATTERY_NAME, default=name) if name is not None else vol.Required(CONF_BATTERY_NAME)
    soc_key = vol.Required(CONF_SOC_ENTITY, default=soc_entity) if soc_entity is not None else vol.Required(CONF_SOC_ENTITY)
    cap_key = (
        vol.Required(CONF_CAPACITY_ENTITY, default=capacity_entity)
        if capacity_entity is not None
        else vol.Required(CONF_CAPACITY_ENTITY)
    )
    min_soc_key = (
        vol.Optional(CONF_MIN_SOC_ENTITY, default=min_soc_entity)
        if min_soc_entity is not None
        else vol.Optional(CONF_MIN_SOC_ENTITY)
    )

    return vol.Schema(
        {
            name_key: str,
            soc_key: soc_sel,
            cap_key: cap_sel,
            min_soc_key: min_soc_sel,
        }
    )

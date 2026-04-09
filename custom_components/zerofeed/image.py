from __future__ import annotations

import math

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_SIGMOID_CENTER_OFFSET, DEFAULT_SIGMOID_K, DOMAIN
from .coordinator import ZerofeedCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ZerofeedCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([ZerofeedSigmoidCurveImage(coordinator, entry)])


class ZerofeedSigmoidCurveImage(CoordinatorEntity[ZerofeedCoordinator], ImageEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False
    _attr_translation_key = "sigmoid_curve"
    _attr_content_type = "image/svg+xml"

    def __init__(self, coordinator: ZerofeedCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{entry.entry_id}_sigmoid_curve"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="ZeroFeed",
        )
        # ImageEntity expects at least one access token for the proxy URL.
        self.access_tokens: list[str] = []
        self.async_update_token()

    async def async_image(self) -> bytes | None:
        return self._render_svg()

    def _render_svg(self) -> bytes:
        controls = self.coordinator.data.get("controls") if self.coordinator.data else {}
        sigmoid_k = float(controls.get("sigmoid_k", DEFAULT_SIGMOID_K))
        center_offset = float(controls.get("sigmoid_center_offset", DEFAULT_SIGMOID_CENTER_OFFSET))
        avg_soc = None
        if self.coordinator.data:
            avg_soc = self.coordinator.data.get("avg_soc")
        center = (float(avg_soc) if avg_soc is not None else 50.0) + center_offset

        k = max(0.0, sigmoid_k)

        width = 460
        height = 240
        pad = 30
        plot_w = width - 2 * pad
        plot_h = height - 2 * pad

        points: list[str] = []
        for soc in range(0, 101):
            x = pad + plot_w * (soc / 100.0)
            y = 1.0 / (1.0 + math.exp(-k * (soc - center)))
            y_px = pad + (1.0 - y) * plot_h
            points.append(f"{x:.1f},{y_px:.1f}")

        center_x = pad + plot_w * (center / 100.0)
        center_x = max(pad, min(pad + plot_w, center_x))

        label_k = f"k={k:.2f}"
        label_center = f"center={center:.1f}%"
        svg = "".join(
            [
                f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>",
                f"<rect x='0' y='0' width='{width}' height='{height}' fill='white' stroke='#dddddd'/>",
                f"<line x1='{pad}' y1='{pad}' x2='{pad}' y2='{pad + plot_h}' stroke='#333333' stroke-width='1'/>",
                f"<line x1='{pad}' y1='{pad + plot_h}' x2='{pad + plot_w}' y2='{pad + plot_h}' stroke='#333333' stroke-width='1'/>",
                f"<line x1='{center_x:.1f}' y1='{pad}' x2='{center_x:.1f}' y2='{pad + plot_h}' stroke='#cccccc' stroke-dasharray='4,4'/>",
                f"<polyline fill='none' stroke='#1a73e8' stroke-width='2' points='{' '.join(points)}'/>",
                f"<text x='{pad}' y='{height - 8}' font-size='12' fill='#333333'>SoC (%)</text>",
                f"<text x='8' y='{pad - 10}' font-size='12' fill='#333333'>Weight</text>",
                f"<text x='{pad}' y='16' font-size='12' fill='#333333'>{label_k}</text>",
                f"<text x='{pad + 80}' y='16' font-size='12' fill='#333333'>{label_center}</text>",
                "</svg>",
            ]
        )
        return svg.encode("utf-8")

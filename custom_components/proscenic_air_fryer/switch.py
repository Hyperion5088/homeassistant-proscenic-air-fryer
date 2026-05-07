"""Switch entities for Proscenic air fryers."""

from __future__ import annotations

from typing import Any, Callable

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ProscenicAirFryerCoordinator
from .entity import ProscenicAirFryerEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Proscenic air fryer switches."""
    coordinator: ProscenicAirFryerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ProscenicAirFryerSwitch(
                coordinator,
                "power",
                "Power",
                "mdi:power",
                lambda data: data.power,
                coordinator.async_set_power,
            ),
            ProscenicAirFryerSwitch(
                coordinator,
                "keep_warm",
                "Keep Warm",
                "mdi:heat-wave",
                lambda data: data.keep_warm,
                coordinator.async_set_keep_warm,
            ),
            ProscenicAirFryerSwitch(
                coordinator,
                "delayed_cook",
                "Delayed Cook",
                "mdi:timer-outline",
                lambda data: data.delayed_cook,
                coordinator.async_set_delayed_cook,
            ),
        ]
    )


class ProscenicAirFryerSwitch(ProscenicAirFryerEntity, SwitchEntity):
    """A Proscenic air fryer switch."""

    def __init__(
        self,
        coordinator: ProscenicAirFryerCoordinator,
        suffix: str,
        name: str,
        icon: str,
        value_fn: Callable[[Any], bool | None],
        set_fn: Callable[[bool], Any],
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, suffix)
        self._attr_name = name
        self._attr_icon = icon
        self._value_fn = value_fn
        self._set_fn = set_fn

    @property
    def is_on(self) -> bool | None:
        """Return whether the switch is on."""
        return self._value_fn(self.coordinator.data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        await self._set_fn(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        await self._set_fn(False)

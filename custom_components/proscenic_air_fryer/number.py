"""Number entities for Proscenic air fryers."""

from __future__ import annotations

from typing import Any, Callable

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
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
    """Set up Proscenic air fryer numbers."""
    coordinator: ProscenicAirFryerCoordinator = hass.data[DOMAIN][entry.entry_id]
    temp_min = 180 if coordinator.temperature_unit == "F" else 80
    temp_max = 400 if coordinator.temperature_unit == "F" else 205
    temp_step = 5 if coordinator.temperature_unit == "F" else 1
    unit = (
        UnitOfTemperature.FAHRENHEIT
        if coordinator.temperature_unit == "F"
        else UnitOfTemperature.CELSIUS
    )
    async_add_entities(
        [
            ProscenicAirFryerNumber(
                coordinator,
                "cooking_temperature",
                "Cooking Temperature",
                "mdi:thermometer",
                temp_min,
                temp_max,
                temp_step,
                unit,
                lambda data: coordinator.display_temperature(data.cooking_temperature),
                coordinator.async_set_cooking_temperature,
                NumberMode.SLIDER,
            ),
            ProscenicAirFryerNumber(
                coordinator,
                "cooking_time",
                "Cooking Time",
                "mdi:timer",
                1,
                60,
                1,
                "min",
                lambda data: data.cooking_time,
                coordinator.async_set_cooking_time,
                NumberMode.SLIDER,
            ),
            ProscenicAirFryerNumber(
                coordinator,
                "warm_time",
                "Keep Warm Time",
                "mdi:timer-sand",
                1,
                60,
                1,
                "min",
                lambda data: data.warm_time,
                coordinator.async_set_warm_time,
                NumberMode.SLIDER,
            ),
            ProscenicAirFryerNumber(
                coordinator,
                "delayed_time",
                "Delayed Time",
                "mdi:timer-cog-outline",
                0,
                720,
                1,
                "min",
                lambda data: data.delayed_time,
                coordinator.async_set_delayed_time,
                NumberMode.SLIDER,
            ),
            ProscenicAirFryerNumber(
                coordinator,
                "cooking_temperature_input",
                "Cooking Temperature Input",
                "mdi:thermometer",
                temp_min,
                temp_max,
                temp_step,
                unit,
                lambda data: coordinator.display_temperature(data.cooking_temperature),
                coordinator.async_set_cooking_temperature,
                NumberMode.BOX,
                enabled_default=False,
            ),
            ProscenicAirFryerNumber(
                coordinator,
                "cooking_time_input",
                "Cooking Time Input",
                "mdi:timer-edit",
                1,
                60,
                1,
                "min",
                lambda data: data.cooking_time,
                coordinator.async_set_cooking_time,
                NumberMode.BOX,
                enabled_default=False,
            ),
            ProscenicAirFryerNumber(
                coordinator,
                "warm_time_input",
                "Keep Warm Time Input",
                "mdi:timer-edit-outline",
                1,
                60,
                1,
                "min",
                lambda data: data.warm_time,
                coordinator.async_set_warm_time,
                NumberMode.BOX,
                enabled_default=False,
            ),
            ProscenicAirFryerNumber(
                coordinator,
                "delayed_time_input",
                "Delayed Time Input",
                "mdi:timer-edit-outline",
                0,
                720,
                1,
                "min",
                lambda data: data.delayed_time,
                coordinator.async_set_delayed_time,
                NumberMode.BOX,
                enabled_default=False,
            ),
        ]
    )


class ProscenicAirFryerNumber(ProscenicAirFryerEntity, NumberEntity):
    """A Proscenic air fryer numeric setting."""

    def __init__(
        self,
        coordinator: ProscenicAirFryerCoordinator,
        suffix: str,
        name: str,
        icon: str,
        minimum: int,
        maximum: int,
        step: int,
        unit: str,
        value_fn: Callable[[Any], int | None],
        set_fn: Callable[[int], Any],
        mode: NumberMode,
        enabled_default: bool = True,
    ) -> None:
        """Initialize the number."""
        super().__init__(coordinator, suffix)
        self._attr_name = name
        self._attr_icon = icon
        self._attr_mode = mode
        self._attr_entity_registry_enabled_default = enabled_default
        self._attr_native_min_value = minimum
        self._attr_native_max_value = maximum
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit
        self._value_fn = value_fn
        self._set_fn = set_fn

    @property
    def native_value(self) -> int | None:
        """Return the current value."""
        return self._value_fn(self.coordinator.data)

    async def async_set_native_value(self, value: float) -> None:
        """Set a new value."""
        await self._set_fn(int(value))

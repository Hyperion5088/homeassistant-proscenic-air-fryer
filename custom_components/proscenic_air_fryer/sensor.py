"""Sensor entities for Proscenic air fryers."""

from __future__ import annotations

from typing import Any, Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MODE_OPTIONS, STATUS_OPTIONS
from .coordinator import ProscenicAirFryerCoordinator
from .entity import ProscenicAirFryerEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Proscenic air fryer sensors."""
    coordinator: ProscenicAirFryerCoordinator = hass.data[DOMAIN][entry.entry_id]
    unit = (
        UnitOfTemperature.FAHRENHEIT
        if coordinator.temperature_unit == "F"
        else UnitOfTemperature.CELSIUS
    )
    async_add_entities(
        [
            ProscenicAirFryerSensor(
                coordinator,
                "status",
                "Status",
                "mdi:pot-steam",
                lambda data: STATUS_OPTIONS.get(data.status, data.status),
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "mode",
                "Mode",
                "mdi:silverware-fork-knife",
                lambda data: MODE_OPTIONS.get(data.mode, data.mode),
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "current_temperature",
                "Current Temperature",
                "mdi:thermometer",
                lambda data: data.cooking_temperature,
                unit,
                SensorDeviceClass.TEMPERATURE,
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "remaining_time",
                "Remaining Time",
                "mdi:timer-sand",
                lambda data: data.remaining_time,
                "min",
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "pot_pulled",
                "Basket Removed",
                "mdi:pot",
                lambda data: data.pot_pulled,
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "last_update",
                "Last Update",
                "mdi:clock-outline",
                lambda data: data.last_update,
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        ]
    )


class ProscenicAirFryerSensor(ProscenicAirFryerEntity, SensorEntity):
    """A Proscenic air fryer sensor."""

    def __init__(
        self,
        coordinator: ProscenicAirFryerCoordinator,
        suffix: str,
        name: str,
        icon: str,
        value_fn: Callable[[Any], Any],
        unit: str | None = None,
        device_class: SensorDeviceClass | None = None,
        entity_category: EntityCategory | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, suffix)
        self._attr_name = name
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_entity_category = entity_category
        self._value_fn = value_fn

    @property
    def native_value(self) -> Any:
        """Return the current value."""
        return self._value_fn(self.coordinator.data)

"""Sensor entities for Proscenic air fryers."""

from __future__ import annotations

from typing import Any, Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEVICE_ID,
    CONF_DISCOVERY_METHOD,
    CONF_HOST,
    CONF_LOCAL_KEY,
    CONF_PROTOCOL_VERSION,
    CONF_REGION,
    CONF_SCAN_SUBNET,
    DOMAIN,
    MODE_OPTIONS,
    STATUS_OPTIONS,
)
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
                lambda data: coordinator.display_temperature(data.cooking_temperature),
                unit,
                SensorDeviceClass.TEMPERATURE,
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "remaining_time",
                "Remaining Time",
                "mdi:timer-sand",
                lambda data: (
                    data.remaining_time
                    if data.status in {"cooking", "appointment", "warm"}
                    else None
                ),
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
                "unknown_12",
                "Unknown DP 12",
                "mdi:help-circle-outline",
                lambda data: data.unknown_12,
                entity_category=EntityCategory.DIAGNOSTIC,
                enabled_default=False,
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "temperature_unit_flag",
                "Temperature Unit Flag",
                "mdi:thermometer-lines",
                lambda data: data.temperature_unit_flag,
                entity_category=EntityCategory.DIAGNOSTIC,
                enabled_default=False,
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "unknown_107",
                "Unknown DP 107",
                "mdi:help-circle-outline",
                lambda data: data.unknown_107,
                entity_category=EntityCategory.DIAGNOSTIC,
                enabled_default=False,
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "raw_dps",
                "Raw DPS",
                "mdi:code-json",
                lambda data: len(data.raw),
                entity_category=EntityCategory.DIAGNOSTIC,
                enabled_default=False,
                attributes_fn=lambda data: {"dps": data.raw},
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "raw_mode",
                "Raw Mode",
                "mdi:code-string",
                lambda data: data.mode,
                entity_category=EntityCategory.DIAGNOSTIC,
                enabled_default=False,
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "last_update",
                "Last Update",
                "mdi:clock-outline",
                lambda data: data.last_update,
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "diagnostic_host",
                "Fryer IP Address",
                "mdi:ip-network",
                lambda data: coordinator.config.get(CONF_HOST),
                entity_category=EntityCategory.DIAGNOSTIC,
                enabled_default=False,
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "diagnostic_device_name",
                "Device Name",
                "mdi:air-fryer",
                lambda data: coordinator.entry.title,
                entity_category=EntityCategory.DIAGNOSTIC,
                enabled_default=False,
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "diagnostic_device_id",
                "Device ID",
                "mdi:identifier",
                lambda data: coordinator.config.get(CONF_DEVICE_ID),
                entity_category=EntityCategory.DIAGNOSTIC,
                enabled_default=False,
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "diagnostic_local_key",
                "Local Key",
                "mdi:key-variant",
                lambda data: coordinator.config.get(CONF_LOCAL_KEY),
                entity_category=EntityCategory.DIAGNOSTIC,
                enabled_default=False,
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "diagnostic_product_id",
                "Product ID",
                "mdi:barcode",
                lambda data: coordinator.config.get("product_id"),
                entity_category=EntityCategory.DIAGNOSTIC,
                enabled_default=False,
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "diagnostic_category",
                "Tuya Category",
                "mdi:tag-outline",
                lambda data: coordinator.config.get("category"),
                entity_category=EntityCategory.DIAGNOSTIC,
                enabled_default=False,
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "diagnostic_protocol_version",
                "Tuya Protocol Version",
                "mdi:lan-connect",
                lambda data: coordinator.config.get(CONF_PROTOCOL_VERSION),
                entity_category=EntityCategory.DIAGNOSTIC,
                enabled_default=False,
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "diagnostic_discovery_method",
                "Discovery Method",
                "mdi:radar",
                lambda data: coordinator.config.get(CONF_DISCOVERY_METHOD),
                entity_category=EntityCategory.DIAGNOSTIC,
                enabled_default=False,
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "diagnostic_scan_subnet",
                "Scan Subnet",
                "mdi:ip-network-outline",
                lambda data: coordinator.config.get(CONF_SCAN_SUBNET),
                entity_category=EntityCategory.DIAGNOSTIC,
                enabled_default=False,
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "diagnostic_region",
                "Tuya Region",
                "mdi:earth",
                lambda data: coordinator.config.get(CONF_REGION),
                entity_category=EntityCategory.DIAGNOSTIC,
                enabled_default=False,
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "diagnostic_uuid",
                "Tuya UUID",
                "mdi:fingerprint",
                lambda data: coordinator.config.get("uuid"),
                entity_category=EntityCategory.DIAGNOSTIC,
                enabled_default=False,
            ),
            ProscenicAirFryerSensor(
                coordinator,
                "diagnostic_initial_dps",
                "Initial DPS",
                "mdi:code-braces",
                lambda data: len(coordinator.entry.data.get("initial_dps") or {}),
                entity_category=EntityCategory.DIAGNOSTIC,
                enabled_default=False,
                attributes_fn=lambda data: {
                    "dps": coordinator.entry.data.get("initial_dps") or {}
                },
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
        enabled_default: bool = True,
        attributes_fn: Callable[[Any], dict[str, Any]] | None = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, suffix)
        self._attr_name = name
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_entity_category = entity_category
        self._attr_entity_registry_enabled_default = enabled_default
        self._value_fn = value_fn
        self._attributes_fn = attributes_fn

    @property
    def native_value(self) -> Any:
        """Return the current value."""
        return self._value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra sensor attributes."""
        if self._attributes_fn is None:
            return None
        return self._attributes_fn(self.coordinator.data)

"""Entity helpers for Proscenic air fryers."""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_ID, CONF_MAC_ADDRESS, DOMAIN
from .coordinator import ProscenicAirFryerCoordinator


class ProscenicAirFryerEntity(CoordinatorEntity[ProscenicAirFryerCoordinator]):
    """Base entity for the Proscenic air fryer."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ProscenicAirFryerCoordinator, suffix: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{suffix}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return Home Assistant device information."""
        config = self.coordinator.config
        connections = set()
        mac_address = self.coordinator.entry.data.get(CONF_MAC_ADDRESS)
        if mac_address:
            connections.add((CONNECTION_NETWORK_MAC, mac_address))
        return DeviceInfo(
            connections=connections,
            identifiers={(DOMAIN, config[CONF_DEVICE_ID])},
            manufacturer="Proscenic",
            model="T21 Air Fryer",
            name=self.coordinator.entry.title,
        )

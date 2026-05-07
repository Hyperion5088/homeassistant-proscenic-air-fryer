"""Entity helpers for Proscenic air fryers."""

from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_ID, DOMAIN
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
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.data[CONF_DEVICE_ID])},
            manufacturer="Proscenic",
            model="T21 Air Fryer",
            name=self.coordinator.entry.title,
        )

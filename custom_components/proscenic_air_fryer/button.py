"""Button entities for Proscenic air fryers."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ProscenicAirFryerCoordinator
from .entity import ProscenicAirFryerEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Proscenic air fryer buttons."""
    coordinator: ProscenicAirFryerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ProscenicStatusButton(coordinator),
            ProscenicStartStopButton(coordinator),
        ]
    )


class ProscenicStatusButton(ProscenicAirFryerEntity, ButtonEntity):
    """Request a fresh status snapshot."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:refresh"
    _attr_name = "Request Status"

    def __init__(self, coordinator: ProscenicAirFryerCoordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator, "request_status")

    async def async_press(self) -> None:
        """Request state from the fryer."""
        await self.coordinator.async_status()


class ProscenicStartStopButton(ProscenicAirFryerEntity, ButtonEntity):
    """Send the T21 start/pause command."""

    _attr_icon = "mdi:play-pause"
    _attr_name = "Start/Pause Cooking"

    def __init__(self, coordinator: ProscenicAirFryerCoordinator) -> None:
        """Initialize the button."""
        super().__init__(coordinator, "start_stop")

    async def async_press(self) -> None:
        """Send the pulse-style start/pause datapoint."""
        await self.coordinator.async_set_start_pause(True)

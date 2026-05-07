"""Select entities for Proscenic air fryers."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MODE_OPTIONS
from .coordinator import ProscenicAirFryerCoordinator
from .entity import ProscenicAirFryerEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Proscenic air fryer selects."""
    coordinator: ProscenicAirFryerCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ProscenicModeSelect(coordinator)])


class ProscenicModeSelect(ProscenicAirFryerEntity, SelectEntity):
    """Mode/preset selector."""

    _attr_icon = "mdi:silverware-fork-knife"
    _attr_name = "Mode"
    _attr_options = list(MODE_OPTIONS.values())

    def __init__(self, coordinator: ProscenicAirFryerCoordinator) -> None:
        """Initialize the select."""
        super().__init__(coordinator, "mode_select")

    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        mode = self.coordinator.data.mode
        return MODE_OPTIONS.get(mode, mode)

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        reverse = {name: value for value, name in MODE_OPTIONS.items()}
        await self.coordinator.async_set_mode(reverse[option])

"""Proscenic air fryer integration."""

from __future__ import annotations

import importlib

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import ProscenicAirFryerCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Proscenic air fryer from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    coordinator = ProscenicAirFryerCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.async_add_executor_job(_import_platforms)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await coordinator.async_config_entry_first_refresh()
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Proscenic air fryer config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: ProscenicAirFryerCoordinator | None = hass.data[DOMAIN].pop(
            entry.entry_id,
            None,
        )
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


def _import_platforms() -> None:
    """Import platform modules outside the event loop."""
    package = __package__
    for platform in PLATFORMS:
        importlib.import_module(f"{package}.{platform.value}")

"""Local Tuya coordinator for Proscenic air fryers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .client import ProscenicLocalTuyaClient
from .const import (
    CONF_DEVICE_ID,
    CONF_HOST,
    CONF_LOCAL_KEY,
    CONF_PROTOCOL_VERSION,
    CONF_TEMPERATURE_UNIT,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DEFAULT_TEMPERATURE_UNIT,
    DOMAIN,
    DP_COOK_TEMP,
    DP_COOK_TIME,
    DP_DELAYED_COOK,
    DP_DELAYED_TIME,
    DP_KEEP_WARM,
    DP_MODE,
    DP_POT_PULLED,
    DP_POWER,
    DP_REMAINING_TIME,
    DP_START,
    DP_STATUS,
    DP_TEMPERATURE_UNIT,
    DP_UNKNOWN_107,
    DP_WARM_TIME,
)

LOGGER = logging.getLogger(__name__)


@dataclass
class ProscenicAirFryerData:
    """Normalized air fryer state."""

    power: bool | None = None
    start_pause: bool | None = None
    keep_warm: bool | None = None
    delayed_cook: bool | None = None
    mode: str | None = None
    status: str | None = None
    cooking_temperature: int | None = None
    cooking_time: int | None = None
    remaining_time: int | None = None
    warm_time: int | None = None
    delayed_time: int | None = None
    pot_pulled: bool | None = None
    temperature_unit_flag: bool | None = None
    unknown_107: int | None = None
    last_update: datetime | None = None
    raw: dict[str, Any] = field(default_factory=dict)


class ProscenicAirFryerCoordinator(DataUpdateCoordinator[ProscenicAirFryerData]):
    """Coordinate local Tuya state and commands for a Proscenic air fryer."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL_SECONDS),
        )
        self.entry = entry
        self.data = ProscenicAirFryerData()
        self._client = ProscenicLocalTuyaClient(
            str(entry.data[CONF_DEVICE_ID]),
            str(entry.data[CONF_HOST]),
            str(entry.data[CONF_LOCAL_KEY]),
            str(entry.data[CONF_PROTOCOL_VERSION]),
        )

    @property
    def config(self) -> dict[str, Any]:
        """Return merged entry data and options."""
        return {**self.entry.data, **self.entry.options}

    @property
    def temperature_unit(self) -> str:
        """Return the unit used by the fryer datapoint."""
        return str(self.config.get(CONF_TEMPERATURE_UNIT, DEFAULT_TEMPERATURE_UNIT))

    async def _async_update_data(self) -> ProscenicAirFryerData:
        """Fetch latest state from the fryer."""
        raw = await self.hass.async_add_executor_job(self._client.status)
        return _normalize(raw)

    async def async_set_power(self, on: bool) -> None:
        """Set the air fryer power."""
        await self._set_dp(DP_POWER, on)

    async def async_set_start_pause(self, on: bool) -> None:
        """Start or stop/pause cooking."""
        await self._set_dp(DP_START, on)

    async def async_set_keep_warm(self, on: bool) -> None:
        """Enable or disable keep warm."""
        await self._set_dp(DP_KEEP_WARM, on)

    async def async_set_delayed_cook(self, on: bool) -> None:
        """Enable or disable delayed cook."""
        await self._set_dp(DP_DELAYED_COOK, on)

    async def async_set_mode(self, value: str) -> None:
        """Set cooking mode/preset."""
        await self._set_dp(DP_MODE, value)

    async def async_set_cooking_temperature(self, value: int) -> None:
        """Set cooking temperature."""
        await self._set_dp(DP_COOK_TEMP, value)

    async def async_set_cooking_time(self, value: int) -> None:
        """Set cooking time in minutes."""
        await self._set_dp(DP_COOK_TIME, value)

    async def async_set_warm_time(self, value: int) -> None:
        """Set keep-warm time in minutes."""
        await self._set_dp(DP_WARM_TIME, value)

    async def async_set_delayed_time(self, value: int) -> None:
        """Set delayed cook time in minutes."""
        await self._set_dp(DP_DELAYED_TIME, value)

    async def async_status(self) -> None:
        """Request a fresh status snapshot."""
        await self.async_request_refresh()

    async def _set_dp(self, dp_id: str, value: Any) -> None:
        """Set one datapoint and refresh state."""
        await self.hass.async_add_executor_job(self._client.set_dp, dp_id, value)
        await self.async_request_refresh()


def _normalize(raw: dict[str, Any]) -> ProscenicAirFryerData:
    """Normalize Tuya DPS values into coordinator data."""
    return ProscenicAirFryerData(
        power=_bool(raw.get(DP_POWER)),
        start_pause=_bool(raw.get(DP_START)),
        keep_warm=_bool(raw.get(DP_KEEP_WARM)),
        delayed_cook=_bool(raw.get(DP_DELAYED_COOK)),
        mode=_str(raw.get(DP_MODE)),
        status=_str(raw.get(DP_STATUS)),
        cooking_temperature=_int(raw.get(DP_COOK_TEMP)),
        cooking_time=_int(raw.get(DP_COOK_TIME)),
        remaining_time=_int(raw.get(DP_REMAINING_TIME)),
        warm_time=_int(raw.get(DP_WARM_TIME)),
        delayed_time=_int(raw.get(DP_DELAYED_TIME)),
        pot_pulled=_bool(raw.get(DP_POT_PULLED)),
        temperature_unit_flag=_bool(raw.get(DP_TEMPERATURE_UNIT)),
        unknown_107=_int(raw.get(DP_UNKNOWN_107)),
        last_update=datetime.now(UTC),
        raw=raw,
    )


def _bool(value: Any) -> bool | None:
    """Return a bool if the value is boolean-like."""
    return value if isinstance(value, bool) else None


def _int(value: Any) -> int | None:
    """Return an int if possible."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _str(value: Any) -> str | None:
    """Return a string if present."""
    return str(value) if value is not None else None

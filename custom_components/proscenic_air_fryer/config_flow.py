"""Config flow for Proscenic air fryers."""

from __future__ import annotations

from ipaddress import ip_network
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import section

from .client import (
    ProscenicApiError,
    ProscenicAuthenticationError,
    ProscenicDiscoveryError,
    ProscenicLocalError,
    discover_local_device,
    fetch_oem_device,
    scan_local_device,
    test_local_device,
)
from .const import (
    CONF_DEVICE_ID,
    CONF_DISCOVERY_METHOD,
    CONF_HOST,
    CONF_LOCAL_KEY,
    CONF_PASSWORD,
    CONF_PROTOCOL_VERSION,
    CONF_REGION,
    CONF_SCAN_SUBNET,
    CONF_TEMPERATURE_UNIT,
    CONF_USERNAME,
    DEFAULT_DISCOVERY_METHOD,
    DEFAULT_PROTOCOL_VERSION,
    DEFAULT_REGION,
    DEFAULT_TEMPERATURE_UNIT,
    DOMAIN,
)

REGIONS = ["eu", "us", "cn", "in"]
PROTOCOL_VERSIONS = ["3.3", "3.4", "3.5"]
DISCOVERY_METHODS = ["broadcast", "subnet"]
CONF_ADVANCED_OPTIONS = "advanced_options"


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return the setup schema."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_USERNAME,
                default=defaults.get(CONF_USERNAME, ""),
            ): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Optional(CONF_HOST, default=defaults.get(CONF_HOST, "")): str,
            vol.Optional(
                CONF_ADVANCED_OPTIONS,
                default={},
            ): section(
                vol.Schema(
                    {
                        vol.Optional(
                            CONF_DEVICE_ID,
                            default=defaults.get(CONF_DEVICE_ID, ""),
                        ): str,
                        vol.Optional(
                            CONF_LOCAL_KEY,
                            default=defaults.get(CONF_LOCAL_KEY, ""),
                        ): str,
                        vol.Optional(
                            CONF_DISCOVERY_METHOD,
                            default=defaults.get(
                                CONF_DISCOVERY_METHOD,
                                DEFAULT_DISCOVERY_METHOD,
                            ),
                        ): vol.In(DISCOVERY_METHODS),
                        vol.Optional(
                            CONF_SCAN_SUBNET,
                            default=defaults.get(CONF_SCAN_SUBNET, ""),
                        ): str,
                        vol.Optional(
                            CONF_REGION,
                            default=defaults.get(CONF_REGION, DEFAULT_REGION),
                        ): vol.In(REGIONS),
                        vol.Optional(
                            CONF_PROTOCOL_VERSION,
                            default=defaults.get(
                                CONF_PROTOCOL_VERSION,
                                DEFAULT_PROTOCOL_VERSION,
                            ),
                        ): vol.In(PROTOCOL_VERSIONS),
                        vol.Optional(
                            CONF_TEMPERATURE_UNIT,
                            default=defaults.get(
                                CONF_TEMPERATURE_UNIT,
                                DEFAULT_TEMPERATURE_UNIT,
                            ),
                        ): vol.In(["F", "C"]),
                    }
                ),
                {"collapsed": True},
            ),
        }
    )


def _options_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Return the options schema."""
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, "")): str,
            vol.Required(CONF_LOCAL_KEY, default=defaults.get(CONF_LOCAL_KEY, "")): str,
            vol.Required(
                CONF_DISCOVERY_METHOD,
                default=defaults.get(CONF_DISCOVERY_METHOD, DEFAULT_DISCOVERY_METHOD),
            ): vol.In(DISCOVERY_METHODS),
            vol.Optional(CONF_SCAN_SUBNET, default=defaults.get(CONF_SCAN_SUBNET, "")): str,
            vol.Required(
                CONF_PROTOCOL_VERSION,
                default=defaults.get(CONF_PROTOCOL_VERSION, DEFAULT_PROTOCOL_VERSION),
            ): vol.In(PROTOCOL_VERSIONS),
            vol.Required(
                CONF_TEMPERATURE_UNIT,
                default=defaults.get(CONF_TEMPERATURE_UNIT, DEFAULT_TEMPERATURE_UNIT),
            ): vol.In(["F", "C"]),
        }
    )


class ProscenicAirFryerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Proscenic air fryers."""

    VERSION = 2

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            data = _clean_input(user_input)
            try:
                entry_data = await self.hass.async_add_executor_job(_resolve_setup, data)
            except ProscenicAuthenticationError:
                errors["base"] = "invalid_auth"
            except ProscenicDiscoveryError:
                errors["base"] = "cannot_discover"
            except ProscenicLocalError:
                errors["base"] = "cannot_connect"
            except ProscenicApiError:
                errors["base"] = "cannot_fetch_key"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(entry_data[CONF_DEVICE_ID])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=entry_data.get("name", "Proscenic Air Fryer"),
                    data=entry_data,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> ProscenicAirFryerOptionsFlow:
        """Return the options flow."""
        return ProscenicAirFryerOptionsFlow(config_entry)


class ProscenicAirFryerOptionsFlow(config_entries.OptionsFlow):
    """Handle Proscenic air fryer options."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.entry = entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Manage options."""
        current = {**self.entry.data, **self.entry.options}
        errors: dict[str, str] = {}
        if user_input is not None:
            data = _clean_input({**current, **user_input})
            try:
                if not data[CONF_HOST]:
                    discovered = await self.hass.async_add_executor_job(
                        _discover_local_device,
                        self.entry.data[CONF_DEVICE_ID],
                        data[CONF_LOCAL_KEY],
                        data[CONF_DISCOVERY_METHOD],
                        data.get(CONF_SCAN_SUBNET) or None,
                    )
                    if discovered is None:
                        raise ProscenicDiscoveryError(
                            "Could not discover Tuya device"
                        )
                    data[CONF_HOST] = discovered.host
                await self.hass.async_add_executor_job(
                    test_local_device,
                    self.entry.data[CONF_DEVICE_ID],
                    data[CONF_HOST],
                    data[CONF_LOCAL_KEY],
                    data[CONF_PROTOCOL_VERSION],
                )
            except ProscenicDiscoveryError:
                errors["base"] = "cannot_discover"
            except ProscenicLocalError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_HOST: data[CONF_HOST],
                        CONF_LOCAL_KEY: data[CONF_LOCAL_KEY],
                        CONF_DISCOVERY_METHOD: data[CONF_DISCOVERY_METHOD],
                        CONF_SCAN_SUBNET: data.get(CONF_SCAN_SUBNET),
                        CONF_PROTOCOL_VERSION: data[CONF_PROTOCOL_VERSION],
                        CONF_TEMPERATURE_UNIT: data[CONF_TEMPERATURE_UNIT],
                    },
                )

        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(current),
            errors=errors,
        )


def _resolve_setup(data: dict[str, Any]) -> dict[str, Any]:
    """Resolve setup data, fetching a local key when needed."""
    device_id = data.get(CONF_DEVICE_ID) or None
    local_key = data.get(CONF_LOCAL_KEY) or None
    device = None
    if not local_key:
        device = fetch_oem_device(
            data[CONF_REGION],
            data[CONF_USERNAME],
            data[CONF_PASSWORD],
            device_id,
        )
        device_id = device.device_id
        local_key = device.local_key
    if not device_id or not local_key:
        raise ProscenicApiError("Device ID and local key are required")

    discovered = None
    if not data[CONF_HOST]:
        discovered = _discover_local_device(
            device_id,
            local_key,
            data[CONF_DISCOVERY_METHOD],
            data.get(CONF_SCAN_SUBNET) or None,
        )
        if discovered is None:
            raise ProscenicDiscoveryError(
                f"Could not discover Tuya device {device_id}"
            )
        data[CONF_HOST] = discovered.host

    raw_status = test_local_device(
        device_id,
        data[CONF_HOST],
        local_key,
        data[CONF_PROTOCOL_VERSION],
    )
    return {
        CONF_DEVICE_ID: device_id,
        CONF_HOST: data[CONF_HOST],
        CONF_LOCAL_KEY: local_key,
        CONF_DISCOVERY_METHOD: data[CONF_DISCOVERY_METHOD],
        CONF_SCAN_SUBNET: data.get(CONF_SCAN_SUBNET),
        CONF_PROTOCOL_VERSION: data[CONF_PROTOCOL_VERSION],
        CONF_REGION: data[CONF_REGION],
        CONF_TEMPERATURE_UNIT: data[CONF_TEMPERATURE_UNIT],
        CONF_USERNAME: data[CONF_USERNAME],
        "name": device.name if device else f"Proscenic {device_id[-6:]}",
        "category": device.category if device else None,
        "uuid": device.uuid if device else None,
        "product_id": device.product_id if device else None,
        "initial_dps": raw_status,
        "discovery": discovered.raw if discovered else None,
    }


def _clean_input(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize user input."""
    cleaned = {
        CONF_REGION: DEFAULT_REGION,
        CONF_DISCOVERY_METHOD: DEFAULT_DISCOVERY_METHOD,
        CONF_PROTOCOL_VERSION: DEFAULT_PROTOCOL_VERSION,
        CONF_TEMPERATURE_UNIT: DEFAULT_TEMPERATURE_UNIT,
        **data,
        **(data.get(CONF_ADVANCED_OPTIONS) or {}),
    }
    cleaned.pop(CONF_ADVANCED_OPTIONS, None)
    for key in (
        CONF_USERNAME,
        CONF_PASSWORD,
        CONF_HOST,
        CONF_DEVICE_ID,
        CONF_LOCAL_KEY,
        CONF_DISCOVERY_METHOD,
        CONF_REGION,
        CONF_SCAN_SUBNET,
        CONF_PROTOCOL_VERSION,
        CONF_TEMPERATURE_UNIT,
    ):
        if key in cleaned and isinstance(cleaned[key], str):
            cleaned[key] = cleaned[key].strip()
    return cleaned


def _discover_local_device(
    device_id: str,
    local_key: str,
    discovery_method: str,
    scan_subnet: str | None,
):
    """Discover a local Tuya device using the selected method."""
    if discovery_method == "subnet":
        if not scan_subnet:
            raise ProscenicDiscoveryError("Scan subnet is required")
        try:
            ip_network(scan_subnet, strict=False)
        except ValueError as err:
            raise ProscenicDiscoveryError("Scan subnet is invalid") from err
        return scan_local_device(device_id, local_key, scan_subnet)
    return discover_local_device(device_id)

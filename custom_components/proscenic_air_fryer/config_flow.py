"""Config flow for Proscenic air fryers."""

from __future__ import annotations

from ipaddress import ip_network
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig

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
    CONF_MAC_ADDRESS,
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
DISCOVERY_METHOD_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[
            {
                "value": "broadcast",
                "label": "Broadcast - listen for Tuya LAN announcements",
            },
            {
                "value": "subnet",
                "label": "Subnet scan - scan a CIDR range",
            },
        ]
    )
)
CONF_ADVANCED_OPTIONS = "advanced_options"


def _cloud_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return the cloud setup schema."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_USERNAME,
                default=defaults.get(CONF_USERNAME, ""),
            ): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Optional(CONF_HOST, default=defaults.get(CONF_HOST, "")): str,
            vol.Optional(CONF_ADVANCED_OPTIONS): section(
                vol.Schema(
                    {
                        vol.Optional(
                            CONF_DISCOVERY_METHOD,
                            default=defaults.get(
                                CONF_DISCOVERY_METHOD,
                                DEFAULT_DISCOVERY_METHOD,
                            ),
                        ): DISCOVERY_METHOD_SELECTOR,
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


def _manual_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return the manual local setup schema."""
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_DEVICE_ID,
                default=defaults.get(CONF_DEVICE_ID, ""),
            ): str,
            vol.Required(
                CONF_LOCAL_KEY,
                default=defaults.get(CONF_LOCAL_KEY, ""),
            ): str,
            vol.Optional(CONF_HOST, default=defaults.get(CONF_HOST, "")): str,
            vol.Optional(CONF_ADVANCED_OPTIONS): section(
                vol.Schema(
                    {
                        vol.Optional(
                            CONF_DISCOVERY_METHOD,
                            default=defaults.get(
                                CONF_DISCOVERY_METHOD,
                                DEFAULT_DISCOVERY_METHOD,
                            ),
                        ): DISCOVERY_METHOD_SELECTOR,
                        vol.Optional(
                            CONF_SCAN_SUBNET,
                            default=defaults.get(CONF_SCAN_SUBNET, ""),
                        ): str,
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
            vol.Required(
                CONF_USERNAME,
                default=defaults.get(CONF_USERNAME, ""),
            ): str,
            vol.Optional(CONF_PASSWORD): str,
            vol.Required(
                CONF_TEMPERATURE_UNIT,
                default=defaults.get(
                    CONF_TEMPERATURE_UNIT,
                    DEFAULT_TEMPERATURE_UNIT,
                ),
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
        """Choose the setup method."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["cloud", "manual"],
        )

    async def async_step_cloud(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Set up using Proscenic cloud lookup."""
        return await self._async_step_setup(
            user_input,
            step_id="cloud",
            schema_fn=_cloud_schema,
        )

    async def async_step_manual(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Set up using manually supplied local Tuya parameters."""
        return await self._async_step_setup(
            user_input,
            step_id="manual",
            schema_fn=_manual_schema,
        )

    async def async_step_dhcp(
        self,
        discovery_info: Any,
    ) -> config_entries.ConfigFlowResult:
        """Handle a DHCP discovered fryer candidate."""
        host = getattr(discovery_info, "ip", None)
        mac_address = _normalize_mac(getattr(discovery_info, "macaddress", None))
        hostname = getattr(discovery_info, "hostname", None)
        self.context["title_placeholders"] = {
            "name": hostname or host or "Proscenic Air Fryer"
        }
        if mac_address:
            await self.async_set_unique_id(mac_address)
            self._abort_if_unique_id_configured(updates={CONF_HOST: host})

        defaults = {
            CONF_HOST: host or "",
            CONF_MAC_ADDRESS: mac_address or "",
            CONF_DISCOVERY_METHOD: DEFAULT_DISCOVERY_METHOD,
        }
        return await self._async_step_setup(
            None,
            defaults=defaults,
            step_id="cloud",
            schema_fn=_cloud_schema,
        )

    async def _async_step_setup(
        self,
        user_input: dict[str, Any] | None,
        defaults: dict[str, Any] | None = None,
        step_id: str = "cloud",
        schema_fn=_cloud_schema,
    ) -> config_entries.ConfigFlowResult:
        """Handle setup from user or discovery."""
        errors: dict[str, str] = {}
        if user_input is not None:
            data = _clean_input({**(defaults or {}), **user_input})
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

        schema_defaults = {**(defaults or {}), **(user_input or {})}
        return self.async_show_form(
            step_id=step_id,
            data_schema=schema_fn(schema_defaults),
            errors=errors,
            description_placeholders={
                "host": schema_defaults.get(CONF_HOST, ""),
            },
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
                options = await self.hass.async_add_executor_job(
                    _resolve_options,
                    self.entry.data,
                    data,
                )
                await self.hass.async_add_executor_job(
                    test_local_device,
                    options[CONF_DEVICE_ID],
                    options[CONF_HOST],
                    options[CONF_LOCAL_KEY],
                    options[CONF_PROTOCOL_VERSION],
                )
            except ProscenicAuthenticationError:
                errors["base"] = "invalid_auth"
            except ProscenicApiError:
                errors["base"] = "cannot_fetch_key"
            except ProscenicLocalError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title="",
                    data=options,
                )

        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(current),
            errors=errors,
        )


def _resolve_options(
    entry_data: dict[str, Any],
    data: dict[str, Any],
) -> dict[str, Any]:
    """Resolve options, refreshing cloud-derived values only when requested."""
    local_key = str(data.get(CONF_LOCAL_KEY) or entry_data[CONF_LOCAL_KEY])
    device_id = str(data.get(CONF_DEVICE_ID) or entry_data[CONF_DEVICE_ID])
    options: dict[str, Any] = {
        CONF_HOST: data[CONF_HOST],
        CONF_DEVICE_ID: device_id,
        CONF_USERNAME: data[CONF_USERNAME],
        CONF_LOCAL_KEY: local_key,
        CONF_REGION: data.get(CONF_REGION) or entry_data.get(CONF_REGION, DEFAULT_REGION),
        CONF_PROTOCOL_VERSION: data.get(CONF_PROTOCOL_VERSION) or entry_data.get(
            CONF_PROTOCOL_VERSION,
            DEFAULT_PROTOCOL_VERSION,
        ),
        CONF_TEMPERATURE_UNIT: data[CONF_TEMPERATURE_UNIT],
    }
    if data.get(CONF_PASSWORD):
        try:
            device = fetch_oem_device(
                options[CONF_REGION],
                data[CONF_USERNAME],
                data[CONF_PASSWORD],
                device_id,
            )
        except ProscenicApiError as err:
            if "was not found" not in str(err):
                raise
            device = fetch_oem_device(
                options[CONF_REGION],
                data[CONF_USERNAME],
                data[CONF_PASSWORD],
                None,
            )
        options.update(
            {
                CONF_DEVICE_ID: device.device_id,
                CONF_LOCAL_KEY: device.local_key,
                "name": device.name,
                "category": device.category,
                "uuid": device.uuid,
                "product_id": device.product_id,
                "cloud_dps": device.dps,
            }
        )
    return options


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
        CONF_MAC_ADDRESS: data.get(CONF_MAC_ADDRESS),
        CONF_PROTOCOL_VERSION: data[CONF_PROTOCOL_VERSION],
        CONF_REGION: data[CONF_REGION],
        CONF_TEMPERATURE_UNIT: data[CONF_TEMPERATURE_UNIT],
        CONF_USERNAME: data.get(CONF_USERNAME),
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
        CONF_MAC_ADDRESS,
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


def _normalize_mac(value: Any) -> str | None:
    """Normalize a MAC address to Home Assistant connection format."""
    if not value:
        return None
    text = str(value).lower().replace("-", ":")
    if ":" not in text and len(text) == 12:
        text = ":".join(text[index : index + 2] for index in range(0, 12, 2))
    return text

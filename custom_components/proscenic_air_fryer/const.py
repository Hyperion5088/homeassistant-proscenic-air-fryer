"""Constants for the Proscenic air fryer integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "proscenic_air_fryer"

CONF_DEVICE_ID = "device_id"
CONF_HOST = "host"
CONF_LOCAL_KEY = "local_key"
CONF_PASSWORD = "password"
CONF_PROTOCOL_VERSION = "protocol_version"
CONF_REGION = "region"
CONF_TEMPERATURE_UNIT = "temperature_unit"
CONF_USERNAME = "username"

DEFAULT_PROTOCOL_VERSION = "3.3"
DEFAULT_REGION = "eu"
DEFAULT_TEMPERATURE_UNIT = "F"
DEFAULT_SCAN_INTERVAL_SECONDS = 15

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
]

STATUS_OPTIONS = {
    "off": "Off",
    "standby": "Standby",
    "stop": "Stopped",
    "cooking": "Cooking",
    "appointment": "Delayed",
    "warm": "Keep warm",
    "end": "Complete",
}

DP_POWER = "1"
DP_START = "2"
DP_MODE = "3"
DP_STATUS = "5"
DP_DELAYED_TIME = "6"
DP_COOK_TIME = "7"
DP_REMAINING_TIME = "8"
DP_POT_PULLED = "102"
DP_COOK_TEMP = "103"
DP_KEEP_WARM = "104"
DP_WARM_TIME = "105"
DP_DELAYED_COOK = "106"
DP_UNKNOWN_107 = "107"
DP_TEMPERATURE_UNIT = "108"

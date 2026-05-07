"""Clients for Proscenic OEM cloud lookup and local Tuya control."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import time
from typing import Any

import requests
import tinytuya

PROSCENIC_CLIENT_ID = "ja9ntfcxcs8qg5sqdcfm"
PROSCENIC_SECRET = (
    "A_4vgq3tcqnam9drtvgam8hneqjprtjnf4_c5rkn5tga889whe5cd7pc9j387knwsuc"
)
TUYA_USER_AGENT = "TY-UA=APP/Android/1.1.6/SDK/null"
TUYA_API_VERSION = "1.0"


class ProscenicApiError(Exception):
    """Base error for Proscenic API calls."""


class ProscenicAuthenticationError(ProscenicApiError):
    """Raised when Proscenic credentials are invalid."""


class ProscenicLocalError(Exception):
    """Raised when local Tuya communication fails."""


@dataclass
class ProscenicDevice:
    """Device details returned by the Proscenic OEM Tuya API."""

    name: str
    device_id: str
    local_key: str
    category: str | None
    uuid: str | None
    product_id: str | None
    dps: dict[str, Any]


class ProscenicOemCloud:
    """Minimal Proscenic OEM Tuya cloud client.

    This follows the public-domain tuya-uncover flow for OEM apps. It is used
    only during setup to fetch the local key; runtime control is local.
    """

    def __init__(self, region: str, username: str, password: str) -> None:
        """Initialize the cloud client."""
        self._endpoint = f"https://a1.tuya{region}.com/api.json"
        self._username = username
        self._password = password
        self._session = requests.Session()
        self._sid: str | None = None

    def login(self) -> None:
        """Log in to the Proscenic OEM Tuya API."""
        token_info = self._api(
            "tuya.m.user.email.token.create",
            {"countryCode": "", "email": self._username},
            requires_sid=False,
        )
        login_info = self._api(
            "tuya.m.user.email.password.login",
            {
                "countryCode": "",
                "email": self._username,
                "ifencrypt": 1,
                "options": '{"group": 1}',
                "passwd": self._encrypt_password(
                    token_info["publicKey"],
                    token_info["exponent"],
                    self._password,
                ),
                "token": token_info["token"],
            },
            requires_sid=False,
        )
        self._sid = login_info["sid"]

    def list_devices(self) -> list[ProscenicDevice]:
        """Return devices visible to this Proscenic account."""
        if self._sid is None:
            self.login()

        devices: list[ProscenicDevice] = []
        for group in self._api("tuya.m.location.list"):
            for dev in self._api(
                "tuya.m.my.group.device.list",
                extra_params={"gid": str(group["groupId"])},
            ):
                devices.append(
                    ProscenicDevice(
                        name=str(dev.get("name") or dev.get("devId")),
                        device_id=str(dev["devId"]),
                        local_key=str(dev["localKey"]),
                        category=dev.get("category"),
                        uuid=dev.get("uuid"),
                        product_id=dev.get("productId"),
                        dps={str(k): v for k, v in dict(dev.get("dps", {})).items()},
                    )
                )
        return devices

    def _api(
        self,
        action: str,
        payload: dict[str, Any] | None = None,
        extra_params: dict[str, str] | None = None,
        requires_sid: bool = True,
    ) -> Any:
        """Call one Tuya OEM API method."""
        params = {
            "a": action,
            "clientId": PROSCENIC_CLIENT_ID,
            "v": TUYA_API_VERSION,
            "time": str(int(time.time())),
            **(extra_params or {}),
        }
        if requires_sid:
            if self._sid is None:
                raise ProscenicApiError("Not logged in")
            params["sid"] = self._sid

        data = {}
        if payload is not None:
            data["postData"] = json.dumps(payload, separators=(",", ":"))
        params["sign"] = self._sign({**params, **data})

        response = self._session.post(
            self._endpoint,
            params=params,
            data=data,
            headers={"User-Agent": TUYA_USER_AGENT},
            timeout=20,
        )
        response.raise_for_status()
        return self._handle_response(response.json())

    def _sign(self, data: dict[str, str]) -> str:
        """Create the OEM mobile API request signature."""
        parts = []
        for key in sorted(data):
            if key == "gid":
                continue
            value = self._mobile_hash(data[key]) if key == "postData" else data[key]
            parts.append(f"{key}={value}")
        return hmac.new(
            PROSCENIC_SECRET.encode(),
            msg="||".join(parts).encode(),
            digestmod=hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _handle_response(result: dict[str, Any]) -> Any:
        """Extract a Tuya API response or raise a useful error."""
        if result.get("success"):
            return result.get("result")
        code = result.get("errorCode")
        message = result.get("errorMsg") or result.get("msg") or "Unknown Tuya API error"
        if code in {"USER_PASSWD_WRONG", "USER_NOT_EXIST"}:
            raise ProscenicAuthenticationError(message)
        raise ProscenicApiError(f"{message} ({code})")

    @staticmethod
    def _mobile_hash(data: str) -> str:
        prehash = hashlib.md5(data.encode()).hexdigest()
        return prehash[8:16] + prehash[0:8] + prehash[24:32] + prehash[16:24]

    @staticmethod
    def _encrypt_password(modulus: str, exponent: str, password: str) -> str:
        passwd_hash = hashlib.md5(password.encode()).hexdigest().encode()
        enc_message_int = pow(
            int.from_bytes(passwd_hash, "big"),
            int(exponent),
            int(modulus),
        )
        return enc_message_int.to_bytes(256, "big").hex()


class ProscenicLocalTuyaClient:
    """Local Tuya client for the Proscenic T21."""

    def __init__(self, device_id: str, host: str, local_key: str, version: str) -> None:
        """Initialize the local client."""
        self._device_id = device_id
        self._host = host
        self._local_key = local_key
        self._version = float(version)

    def status(self) -> dict[str, Any]:
        """Return local DPS status."""
        result = self._device().status()
        if "dps" not in result:
            raise ProscenicLocalError(str(result))
        return {str(k): v for k, v in result["dps"].items()}

    def set_dp(self, dp_id: str, value: Any) -> dict[str, Any]:
        """Set one datapoint."""
        result = self._device().set_value(int(dp_id), value)
        if isinstance(result, dict) and result.get("Err"):
            raise ProscenicLocalError(str(result))
        return result if isinstance(result, dict) else {"result": result}

    def _device(self) -> tinytuya.Device:
        """Create a TinyTuya device object."""
        device = tinytuya.Device(self._device_id, self._host, self._local_key)
        device.set_version(self._version)
        device.set_socketTimeout(10)
        return device


def fetch_oem_device(
    region: str,
    username: str,
    password: str,
    device_id: str | None = None,
) -> ProscenicDevice:
    """Fetch a Proscenic device and local key from user credentials."""
    devices = ProscenicOemCloud(region, username, password).list_devices()
    if not devices:
        raise ProscenicApiError("No Proscenic devices found")
    if device_id:
        for device in devices:
            if device.device_id == device_id:
                return device
        raise ProscenicApiError(f"Device {device_id} was not found")
    return devices[0]


def test_local_device(device_id: str, host: str, local_key: str, version: str) -> dict[str, Any]:
    """Read local status from a device."""
    return ProscenicLocalTuyaClient(device_id, host, local_key, version).status()

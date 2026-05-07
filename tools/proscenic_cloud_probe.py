#!/usr/bin/env python3
"""Probe ProscenicHome cloud account/device metadata.

This script only logs in and lists devices. It does not send appliance control
commands.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from typing import Any

import aiohttp

HOSTS = {
    "US": "mobile.proscenic.tw",
    "EU": "mobile.proscenic.com.de",
    "CN": "mobile.proscenic.cn",
}


async def main() -> int:
    """Run the probe."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", choices=sorted(HOSTS), default=os.getenv("PROSCENIC_REGION", "EU"))
    parser.add_argument("--username", default=os.getenv("PROSCENIC_USERNAME"))
    parser.add_argument("--password", default=os.getenv("PROSCENIC_PASSWORD"))
    parser.add_argument("--raw", action="store_true", help="Print full raw JSON responses")
    args = parser.parse_args()

    if not args.username or not args.password:
        print(
            "Set PROSCENIC_USERNAME and PROSCENIC_PASSWORD, or pass --username/--password.",
            file=sys.stderr,
        )
        return 2

    host = HOSTS[args.region]
    base_url = f"https://{host}"
    async with aiohttp.ClientSession() as session:
        login = await request_json(
            session,
            "POST",
            f"{base_url}/user/login",
            headers=login_headers(host),
            data=json.dumps(login_payload(args.username, args.password)).encode(),
        )
        print_response("login", login, args.raw)
        token = nested_get(login, "data", "token")
        if not token:
            print("No token returned; cannot list devices.", file=sys.stderr)
            return 1

        devices = await request_json(
            session,
            "POST",
            f"{base_url}/user/getEquips/{args.username}",
            headers={"token": token},
            data={"username": args.username},
        )
        print_response("devices", devices, args.raw)
        content = nested_get(devices, "data", "content") or []
        print("\nDevices:")
        for index, device in enumerate(content, start=1):
            print(f"{index}. {summarize_device(device)}")
        if not content:
            print("No devices returned.")
    return 0


async def request_json(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    **kwargs: Any,
) -> dict[str, Any]:
    """Send a request and decode JSON."""
    async with session.request(method, url, **kwargs) as response:
        text = await response.text()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {
                "http_status": response.status,
                "raw": text,
            }


def login_headers(host: str) -> dict[str, str]:
    """Return ProscenicHome-style login headers."""
    return {
        "os": "i",
        "Content-Type": "application/json",
        "c": "338",
        "lan": "en",
        "Host": host,
        "User-Agent": "ProscenicHome/1.7.8 (iPhone; iOS 14.2.1; Scale/3.00)",
        "v": "1.7.8",
    }


def login_payload(username: str, password: str) -> dict[str, str]:
    """Return the login payload used by known ProscenicHome clients."""
    password_hash = hashlib.md5(password.encode("utf-8")).hexdigest()
    return {
        "state": "欧洲",
        "countryCode": "49",
        "appVer": "1.7.8",
        "type": "2",
        "os": "IOS",
        "password": password_hash,
        "registrationId": "13165ffa4eb156ac484",
        "language": "EN",
        "username": username,
        "pwd": password,
    }


def nested_get(value: dict[str, Any], *keys: str) -> Any:
    """Return a nested dictionary value."""
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def print_response(name: str, response: dict[str, Any], raw: bool) -> None:
    """Print a response safely."""
    if raw:
        print(f"\n{name}:")
        print(json.dumps(redact(response), indent=2, sort_keys=True))
        return
    code = response.get("code", response.get("http_status", "unknown"))
    message = response.get("message") or response.get("msg") or response.get("error") or ""
    print(f"{name}: code={code} {message}".rstrip())


def summarize_device(device: dict[str, Any]) -> str:
    """Return a compact device summary."""
    fields = {
        "name": device.get("name"),
        "code": device.get("code"),
        "typeName": device.get("typeName"),
        "type": device.get("type"),
        "model": device.get("model"),
        "sn": device.get("sn"),
        "status": device.get("status"),
        "cloud": device.get("cloud"),
        "enabled": device.get("enabled"),
    }
    return ", ".join(f"{key}={value}" for key, value in fields.items() if value is not None)


def redact(value: Any) -> Any:
    """Redact likely secret values from printed JSON."""
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            if key.lower() in {"token", "password", "pwd"}:
                redacted[key] = "<redacted>"
            else:
                redacted[key] = redact(item)
        return redacted
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

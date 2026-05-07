# Proscenic Air Fryer for Home Assistant

**Beta status:** this integration is experimental. It has only been tested against one Proscenic T21 on the author's network. It may work with other Proscenic/Tuya air fryer models, but datapoints can vary by region, firmware, and model.

Custom Home Assistant integration for a stock Proscenic T21 air fryer. Other stock Proscenic/Tuya air fryers may work if they use the same local Tuya protocol and compatible datapoints.

The integration uses the Proscenic OEM Tuya account only during setup to fetch the device's local key. Runtime control is local over the Tuya LAN protocol.

## Setup

You need:

- Proscenic account email and password
- fryer IP address, or network/VLAN access for discovery
- Home Assistant network access to the fryer, usually TCP `6668`

During setup the password is used once to fetch the local key and is not stored in the config entry.
Leave the fryer IP address blank to discover the device. Broadcast discovery listens for Tuya LAN announcements on the local network. If broadcasts do not cross your VLANs, choose subnet scan in Advanced Options and enter a CIDR subnet such as `192.168.13.0/24`.

Known working T21 values:

- protocol: `3.3`
- product id: `ngdn90sk1yqmk9ww`
- Tuya category: `df`

## Compatibility

Tested:

- Proscenic T21

Potentially compatible:

- Other Proscenic/Tuya air fryers that expose the same or similar Tuya datapoints.

Untested models should be added cautiously. Start with read-only status, then verify harmless controls such as temperature and time before using power or start/stop.

## Branding

The repository includes HACS branding assets in `brand/` and Home Assistant local integration branding in `custom_components/proscenic_air_fryer/brand/`. Local custom integration branding is supported by Home Assistant Core 2026.3 and newer. Older Home Assistant versions may still show the generic integration icon unless the integration is added to the upstream Home Assistant brands repository.

## Exposed Controls

- power switch
- start cooking button
- keep warm switch
- delayed cook switch
- cooking temperature
- cooking time
- keep warm time
- delayed time
- preset selector
- status, mode, temperature, remaining time, and diagnostic sensors
- disabled-by-default diagnostic entities for device name, device ID, local key, category, product ID, UUID, initial DPS, protocol, region, discovery method, scan subnet, IP address, raw DPS, and unknown datapoints
- optional IP discovery by Tuya LAN broadcast or user-provided subnet scan

Starting a cooking appliance remotely has real-world safety implications. Use automations conservatively.

Known T21 behavior:

- The `Start Cooking` button sends the app's start datapoint. It did not reliably stop or pause an active cook in testing.
- Turning power off during cooking works as the current stop path.
- Preset temperature/time edits can be changed for the current session, but the fryer does not persist those edits back to the preset.

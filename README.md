# Proscenic Air Fryer for Home Assistant

**Compatibility status:** this integration has been tested against one Proscenic T21 on the author's network. It may work with other Proscenic/Tuya air fryer models, but datapoints can vary by region, firmware, and model.

Custom Home Assistant integration for a stock Proscenic T21 air fryer. Other stock Proscenic/Tuya air fryers may work if they use the same local Tuya protocol and compatible datapoints.

The integration uses the Proscenic OEM Tuya account only during setup to fetch the device's local key. Runtime control is local over the Tuya LAN protocol.

## Setup

You need:

- Proscenic account email and password
- fryer IP address, or network/VLAN access for discovery
- Home Assistant network access to the fryer, usually TCP `6668`

During setup the password is used once to fetch the local key and is not stored in the config entry.

The first setup page asks how you want to add the fryer:

- Cloud lookup: enter your Proscenic email/password. The integration fetches Device ID and Local Key from the Proscenic/Tuya cloud once, then controls the fryer locally. This is the normal setup path because those local Tuya values are not printed on the fryer.
- Manual local setup: enter Device ID and Local Key yourself. This path does not contact the Proscenic/Tuya cloud, but it only works if you already have those values, usually from a previous cloud lookup or another Tuya tool.

Both setup paths then use the same local connection choices:

- Manual IP setup: enter the fryer IP address if you know it. This avoids discovery and goes straight to a local connection test.
- Broadcast discovery: leave Fryer IP Address blank and leave Discovery Method as Broadcast. Home Assistant must be able to receive Tuya LAN UDP broadcasts from the fryer network.
- Subnet discovery: leave Fryer IP Address blank, choose Discovery Method `Subnet scan`, and enter the network in IP/CIDR format in Scan Subnet, for example `192.168.13.0/24`. This is useful when the fryer is on another VLAN and broadcasts do not cross VLANs.

Home Assistant can also start a setup flow from DHCP discovery for known Proscenic/Tuya fryer network hardware. In that case the fryer IP address is prefilled and you only need to provide the Proscenic account details so the integration can fetch the Local Key.

If the fryer is re-paired to Wi-Fi, Proscenic/Tuya may issue a new Device ID or Local Key. Open the integration options and enter the Proscenic password again to refresh the cloud-derived values. The password is used once for that refresh and is not stored.

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
- disabled-by-default numeric input box versions of the temperature and timer controls
- preset selector
- status, mode, temperature, remaining time, and diagnostic sensors
- disabled-by-default diagnostic entities for device name, device ID, local key, category, product ID, UUID, initial DPS, protocol, region, discovery method, scan subnet, IP address, raw DPS, and unknown datapoints
- optional IP discovery by Tuya LAN broadcast or user-provided subnet scan

Starting a cooking appliance remotely has real-world safety implications. Use automations conservatively.

Known T21 behavior:

- The `Start Cooking` button sends the app's start datapoint. It starts cooking even if the fryer previously reported power off.
- Pause has not worked reliably on the tested T21. Turning power off during cooking is the current stop path.
- Preset temperature/time edits can be changed for the current session, but the fryer does not persist those edits back to the preset.

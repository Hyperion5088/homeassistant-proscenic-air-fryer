# Proscenic Air Fryer for Home Assistant

**Beta status:** this integration is experimental. It has only been tested against one Proscenic T21 on the author's network. It may work with other Proscenic/Tuya air fryer models, but datapoints can vary by region, firmware, and model.

Custom Home Assistant integration for a stock Proscenic T21 air fryer. Other stock Proscenic/Tuya air fryers may work if they use the same local Tuya protocol and compatible datapoints.

The integration uses the Proscenic OEM Tuya account only during setup to fetch the device's local key. Runtime control is local over the Tuya LAN protocol.

## Setup

You need:

- Proscenic account email and password
- fryer IP address
- Home Assistant network access to the fryer, usually TCP `6668`

During setup the password is used once to fetch the local key and is not stored in the config entry.

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

## Exposed Controls

- power switch
- start/stop button
- keep warm switch
- delayed cook switch
- cooking temperature
- cooking time
- keep warm time
- delayed time
- status, raw mode, temperature, remaining time, and diagnostic sensors
- disabled-by-default diagnostic entities for device name, device ID, local key, category, product ID, UUID, initial DPS, protocol, region, IP address, raw DPS, and unknown datapoints

Starting a cooking appliance remotely has real-world safety implications. Use automations conservatively.

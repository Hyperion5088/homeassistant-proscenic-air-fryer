# Proscenic Air Fryer for Home Assistant

**Beta status:** this integration is experimental. It has been tested against one Proscenic T21 on the author's network, but the Proscenic/Tuya OEM API and datapoints may vary by region, firmware, and model.

Custom Home Assistant integration for a stock Proscenic T21-style air fryer.

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

## Exposed Controls

- power switch
- start/stop button
- keep warm switch
- delayed cook switch
- cooking temperature
- cooking time
- keep warm time
- delayed time
- mode/preset selector
- status, mode, temperature, remaining time, and diagnostic sensors

Starting a cooking appliance remotely has real-world safety implications. Use automations conservatively.

# Proscenic T21 Datapoints

These datapoints have only been verified against a Proscenic T21. Other Proscenic/Tuya air fryer models may use the same datapoints, but that is not guaranteed.

Source: Proscenic Android app `4.1.0`, package `com.proscenic.smart.robot`, class `com.proscenic.fryer.t21.T21HomeActivity`.

The current Proscenic app uses the Thingclips/Tuya device model internally. For the T21 fryer, `T21HomeActivity.sendOrder(code, value)` builds a map and calls `CommonDevicePresenter.publishDps(map)`.

## Observed DPs

| DP | Type | Meaning | Evidence |
| --- | --- | --- | --- |
| `1` | bool | Power | `turnOnAndOff(boolean)` publishes `1`; `freshViewsWithDps` stores it as `isOn`. |
| `2` | bool | Start control | `startCooking()` publishes `2=true`; testing confirmed this does not reliably stop or pause an active cook. |
| `3` | enum/string | Cooking mode / food preset | `freshViewsWithDps` stores it as `mode`; observed values are listed below. |
| `5` | enum/string | Working status | `freshViewsWithDps` stores it as `status`; examples include `off`, `stop`, `cooking`, `appointment`, `warm`, `end`. |
| `6` | integer | Appointment/delay time | `startCooking()` publishes appointment time when pre-cook is enabled. |
| `7` | integer | Cooking time | Time wheel publishes `7`; state stored as `cookingTime`. |
| `8` | integer | Remaining/last time | State stored as `lastTime`. |
| `12` | integer | Unknown standby/cooking state value | Observed as `0` while changing presets and cooking. Meaning not yet known. |
| `102` | bool | Pot/basket pulled or door/interlock state | `freshViewsWithDps` calls `potPull(boolean)`. |
| `103` | integer | Cooking temperature | Temperature wheel publishes `103`; state stored as `cookingTemperature`. |
| `104` | bool | Keep warm enabled | `startCooking()` publishes `104=true` when warm is enabled; power-off/status reset publishes `104=false`. |
| `105` | integer | Keep warm time | `startCooking()` publishes warm time as `105`; state stored as `warmTime`. |
| `106` | bool | Appointment/delay enabled | `startCooking()` publishes `106=true` when pre-cook is enabled; power-off/status reset publishes `106=false`. |
| `107` | integer | Unknown T21 state value | App reads the value but the extracted bytecode context did not reveal the UI meaning. |
| `108` | bool | Temperature unit | App stores it as `defaultUnit`, updates `FryerUtils.setTemperatureT31`, and swaps Celsius/Fahrenheit wheel data. |

## Control Notes

## Observed T21 Presets

| Mode code | App preset | Time | Temperature |
| --- | --- | --- | --- |
| `dbf1` | Manual | User-defined | User-defined |
| `dfb2` | Chips | 18 min | 400°F / 204°C |
| `dfb3` | Shrimp | 8 min | 360°F / 182°C |
| `dfb4` | Pizza | 7 min | 330°F / 166°C |
| `dfb5` | Chicken | 20 min | 360°F / 182°C |
| `dfb6` | Fish | 10 min | 400°F / 204°C |
| `dfb7` | Steaks | 8 min | 360°F / 182°C |
| `dfb8` | Cake | 12 min | 360°F / 182°C |
| `dfb9` | Streaky Meat | 12 min | 360°F / 182°C |
| `dfb10` | Preheat | 5 min | 370°F / 188°C |

The app sends these commands through `publishDps`, not through the older ProscenicHome `/instructions/...` endpoints.

Safe command candidates:

- power on/off: `{ "1": true/false }`
- set temperature: `{ "103": <fahrenheit integer> }`
- set cooking time: `{ "7": <minutes> }`
- enable/disable keep warm: `{ "104": true/false }`
- set keep warm time: `{ "105": <minutes> }`
- enable/disable delayed start: `{ "106": true/false }`
- set delayed start time: `{ "6": <minutes> }`

Potentially hazardous command:

- start cooking: `{ "2": true }`

Home Assistant exposes start cooking as an explicit button with clear naming, not as an automatically restored switch. Use DP1 power off as the tested stop path. Preset temperature/time edits are session-only and are not persisted back to the preset by the fryer.

## Remaining Unknowns

- The HTTP/MQTT/WebSocket route the Thingclips SDK uses for account login, device listing, and `publishDps`.
- Whether SDK certificate pinning blocks HTTPS interception.

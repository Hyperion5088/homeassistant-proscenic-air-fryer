# Proscenic T21 Datapoints

These datapoints have only been verified against a Proscenic T21. Other Proscenic/Tuya air fryer models may use the same datapoints, but that is not guaranteed.

Source: Proscenic Android app `4.1.0`, package `com.proscenic.smart.robot`, class `com.proscenic.fryer.t21.T21HomeActivity`.

The current Proscenic app uses the Thingclips/Tuya device model internally. For the T21 fryer, `T21HomeActivity.sendOrder(code, value)` builds a map and calls `CommonDevicePresenter.publishDps(map)`.

## Observed DPs

| DP | Type | Meaning | Evidence |
| --- | --- | --- | --- |
| `1` | bool | Power | `turnOnAndOff(boolean)` publishes `1`; `freshViewsWithDps` stores it as `isOn`. |
| `2` | bool | Start / stop / pause control | `turnStop()` publishes `2=true`; `startCooking()` publishes `2=true`; state is stored as `isStop`. |
| `3` | enum/string | Cooking mode / food preset | `freshViewsWithDps` stores it as `mode`; examples include `dbf1`, `dfb10`, `dfb11`. |
| `5` | enum/string | Working status | `freshViewsWithDps` stores it as `status`; examples include `off`, `stop`, `cooking`, `appointment`, `warm`, `end`. |
| `6` | integer | Appointment/delay time | `startCooking()` publishes appointment time when pre-cook is enabled. |
| `7` | integer | Cooking time | Time wheel publishes `7`; state stored as `cookingTime`. |
| `8` | integer | Remaining/last time | State stored as `lastTime`. |
| `102` | bool | Pot/basket pulled or door/interlock state | `freshViewsWithDps` calls `potPull(boolean)`. |
| `103` | integer | Cooking temperature | Temperature wheel publishes `103`; state stored as `cookingTemperature`. |
| `104` | bool | Keep warm enabled | `startCooking()` publishes `104=true` when warm is enabled; power-off/status reset publishes `104=false`. |
| `105` | integer | Keep warm time | `startCooking()` publishes warm time as `105`; state stored as `warmTime`. |
| `106` | bool | Appointment/delay enabled | `startCooking()` publishes `106=true` when pre-cook is enabled; power-off/status reset publishes `106=false`. |
| `107` | integer | Unknown T21 state value | App reads the value but the extracted bytecode context did not reveal the UI meaning. |
| `108` | bool | Temperature unit | App stores it as `defaultUnit`, updates `FryerUtils.setTemperatureT31`, and swaps Celsius/Fahrenheit wheel data. |

## Control Notes

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

- start/stop: `{ "2": true }`

Home Assistant should expose start cooking as an explicit button with clear naming, not as an automatically restored switch.

## Remaining Unknowns

- The HTTP/MQTT/WebSocket route the Thingclips SDK uses for account login, device listing, and `publishDps`.
- Whether SDK certificate pinning blocks HTTPS interception.

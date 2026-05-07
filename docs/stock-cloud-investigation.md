# Stock ProscenicHome Cloud Investigation

Goal: support an unmodified Proscenic air fryer through the ProscenicHome app/cloud API.

## Current Findings

Public ProscenicHome reverse engineering work exists, but it is almost entirely vacuum-focused.

Known hosts:

- `EU`: `https://mobile.proscenic.com.de`
- `US`: `https://mobile.proscenic.tw`
- `CN`: `https://mobile.proscenic.cn`

Known account flow:

- `POST /user/login`
- `POST /user/getEquips/{username}`

Known device list fields from vacuum examples include `name`, `code`, `typeName`, `model`, `sn`, `status`, `jump`, `cloud`, and `enabled`.

Known vacuum control flow:

- command URLs usually live under `/instructions/...`
- live status can use `/appInit/getSockAddr` plus a token-authenticated socket
- encrypted socket payloads use AES ECB with the token as the key

Unknown for air fryers:

- device `typeName`
- command endpoint paths
- infoType values
- payload shape for power, start/pause, temperature, time, preset, keep warm, and schedule
- whether the current Proscenic app still uses the older ProscenicHome endpoints

## Probe Results

The older ProscenicHome login endpoint accepts the account and returns success with `equipcount=1`, but `POST /user/getEquips/{username}` returns an empty device page across EU, US, and CN regions. That strongly suggests the account/device is not exposed through the legacy ProscenicHome device-list API used by the old vacuum integrations.

The current Android app is:

- package: `com.proscenic.smart.robot`
- app name: `Proscenic`
- version inspected: `4.1.0`

APK inspection shows the current app embeds the Thingclips/Tuya SDK and includes Proscenic fryer activities:

- `com.proscenic.fryer.activity.FryerHomeActivity`
- `com.proscenic.fryer.activity.FryerCookingDetailsActivity`
- `com.proscenic.fryer.t21.T21HomeActivity`
- `com.proscenic.fryer.t21.T21CookbookDetailsActivity`

This means the stock integration path should be treated as a Tuya OEM app problem, not as the legacy ProscenicHome vacuum API.

## Safe Next Step

Run the probe to list devices. It logs in and reads device metadata only; it does not send control commands.

```bash
cd /Users/antony/Code/HomeAssistant/integrations/homeassistant-proscenic-air-fryer
PROSCENIC_REGION=EU \
PROSCENIC_USERNAME='you@example.com' \
PROSCENIC_PASSWORD='your-password' \
python3 tools/proscenic_cloud_probe.py --raw
```

The key result is the air fryer device metadata, especially `typeName`, `code`, `model`, `sn`, `jump`, and `cloud`.

## Likely Implementation Shape

Once the stock cloud path is known, the Home Assistant integration should be changed from local MQTT to cloud polling:

- config flow collects the credentials and region needed by the chosen cloud path
- API client logs in and stores tokens in memory
- coordinator polls current state
- entities expose power/start/pause, temperature, time, preset, keep warm, and delay controls
- integration retries login on token expiry

For safety, command entities should be explicit and conservative. Starting a cooking appliance remotely should be a deliberate action, not an accidental state restore.

## Recommended Next Steps

1. Try pairing the air fryer with the generic Smart Life or Tuya Smart app. If that works, use Home Assistant's built-in Tuya integration first and download diagnostics for the device. The diagnostics will reveal the device category and datapoint schema.

2. If the fryer only pairs with the Proscenic OEM app, investigate Tuya OEM app account access:

   - determine whether Tuya IoT Platform can link the Proscenic OEM app account
   - determine whether the Android Thingclips app key/secret can be used with the Tuya App SDK auth flow outside Android
   - capture app traffic if SDK signing prevents direct HTTP probing

3. Extract the fryer datapoint schema from either:

   - Home Assistant Tuya diagnostics, if the device appears there
   - Tuya IoT Platform device debug page, if the OEM account can be linked
   - app traffic while opening the fryer panel and changing harmless settings such as temperature/time without starting cooking

## T21 Datapoint Recovery

Static APK analysis recovered the main T21 datapoints from `T21HomeActivity`. See `t21-datapoints.md`.

The app's embedded `THING_SMART_APPKEY` and `THING_SMART_SECRET` were tested against the standard Tuya OpenAPI token endpoint and returned `sign invalid`, so these SDK credentials cannot simply be used as a normal Tuya cloud project access ID/secret.

## iOS Proxyman Capture

Proxyman on iOS can decrypt the current Proscenic app traffic when SSL proxying is enabled and the Proxyman certificate is trusted on the phone.

Captured hosts so far:

- `https://appeu.proscenic.com`
- `https://appoperate-eu.proscenic.com`

Useful account/catalog endpoints captured:

- `GET /api/v1/app/version`
- `GET /api/v1/user/info`
- `POST /api/v1/stat/device/active`
- `GET /api/app/tag/page`
- `GET /api/app/recommended/maybeLike`
- `GET /api/app/recommended/cookSeries?pageIndex=1&pageSize=10`

The captured `POST /api/v1/stat/device/active` request confirmed that Proscenic exposes a stock fryer Tuya device id through the app.

The `/api/v1/user/info` product catalog confirms the T21 product entry:

- model/code: `T210`
- name: `T21`
- tag: `lib_fryer_u2_t3`
- Tuya product IDs: `ngdn90sk1yqmk9ww`, `xknldxif2q9jkplb`

The `appoperate-eu.proscenic.com` capture is currently recipe/content traffic, not device control traffic. It provides recipe names, temperatures, and cooking times, but does not expose live DP state or `publishDps` calls.

Tuya/Thingclips SDK traffic captured:

- host: `https://a1.tuyaeu.com`
- path: `POST /api.json`
- action parameter: `a=smartlife.m.api.batch.invoke`
- request body format: `application/x-www-form-urlencoded`
- important parameters: `sid`, `sign`, `postData`, `requestId`, `gid`, `clientId`, `uid`, `deviceId`, `sdkVersion`
- response body: encrypted `result` blob plus response `sign` and timestamp

This is the real Tuya mobile SDK control plane, but Proxyman only exposes the outer HTTPS and form wrapper. The actual batched API calls are encrypted inside `postData`, and the response payload is encrypted inside `result`.

A logout/login capture showed these outer Tuya SDK actions:

1. `smartlife.m.user.loginout`
2. `smartlife.m.user.username.token.get` (`v=2.0`, no `sid`)
3. `smartlife.m.user.email.password.login` (`v=3.0`, no `sid`)
4. `smartlife.m.token.get` (`sid` present)
5. `smartlife.m.app.domain.query`
6. `smartlife.m.app.smart.privacy.setting`
7. `smartlife.m.app.build.common.get`
8. `smartlife.m.miniprogram.kit.whitelist.query`
9. `b.m.device.register`
10. `smartlife.m.client.url.conf.get`
11. `smartlife.m.client.cache.config.list`
12. `smartlife.m.miniprogram.basiclibrary.get`
13. `smartlife.m.miniprogram.i18n.base.get`
14. `m.life.home.space.list`
15. `smartlife.m.api.batch.invoke`
16. `smartlife.m.pull.config.data.for.app`

The login sequence confirms that `sid` is issued/derived after the encrypted `email.password.login` exchange. The password itself is not enough to reproduce later calls; the mobile SDK also computes request signatures and encrypts/decrypts `postData`/`result`.

Do not commit raw Proxyman exports. They contain live session tokens in request headers.

Next practical path: capture enough Tuya SDK calls to classify which outer requests happen for panel load versus harmless setting changes. If the encrypted wrapper cannot be reproduced directly, the practical implementation may need to use an existing Tuya cloud/library path rather than Proscenic's mobile SDK encryption.

## Sources

- https://github.com/JuliusBlueTek/Proscenic-Home-Assistant
- https://community.jeedom.com/t/proscenichome-api-reverse-engineering-for-m7-pro/27461
- https://github.com/andker87/Proscenic-M7-PRO

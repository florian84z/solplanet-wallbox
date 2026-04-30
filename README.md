# Solplanet Wallbox for Home Assistant

Custom integration for the Solplanet / AISWEI EV Wallbox via the AISWEI App Cloud API.

## Entities

| Entity | Type | Description |
|---|---|---|
| Ladestrom | Sensor | Current charge current (A) |
| Ladeleistung | Sensor | Charge power (W) |
| Ladezeit Session | Sensor | Session duration (min) |
| Energie Session | Sensor | Session energy (Wh) |
| Spannung | Sensor | Voltage phase A (V) |
| Max. Ladestrom | Sensor | Current max current setting (A) |
| Fehlercode | Sensor | Fault code (0 = no fault) |
| Ladepunkt Status | Sensor | 0=no plug, 1=plugged, 2=starting, 3=charging |
| Lädt | Binary Sensor | Charging active |
| Stecker verbunden | Binary Sensor | Plug connected |
| Online | Binary Sensor | MQTT connection status |
| Solar-Laden | Binary Sensor | Solar surplus charging active |
| Plug and Charge | Binary Sensor | No RFID needed |
| Gesperrt | Binary Sensor | Charging point locked |
| Laden starten/stoppen | Switch | Start/stop charging session |
| Max. Ladestrom setzen | Number | Set max charge current (6–32 A) |

## Setup

1. Install via HACS (custom repository)
2. Restart Home Assistant
3. Go to Settings → Integrations → Add → "Solplanet Wallbox"
4. Enter your credentials:
   - **Wallbox SN**: Serial number of your wallbox (e.g. `EL0011112560xxx`)
   - **Plant ID**: Your plant ID (e.g. `5223xxx`)
   - **User ID**: Your AISWEI user ID (e.g. `1645xxx`)
   - **Token**: JWT token from the AISWEI app (valid ~90 days)

## Getting the Token

Capture the token from the AISWEI iOS/Android app using mitmproxy:
1. Set up mitmproxy as HTTP proxy on your phone
2. Open the AISWEI app
3. Copy the `token` header value from any API request
4. The token is valid for ~90 days

## Supported Devices

- Solplanet SOL EVPOWER / EV Charger (tested with `EL001...` serial numbers)
- Any AISWEI-based wallbox using the `aienergy-germany.aisweicloud.com` API

## Notes

- API: `aienergy-germany.aisweicloud.com` (App Cloud API)
- Poll interval: 30 seconds
- Write commands (start/stop/set current) use RRPC over MQTT

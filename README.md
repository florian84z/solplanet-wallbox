# Solplanet Wallbox for Home Assistant

Custom integration for the Solplanet / AISWEI EV Wallbox via the Solplanet Web Cloud API.

## Installation via HACS

1. HACS → Custom repositories → `https://github.com/florian84z/solplanet-wallbox` → Integration
2. Installieren → HA neu starten
3. Einstellungen → Integrationen → Hinzufügen → "Solplanet Wallbox"

## Konfiguration

| Feld | Beschreibung |
|---|---|
| Wallbox Seriennummer | Seriennummer der Wallbox (steht auf dem Gerät oder in der App) |
| Anlagen-ID | Plant ID aus der Solplanet Cloud URL |
| Token | Web Token aus dem Browser (siehe unten) |

### Token holen

1. `https://cloud.solplanet.net` im Browser öffnen (eingeloggt)
2. F12 → Application → Local Storage → `cloud.solplanet.net`
3. Wert `token` kopieren

Der Token ist mehrere Wochen gültig und muss danach erneuert werden.

## Entitäten

| Entität | Typ | Beschreibung |
|---|---|---|
| Ladestrom | Sensor | Aktueller Ladestrom (A) |
| Energie heute | Sensor | Geladene Energie heute (kWh) |
| Energie gesamt | Sensor | Gesamte geladene Energie (kWh) |
| Energie diesen Monat | Sensor | Energie diesen Monat (kWh) |
| Sitzungsdauer | Sensor | Dauer der aktuellen Ladesitzung (s) |
| Energie Session | Sensor | Energie der aktuellen Sitzung (kWh) |
| Max. Ladestrom | Sensor | Aktuell eingestellter Max. Strom (A) |
| Ladepunkt Status | Sensor | 0=kein Stecker, 1=lädt |
| Lädt | Binary Sensor | Ladevorgang aktiv |
| Solar-Laden | Binary Sensor | Solar-Überschussladen aktiv |
| Plug and Charge | Binary Sensor | Kein RFID erforderlich |
| Gesperrt | Binary Sensor | Ladepunkt gesperrt |
| Load Balancing | Binary Sensor | Load Balancing aktiv |
| Max. Ladestrom setzen | Number | Maximalen Ladestrom einstellen (6–32 A) |

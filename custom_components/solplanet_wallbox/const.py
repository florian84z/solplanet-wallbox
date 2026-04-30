"""Constants for Solplanet Wallbox integration."""

DOMAIN = "solplanet_wallbox"
MANUFACTURER = "Solplanet / AISWEI"

CONF_DEVICE_SN = "device_sn"
CONF_PLANT_ID = "plant_id"
CONF_TOKEN = "token"

# Web Cloud API (cloud.solplanet.net) - no HMAC needed, just token header
CLOUD_BASE = "https://cloud.solplanet.net/api"

DEFAULT_SCAN_INTERVAL = 30

POINT_STATUS = {
    0: "idle_no_plug",
    1: "idle_plugged",
    2: "starting",
    3: "charging",
}

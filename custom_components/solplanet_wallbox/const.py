"""Constants for Solplanet Wallbox integration."""

DOMAIN = "solplanet_wallbox"
MANUFACTURER = "Solplanet / AISWEI"

CONF_DEVICE_SN = "device_sn"
CONF_PLANT_ID = "plant_id"
CONF_USER_ID = "user_id"
CONF_TOKEN = "token"

APP_BASE = "https://aienergy-germany.aisweicloud.com"
APP_KEY = "204118125"
APP_VERSION = "4.11.1"

DEFAULT_SCAN_INTERVAL = 30

POINT_STATUS = {
    0: "idle_no_plug",
    1: "idle_plugged",
    2: "starting",
    3: "charging",
}

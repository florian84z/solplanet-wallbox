"""Binary sensors for Solplanet Wallbox."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass, BinarySensorEntity, BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import SolplanetWallboxCoordinator

BINARY_SENSORS = [
    (BinarySensorEntityDescription(
        key="is_charging", name="Lädt",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
    ), "is_charging"),
    (BinarySensorEntityDescription(
        key="solar_enable", name="Solar-Laden",
        device_class=BinarySensorDeviceClass.POWER,
    ), "solar_enable"),
    (BinarySensorEntityDescription(
        key="plug_chg_enable", name="Plug and Charge",
        device_class=BinarySensorDeviceClass.PLUG,
    ), "plug_chg_enable"),
    (BinarySensorEntityDescription(
        key="point_lock", name="Gesperrt",
        device_class=BinarySensorDeviceClass.LOCK,
    ), "point_lock"),
    (BinarySensorEntityDescription(
        key="load_balance", name="Load Balancing",
    ), "load_balance"),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SolplanetWallboxCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WallboxBinarySensor(coordinator, desc, key) for desc, key in BINARY_SENSORS])


class WallboxBinarySensor(CoordinatorEntity[SolplanetWallboxCoordinator], BinarySensorEntity):
    def __init__(self, coordinator, description, data_key):
        super().__init__(coordinator)
        self.entity_description = description
        self._data_key = data_key
        self._attr_unique_id = f"{coordinator.device_sn}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.device_sn)},
            "name": f"Solplanet Wallbox {coordinator.device_sn}",
            "manufacturer": MANUFACTURER,
            "model": "EV Charger",
        }

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        val = self.coordinator.data.get(self._data_key)
        return bool(val) if val is not None else None

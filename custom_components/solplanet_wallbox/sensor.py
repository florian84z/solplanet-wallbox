"""Sensors for Solplanet Wallbox."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent, UnitOfEnergy, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import SolplanetWallboxCoordinator

SENSORS = [
    (SensorEntityDescription(
        key="cur_a", name="Ladestrom",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ), "cur_a"),
    (SensorEntityDescription(
        key="etoday", name="Energie heute",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ), "etoday"),
    (SensorEntityDescription(
        key="etotal", name="Energie gesamt",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ), "etotal"),
    (SensorEntityDescription(
        key="emonth", name="Energie diesen Monat",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ), "emonth"),
    (SensorEntityDescription(
        key="keep_time", name="Sitzungsdauer",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
    ), "keep_time"),
    (SensorEntityDescription(
        key="session_energy", name="Energie Session",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ), "session_energy"),
    (SensorEntityDescription(
        key="max_cur", name="Max. Ladestrom",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ), "max_cur"),
    (SensorEntityDescription(
        key="point_status", name="Ladepunkt Status",
    ), "point_status"),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SolplanetWallboxCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WallboxSensor(coordinator, desc, key) for desc, key in SENSORS])


class WallboxSensor(CoordinatorEntity[SolplanetWallboxCoordinator], SensorEntity):
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
            "sw_version": coordinator.data.get("soft_ver") if coordinator.data else None,
        }

    @property
    def native_value(self):
        return self.coordinator.data.get(self._data_key) if self.coordinator.data else None

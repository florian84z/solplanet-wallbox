"""Sensors for Solplanet Wallbox."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfElectricCurrent, UnitOfEnergy, UnitOfPower, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import SolplanetWallboxCoordinator

SENSORS: list[tuple[SensorEntityDescription, str]] = [
    (SensorEntityDescription(
        key="current_a", name="Ladestrom",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ), "current_a"),
    (SensorEntityDescription(
        key="chg_power", name="Ladeleistung",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ), "chg_power"),
    (SensorEntityDescription(
        key="chg_time", name="Ladezeit Session",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
    ), "chg_time"),
    (SensorEntityDescription(
        key="chg_epe", name="Energie Session",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ), "chg_epe"),
    (SensorEntityDescription(
        key="voltage_a", name="Spannung",
        native_unit_of_measurement="V",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ), "voltage_a"),
    (SensorEntityDescription(
        key="max_cur", name="Max. Ladestrom",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ), "max_cur"),
    (SensorEntityDescription(
        key="fault_code", name="Fehlercode",
    ), "fault_code"),
    (SensorEntityDescription(
        key="point_status", name="Ladepunkt Status",
    ), "point_status"),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SolplanetWallboxCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        WallboxSensor(coordinator, desc, key)
        for desc, key in SENSORS
    ])


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

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

SENSORS = [
    (SensorEntityDescription(
        key="cur_a", name="Ladestrom",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-ac",
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
        icon="mdi:timer",
    ), "keep_time"),
    (SensorEntityDescription(
        key="session_duration", name="Sitzungsdauer Minuten",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:timer-outline",
    ), "session_duration"),
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
        icon="mdi:current-ac",
    ), "max_cur"),
    (SensorEntityDescription(
        key="point_status", name="Ladepunkt Status",
        icon="mdi:ev-station",
    ), "point_status"),
    (SensorEntityDescription(
        key="order_id", name="Aktuelle Order ID",
        icon="mdi:identifier",
    ), "order_id"),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SolplanetWallboxCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [WallboxSensor(coordinator, desc, key) for desc, key in SENSORS]
    entities.append(WallboxMaxPowerSensor(coordinator))
    async_add_entities(entities)


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


class WallboxMaxPowerSensor(CoordinatorEntity[SolplanetWallboxCoordinator], SensorEntity):
    """Max Ladeleistung in W (3-phasig: MaxCur × 230V × 3)."""

    def __init__(self, coordinator: SolplanetWallboxCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_sn}_max_power"
        self._attr_name = "Max. Ladeleistung"
        self._attr_native_unit_of_measurement = UnitOfPower.WATT
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = "mdi:lightning-bolt"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.device_sn)},
            "name": f"Solplanet Wallbox {coordinator.device_sn}",
            "manufacturer": MANUFACTURER,
            "model": "EV Charger",
        }

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        max_cur = self.coordinator.data.get("max_cur")
        if max_cur is None:
            return None
        return round(float(max_cur) * 230 * 3)

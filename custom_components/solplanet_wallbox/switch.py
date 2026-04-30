"""Switch entities for Solplanet Wallbox."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import SolplanetWallboxCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SolplanetWallboxCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WallboxChargingSwitch(coordinator)])


class WallboxChargingSwitch(CoordinatorEntity[SolplanetWallboxCoordinator], SwitchEntity):
    """Start/stop charging."""

    def __init__(self, coordinator: SolplanetWallboxCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_sn}_charging_switch"
        self._attr_name = "Laden starten/stoppen"
        self._attr_icon = "mdi:ev-station"
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
        return self.coordinator.data.get("is_charging", False)

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_start_charging()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_stop_charging()

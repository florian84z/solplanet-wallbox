"""Switch entity for Solplanet Wallbox - start/stop charging via MaxCur."""
from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import SolplanetWallboxCoordinator

_LOGGER = logging.getLogger(__name__)

# Default current when enabling charging (if max_cur is 0 or unknown)
DEFAULT_CURRENT = 6


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SolplanetWallboxCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WallboxChargingSwitch(coordinator)])


class WallboxChargingSwitch(CoordinatorEntity[SolplanetWallboxCoordinator], SwitchEntity):
    """Toggle charging by setting MaxCur to 0 (off) or last value (on).
    
    The Solplanet web UI uses this exact mechanism:
    - Charging OFF = RRPC/Config MaxCur: 0
    - Charging ON  = RRPC/Config MaxCur: <configured value>
    """

    def __init__(self, coordinator: SolplanetWallboxCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_sn}_charging_switch"
        self._attr_name = "Laden aktivieren"
        self._attr_icon = "mdi:ev-station"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.device_sn)},
            "name": f"Solplanet Wallbox {coordinator.device_sn}",
            "manufacturer": MANUFACTURER,
            "model": "EV Charger",
        }
        self._last_current: int = DEFAULT_CURRENT

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        max_cur = self.coordinator.data.get("max_cur")
        if max_cur is None:
            return None
        enabled = int(max_cur) > 0
        # Remember last non-zero current for restore
        if enabled and int(max_cur) > 0:
            self._last_current = int(max_cur)
        return enabled

    async def async_turn_on(self, **kwargs) -> None:
        """Start charging by restoring last current."""
        current = self._last_current or DEFAULT_CURRENT
        _LOGGER.info("Enabling charging at %sA", current)
        await self.coordinator.async_set_max_current(current)

    async def async_turn_off(self, **kwargs) -> None:
        """Stop charging by setting MaxCur to 0."""
        # Save current value before disabling
        if self.coordinator.data:
            cur = self.coordinator.data.get("max_cur", DEFAULT_CURRENT)
            if cur and int(cur) > 0:
                self._last_current = int(cur)
        _LOGGER.info("Disabling charging (MaxCur=0)")
        await self.coordinator.async_set_max_current(0)

"""Switch entities for Solplanet Wallbox."""
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

DEFAULT_CURRENT = 6


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: SolplanetWallboxCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        WallboxChargingSwitch(coordinator),
        WallboxPlugChargeSwitch(coordinator),
    ])


def _device_info(coordinator):
    return {
        "identifiers": {(DOMAIN, coordinator.device_sn)},
        "name": f"Solplanet Wallbox {coordinator.device_sn}",
        "manufacturer": MANUFACTURER,
        "model": "EV Charger",
    }


class WallboxChargingSwitch(CoordinatorEntity[SolplanetWallboxCoordinator], SwitchEntity):
    """Toggle charging via MaxCur (0 = off, >0 = on).
    
    The Solplanet web UI uses this mechanism:
    - Charging OFF = RRPC/Config MaxCur: 0
    - Charging ON  = RRPC/Config MaxCur: <configured value>
    """

    def __init__(self, coordinator: SolplanetWallboxCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_sn}_charging_switch"
        self._attr_name = "Laden aktivieren"
        self._attr_icon = "mdi:ev-station"
        self._attr_device_info = _device_info(coordinator)
        self._last_current: int = DEFAULT_CURRENT

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        max_cur = self.coordinator.data.get("max_cur")
        if max_cur is None:
            return None
        enabled = int(max_cur) > 0
        if enabled:
            self._last_current = int(max_cur)
        return enabled

    async def async_turn_on(self, **kwargs) -> None:
        current = self._last_current or DEFAULT_CURRENT
        _LOGGER.info("Laden aktivieren bei %sA", current)
        await self.coordinator.async_set_max_current(current)

    async def async_turn_off(self, **kwargs) -> None:
        if self.coordinator.data:
            cur = self.coordinator.data.get("max_cur", DEFAULT_CURRENT)
            if cur and int(cur) > 0:
                self._last_current = int(cur)
        _LOGGER.info("Laden deaktivieren (MaxCur=0)")
        await self.coordinator.async_set_max_current(0)


class WallboxPlugChargeSwitch(CoordinatorEntity[SolplanetWallboxCoordinator], SwitchEntity):
    """Toggle Plug & Charge – auto-start when cable is connected."""

    def __init__(self, coordinator: SolplanetWallboxCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_sn}_plug_charge"
        self._attr_name = "Plug & Charge"
        self._attr_icon = "mdi:ev-plug-type2"
        self._attr_device_info = _device_info(coordinator)

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("plug_chg_enable", False)

    async def async_turn_on(self, **kwargs) -> None:
        _LOGGER.info("Plug & Charge aktiviert")
        await self.coordinator.async_set_plug_charge(True)

    async def async_turn_off(self, **kwargs) -> None:
        _LOGGER.info("Plug & Charge deaktiviert")
        await self.coordinator.async_set_plug_charge(False)

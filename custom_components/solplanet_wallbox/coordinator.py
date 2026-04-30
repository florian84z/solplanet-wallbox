"""Solplanet Wallbox data coordinator."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import SolplanetWallboxClient
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class SolplanetWallboxCoordinator(DataUpdateCoordinator):
    """Coordinator polling realtime + config data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: SolplanetWallboxClient,
        device_sn: str,
    ) -> None:
        self.client = client
        self.device_sn = device_sn
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{device_sn}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict:
        try:
            realtime, config = await asyncio.gather(
                self.client.get_realtime(),
                self.client.get_config(),
            )
            return {
                # Realtime
                "point_status":    realtime.point_status,
                "is_charging":     realtime.is_charging,
                "is_connected":    realtime.is_connected,
                "current_a":       realtime.current_a,
                "voltage_a":       realtime.vol_a,
                "chg_power":       realtime.chg_power,
                "chg_time":        realtime.chg_time,
                "chg_epe":         realtime.chg_epe,
                "fault_code":      realtime.fault_code,
                "mqtt_online":     realtime.mqtt_status == 1,
                "order_no":        realtime.order_no_server,
                "start_time":      realtime.start_time,
                # Config
                "max_cur":         config.get("MaxCur"),
                "solar_enable":    config.get("SolarEnable"),
                "plug_chg_enable": config.get("PlugChgEnable"),
                "point_lock":      config.get("PointLock"),
                "off_peak_enable": config.get("OffPeakEnable"),
                "soft_ver":        config.get("SoftVer"),
                "hard_ver":        config.get("HardVer"),
            }
        except Exception as err:
            raise UpdateFailed(f"Wallbox API error: {err}") from err

    async def async_start_charging(self) -> None:
        await self.client.start_charging()
        await self.async_refresh()

    async def async_stop_charging(self) -> None:
        await self.client.stop_charging()
        await self.async_refresh()

    async def async_set_max_current(self, ampere: int) -> None:
        await self.client.set_max_current(ampere)
        await self.async_refresh()

    async def async_lock(self) -> None:
        await self.client.lock()
        await self.async_refresh()

    async def async_unlock(self) -> None:
        await self.client.unlock()
        await self.async_refresh()

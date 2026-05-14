"""Solplanet Wallbox coordinator."""
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
    """Polls live data + config every 30s."""

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
            live, cfg = await asyncio.gather(
                self.client.get_live_data(),
                self.client.get_config(),
            )
            return {
                # Live data
                "point_status":      live.point_status,
                "is_charging":       live.is_charging,
                "is_connected":      live.is_connected,
                "cur_a":             live.cur_a,
                "etoday":            live.etoday,
                "etotal":            live.etotal,
                "emonth":            live.emonth,
                "keep_time":         live.keep_time,
                "session_energy":    live.session_energy_kwh,
                "session_duration":  live.session_duration_min,
                "soft_ver":          live.soft_ver,
                "order_id":          live.order_id,
                "start_type":        live.start_type,
                # Config
                "max_cur":           cfg.get("maxCur"),
                "solar_enable":      bool(cfg.get("solarEnable")),
                "plug_chg_enable":   bool(cfg.get("plugChgEnable")),
                "point_lock":        bool(cfg.get("pointLock")),
                "load_balance":      bool(cfg.get("loadBalanceEnable")),
                "delay_enable":      bool(cfg.get("delayEnable")),
            }
        except Exception as err:
            raise UpdateFailed(f"Wallbox API error: {err}") from err

    async def async_set_max_current(self, ampere: int) -> None:
        await self.client.set_max_current(ampere)
        await self.async_refresh()

    async def async_set_plug_charge(self, enabled: bool) -> None:
        await self.client.set_plug_charge(enabled)
        await self.async_refresh()

    async def async_start_charging(self) -> None:
        await self.client.start_charging()
        await self.async_refresh()

    async def async_stop_charging(self) -> None:
        await self.client.stop_charging()
        await self.async_refresh()

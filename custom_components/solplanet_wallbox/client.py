"""Solplanet Wallbox Web Cloud API Client.

Uses cloud.solplanet.net (same-origin web API).
Authentication: token from browser localStorage['token'].
No HMAC signature required.

Endpoints used:
  GET /charger/ChargeDetailBySn?devSn=<SN>      -> live data
  GET /charger/getChargerOperateInfo?devSn=<SN> -> config
  POST /charger/request-message-to-pile         -> RRPC write
  POST /charger/proxy-message-by-mqtt           -> RRPC ack
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from urllib.parse import quote

from aiohttp import ClientSession

from .const import CLOUD_BASE

_LOGGER = logging.getLogger(__name__)


@dataclass
class WallboxLiveData:
    """Live data from ChargeDetailBySn."""
    point_status: str | None = None   # "0"=idle, "1"=charging
    cur_a: float | None = None        # Ladestrom in A
    etoday: float | None = None       # Energie heute kWh
    etotal: float | None = None       # Energie gesamt kWh
    emonth: float | None = None       # Energie diesen Monat kWh
    keep_time: int | None = None      # Sitzungsdauer Sekunden
    chg_epe: int | None = None        # Sitzungsenergie (×0.1 kWh)
    soft_ver: str | None = None       # Firmware
    order_id: str | None = None

    @property
    def is_charging(self) -> bool:
        return str(self.point_status) == "1"

    @property
    def is_connected(self) -> bool:
        return str(self.point_status) in ("1",)

    @property
    def session_energy_kwh(self) -> float | None:
        if self.chg_epe is None:
            return None
        return round(self.chg_epe / 10, 2)


class SolplanetWallboxClient:
    """Client for the Solplanet Web Cloud API."""

    def __init__(
        self,
        session: ClientSession,
        token: str,
        device_sn: str,
        plant_id: str,
    ) -> None:
        self._session = session
        self._token = token
        self._device_sn = device_sn
        self._plant_id = plant_id

    def _headers(self, referer_path: str = "") -> dict:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "token": self._token,
            "localE": "de_DE",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/147.0.0.0 Safari/537.36"
            ),
            "Referer": (
                f"https://cloud.solplanet.net/home/device/"
                f"evchargerDetail?deviceSn={self._device_sn}&id={self._plant_id}"
            ),
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
        }

    async def _get(self, path: str, params: dict | None = None) -> dict:
        async with self._session.get(
            f"{CLOUD_BASE}{path}",
            headers=self._headers(),
            params=params,
        ) as r:
            r.raise_for_status()
            data = await r.json(content_type=None)
            return data.get("result", data)

    async def _rrpc(self, key: str, data: dict) -> dict:
        """Send RRPC command and proxy ACK."""
        message = json.dumps({"key": key, "data": data})
        encoded = quote(message)

        url1 = (
            f"{CLOUD_BASE}/charger/request-message-to-pile"
            f"?devSn={self._device_sn}&message={encoded}"
        )
        async with self._session.post(url1, headers=self._headers()) as r:
            r.raise_for_status()
            resp1 = await r.json(content_type=None)

        if resp1.get("code") != 200:
            raise RuntimeError(f"RRPC failed: {resp1}")

        ack = json.dumps(resp1.get("result", {}))
        url2 = (
            f"{CLOUD_BASE}/charger/proxy-message-by-mqtt"
            f"?devSn={self._device_sn}&message={quote(ack)}"
        )
        async with self._session.post(url2, headers=self._headers()) as r:
            r.raise_for_status()

        return resp1

    async def get_live_data(self) -> WallboxLiveData:
        """Get live charging data."""
        r = await self._get("/charger/ChargeDetailBySn", {"devSn": self._device_sn})
        return WallboxLiveData(
            point_status=str(r.get("point_status", "0")),
            cur_a=r.get("cur_a"),
            etoday=r.get("etoday"),
            etotal=r.get("etotal"),
            emonth=r.get("emonth"),
            keep_time=r.get("keep_time"),
            chg_epe=r.get("chg_epe"),
            soft_ver=r.get("soft_ver"),
            order_id=r.get("order_id"),
        )

    async def get_config(self) -> dict:
        """Get wallbox config."""
        return await self._get(
            "/charger/getChargerOperateInfo", {"devSn": self._device_sn}
        )

    async def set_max_current(self, ampere: int) -> dict:
        return await self._rrpc("RRPC/Config", {"name0": False, "MaxCur": ampere})

    async def set_plug_charge(self, enable: bool) -> dict:
        return await self._rrpc("RRPC/Config", {
            "PlugChgEnable": 1 if enable else 0,
            "RfidChgEnable": 0 if enable else 1,
            "BookEnable": 0,
        })

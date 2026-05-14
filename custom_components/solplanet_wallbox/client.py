"""Solplanet Wallbox Web Cloud API Client."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from urllib.parse import quote

from aiohttp import ClientSession

from .const import CLOUD_BASE, CLOUD_HOST

_LOGGER = logging.getLogger(__name__)


@dataclass
class WallboxLiveData:
    point_status: str | None = None
    cur_a: float | None = None
    etoday: float | None = None
    etotal: float | None = None
    emonth: float | None = None
    keep_time: int | None = None
    chg_epe: int | None = None
    soft_ver: str | None = None
    order_id: str | None = None
    start_timestamp: int | None = None
    start_type: int | None = None

    @property
    def is_connected(self) -> bool:
        return str(self.point_status) in ("1", "2", "3")

    @property
    def is_charging(self) -> bool:
        return str(self.point_status) == "1"

    @property
    def session_energy_kwh(self) -> float | None:
        if self.chg_epe is None:
            return None
        return round(self.chg_epe / 10, 2)

    @property
    def session_duration_min(self) -> int | None:
        if self.keep_time is None:
            return None
        return round(self.keep_time / 60)


class SolplanetWallboxClient:
    def __init__(
        self,
        session: ClientSession,
        token: str,
        cookie: str,
        device_sn: str,
        plant_id: str,
        auth_manager=None,
    ) -> None:
        self._session = session
        self._token = token
        self._cookie = cookie
        self._device_sn = device_sn
        self._plant_id = plant_id
        self._auth_manager = auth_manager

    def _headers(self) -> dict:
        return {
            "Accept": "application/json",
            "Accept-Language": "de-DE,de;q=0.9",
            "Content-Type": "application/json",
            "Referer": (
                f"{CLOUD_HOST}/home/device/evchargerDetail"
                f"?deviceSn={self._device_sn}&id={self._plant_id}"
            ),
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/147.0.0.0 Safari/537.36"
            ),
            "localE": "de_DE",
            "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "token": self._token,
            "Cookie": self._cookie,
        }

    async def _refresh_auth(self) -> None:
        """Refresh token and cookie via auth manager."""
        if self._auth_manager:
            auth = await self._auth_manager.async_get_auth(force_refresh=True)
            self._token = auth.token
            self._cookie = auth.cookie
            _LOGGER.debug("Auth refreshed")

    async def _get(self, path: str, params: dict | None = None) -> dict:
        async with self._session.get(
            f"{CLOUD_BASE}{path}",
            headers=self._headers(),
            params=params,
        ) as r:
            if r.status in (401, 403, 444):
                _LOGGER.debug("Auth error %s, refreshing...", r.status)
                await self._refresh_auth()
                async with self._session.get(
                    f"{CLOUD_BASE}{path}",
                    headers=self._headers(),
                    params=params,
                ) as r2:
                    r2.raise_for_status()
                    data = await r2.json(content_type=None)
                    return data.get("result", data)
            r.raise_for_status()
            data = await r.json(content_type=None)
            return data.get("result", data)

    async def _rrpc(self, key: str, data: dict) -> dict:
        """Send RRPC command + ACK to Wallbox."""
        message = json.dumps({"key": key, "data": data})
        encoded = quote(message)
        # Step 1: Send command
        url1 = (
            f"{CLOUD_BASE}/charger/request-message-to-pile"
            f"?devSn={self._device_sn}&message={encoded}"
        )
        async with self._session.post(url1, headers=self._headers()) as r:
            r.raise_for_status()
            resp1 = await r.json(content_type=None)
        if resp1.get("code") != 200:
            raise RuntimeError(f"RRPC failed: {resp1}")
        # Step 2: ACK via MQTT proxy (required!)
        ack = json.dumps(resp1.get("result", {}))
        url2 = (
            f"{CLOUD_BASE}/charger/proxy-message-by-mqtt"
            f"?devSn={self._device_sn}&message={quote(ack)}"
        )
        async with self._session.post(url2, headers=self._headers()) as r:
            r.raise_for_status()
        return resp1

    async def get_live_data(self) -> WallboxLiveData:
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
            start_timestamp=r.get("start_timestamp"),
            start_type=r.get("start_type"),
        )

    async def get_config(self) -> dict:
        return await self._get(
            "/charger/getChargerOperateInfo", {"devSn": self._device_sn}
        )

    async def get_charge_history(self, query_type: str = "month") -> dict:
        """Tägliche kWh Ladehistorie (month/year)."""
        return await self._get(
            "/charger/pileOrdersChart",
            {
                "queryType": query_type,
                "devSn": self._device_sn,
                "filter": "",
            },
        )

    async def set_max_current(self, ampere: int) -> dict:
        return await self._rrpc("RRPC/Config", {"name0": False, "MaxCur": ampere})

    async def set_plug_charge(self, enabled: bool) -> dict:
        return await self._rrpc("RRPC/Config", {
            "BookEnable": 0,
            "PlugChgEnable": 1 if enabled else 0,
            "RfidChgEnable": 0,
        })

    async def start_charging(self) -> dict:
        return await self._rrpc("RRPC/StartChg", {
            "StartType": 4,
            "GunNo": 1,
        })

    async def stop_charging(self) -> dict:
        # OrderNo kann leer bleiben – funktioniert laut HAR
        return await self._rrpc("RRPC/StopChg", {
            "StopCode": 1,
            "OrderNoServer": "",
            "OrderNoAPP": "",
            "OrderNoPoint": "",
            "GunNo": 1,
        })

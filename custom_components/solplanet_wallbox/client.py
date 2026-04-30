"""Solplanet Wallbox Web Cloud API Client."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from urllib.parse import quote

from aiohttp import ClientSession, CookieJar

from .const import CLOUD_BASE

_LOGGER = logging.getLogger(__name__)

CLOUD_HOST = "https://cloud.solplanet.net"


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

    @property
    def is_charging(self) -> bool:
        return str(self.point_status) == "1"

    @property
    def session_energy_kwh(self) -> float | None:
        if self.chg_epe is None:
            return None
        return round(self.chg_epe / 10, 2)


class SolplanetWallboxClient:
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
        self._cookie = None

    def _headers(self) -> dict:
        h = {
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
        }
        if self._cookie:
            h["Cookie"] = self._cookie
        return h

    async def _fetch_cookie(self) -> None:
        """Fetch the anti-bot session cookie by visiting the page first."""
        try:
            async with self._session.get(
                f"{CLOUD_HOST}/home/device/evchargerDetail"
                f"?deviceSn={self._device_sn}&id={self._plant_id}",
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/147.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/html",
                    "token": self._token,
                },
                allow_redirects=True,
            ) as r:
                cookies = r.cookies
                cookie_parts = []
                for name, val in cookies.items():
                    cookie_parts.append(f"{name}={val}")
                if cookie_parts:
                    self._cookie = "; ".join(cookie_parts)
                    _LOGGER.debug("Got cookie: %s", self._cookie)
        except Exception as err:
            _LOGGER.debug("Cookie fetch failed: %s", err)

    async def _get(self, path: str, params: dict | None = None) -> dict:
        if not self._cookie:
            await self._fetch_cookie()

        async with self._session.get(
            f"{CLOUD_BASE}{path}",
            headers=self._headers(),
            params=params,
        ) as r:
            if r.status == 444:
                # Cookie expired, refresh and retry once
                _LOGGER.debug("444 received, refreshing cookie and retrying")
                self._cookie = None
                await self._fetch_cookie()
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
        r = await self._get(
            "/charger/ChargeDetailBySn", {"devSn": self._device_sn}
        )
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
        return await self._get(
            "/charger/getChargerOperateInfo", {"devSn": self._device_sn}
        )

    async def set_max_current(self, ampere: int) -> dict:
        return await self._rrpc("RRPC/Config", {"name0": False, "MaxCur": ampere})

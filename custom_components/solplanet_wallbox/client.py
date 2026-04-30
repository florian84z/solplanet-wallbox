"""Solplanet Wallbox App API Client."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time
import uuid
from dataclasses import dataclass
from email.utils import formatdate
from urllib.parse import urlencode

from aiohttp import ClientSession

from .const import APP_BASE, APP_KEY, APP_VERSION

_LOGGER = logging.getLogger(__name__)


@dataclass
class WallboxRealtimeData:
    """Realtime data from pile-realtime-info endpoint."""
    dev_sn: str | None = None
    mqtt_status: int | None = None
    point_status: int | None = None
    vol_a: float | None = None
    cur_a: float | None = None
    chg_power: float | None = None
    chg_time: int | None = None
    chg_epe: float | None = None
    fault_code: int | None = None
    order_no_server: str | None = None
    start_time: str | None = None

    @property
    def current_a(self) -> float | None:
        """Return current in Ampere (CurA is in 10mA units)."""
        return round(self.cur_a / 100, 2) if self.cur_a is not None else None

    @property
    def is_charging(self) -> bool:
        return self.point_status == 3

    @property
    def is_connected(self) -> bool:
        return self.point_status in (1, 2, 3)


class SolplanetWallboxClient:
    """Client for the Solplanet/AISWEI Wallbox App Cloud API."""

    def __init__(
        self,
        session: ClientSession,
        userid: str,
        token: str,
        device_sn: str,
        plant_id: str,
        app_secret: str = "",
    ) -> None:
        self._session = session
        self._userid = userid
        self._token = token
        self._device_sn = device_sn
        self._plant_id = plant_id
        self._app_secret = app_secret

    def _make_headers(self, method: str, path: str) -> dict:
        ts = str(int(time.time() * 1000))
        nonce = str(uuid.uuid4()).upper()
        date = formatdate(usegmt=True)
        ct = "application/x-www-form-urlencoded; charset=UTF-8"
        signed_headers = "\n".join([
            f"X-Ca-Key:{APP_KEY}",
            f"X-Ca-Nonce:{nonce}",
            "X-Ca-Signature-Method:HmacSHA256",
            f"X-Ca-Timestamp:{ts}",
            "X-Ca-Version:1",
        ])
        sts = "\n".join([
            method.upper(),
            "application/json; charset=UTF-8",
            "",
            ct,
            date,
            signed_headers,
            path,
        ])
        if self._app_secret:
            sig = base64.b64encode(
                hmac.new(self._app_secret.encode(), sts.encode(), hashlib.sha256).digest()
            ).decode()
        else:
            sig = "NO_SECRET"

        return {
            "userid": self._userid,
            "token": self._token,
            "factory": "aiswei",
            "x-ca-timestamp": ts,
            "x-ca-key": APP_KEY,
            "region": "1",
            "x-ca-signature-method": "HmacSHA256",
            "locale": "de_DE",
            "os": "iOS",
            "versioncode": APP_VERSION,
            "usertype": "1",
            "date": date,
            "x-ca-nonce": nonce,
            "x-ca-signature": sig,
            "x-ca-signature-headers": "X-Ca-Key,X-Ca-Nonce,X-Ca-Signature-Method,X-Ca-Timestamp,X-Ca-Version",
            "x-ca-version": "1",
            "Accept": "application/json; charset=UTF-8",
            "Content-Type": ct,
        }

    async def _post(self, path: str, data: dict) -> dict:
        async with self._session.post(
            f"{APP_BASE}{path}",
            headers=self._make_headers("POST", path),
            data=data,
        ) as r:
            r.raise_for_status()
            return await r.json(content_type=None)

    async def _rrpc(self, key: str, data: dict) -> dict:
        """Send RRPC command (2-step: send + proxy ACK)."""
        msg = json.dumps({"key": key, "data": data})
        r1 = await self._post("/charger/request-message-to-pile.json", {
            "devSn": self._device_sn,
            "message": msg,
            "psn": "",
            "stationId": self._plant_id,
        })
        if r1.get("status_code") != 200:
            raise RuntimeError(f"RRPC failed: {r1}")
        await self._post("/charger/proxy-message-by-mqtt.json", {
            "devSn": self._device_sn,
            "message": json.dumps(r1.get("data", {})),
        })
        return r1

    async def get_realtime(self) -> WallboxRealtimeData:
        """Get live charging data."""
        r = (await self._post(
            "/charger/pile-realtime-info.json",
            {"devSn": self._device_sn},
        )).get("data", {})
        return WallboxRealtimeData(
            dev_sn=r.get("DevSn"),
            mqtt_status=r.get("MQTTStatus"),
            point_status=r.get("PointStatus"),
            vol_a=r.get("VolA"),
            cur_a=r.get("CurA"),
            chg_power=r.get("ChgPower"),
            chg_time=r.get("ChgTime"),
            chg_epe=r.get("ChgEPE"),
            fault_code=r.get("FaultCode"),
            order_no_server=r.get("OrderNoServer"),
            start_time=r.get("StartTime"),
        )

    async def get_config(self) -> dict:
        """Get wallbox configuration."""
        return (await self._post(
            "/charger/pile-config-info.json",
            {"devSn": self._device_sn},
        )).get("data", {})

    async def start_charging(self) -> dict:
        return await self._rrpc("RRPC/StartChg", {
            "OrderNoAPP": "", "OrderNoServer": "", "StartType": 5,
            "OrderNoPoint": "", "GunNo": 1,
        })

    async def stop_charging(self) -> dict:
        return await self._rrpc("RRPC/StopChg", {
            "StopCode": 1, "OrderNoAPP": "", "OrderNoServer": "",
            "OrderNoPoint": "", "GunNo": 1,
        })

    async def lock(self) -> dict:
        return await self._rrpc("RRPC/LockPile", {"DevSn": self._device_sn})

    async def unlock(self) -> dict:
        return await self._rrpc("RRPC/UnLockPile", {"DevSn": self._device_sn})

    async def set_max_current(self, ampere: int) -> dict:
        return await self._rrpc("RRPC/Config", {"MaxCur": ampere})

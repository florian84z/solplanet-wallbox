"""Authentication for Solplanet Cloud API."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import quote

from aiohttp import ClientSession, ClientResponseError

_LOGGER = logging.getLogger(__name__)

CLOUD_HOST = "https://cloud.solplanet.net"


@dataclass
class SolplanetAuth:
    """Holds authentication credentials."""
    token: str
    cookie: str
    user_id: str = ""


class SolplanetAuthManager:
    """Manages login and token refresh for Solplanet Cloud."""

    def __init__(
        self,
        session: ClientSession,
        email: str,
        password: str,
    ) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._auth: SolplanetAuth | None = None

    async def async_login(self) -> SolplanetAuth:
        """Login and return fresh auth credentials."""
        _LOGGER.debug("Logging in to Solplanet Cloud as %s", self._email)

        url = (
            f"{CLOUD_HOST}/api/user/login"
            f"?account={quote(self._email)}&password={quote(self._password)}"
        )

        async with self._session.post(
            url,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/147.0.0.0 Safari/537.36"
                ),
                "Referer": f"{CLOUD_HOST}/login",
                "Origin": CLOUD_HOST,
            },
        ) as r:
            if r.status != 200:
                raise RuntimeError(f"Login HTTP error: {r.status}")

            data = await r.json(content_type=None)
            _LOGGER.debug("Login response: code=%s", data.get("code"))

            if data.get("code") not in (200, 0):
                msg = data.get("msg", "Unknown error")
                raise RuntimeError(f"Login failed: {msg} (code={data.get('code')})")

            result = data.get("result", data)

            # Extract token — different APIs put it in different places
            token = (
                result.get("token")
                or result.get("access_token")
                or data.get("token")
                or ""
            )

            if not token:
                # Try to get token from response headers or cookies
                resp_cookies = r.cookies
                for name, val in resp_cookies.items():
                    if "token" in name.lower():
                        token = val
                        break

            if not token:
                raise RuntimeError(
                    f"Login succeeded but no token found in response: {data}"
                )

            # Build cookie string from response cookies
            cookie_parts = []
            for name, val in r.cookies.items():
                cookie_parts.append(f"{name}={val}")

            # apitoken cookie is set by the web app JS, reconstruct it
            # The JWT token IS the apitoken cookie value
            if not any("apitoken" in p for p in cookie_parts):
                # Try to find JWT in result
                jwt = result.get("apitoken") or result.get("jwt") or ""
                if jwt:
                    cookie_parts.append(f"apitoken={jwt}")

            cookie_str = "; ".join(cookie_parts) if cookie_parts else f"token={token}"

            user_id = str(result.get("userId") or result.get("user_id") or "")

            self._auth = SolplanetAuth(
                token=token,
                cookie=cookie_str,
                user_id=user_id,
            )

            _LOGGER.info(
                "Solplanet login successful, user_id=%s, token=%s...",
                user_id,
                token[:10],
            )
            return self._auth

    async def async_get_auth(self, force_refresh: bool = False) -> SolplanetAuth:
        """Get current auth, refreshing if needed."""
        if self._auth is None or force_refresh:
            return await self.async_login()
        return self._auth

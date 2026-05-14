"""Config flow for Solplanet Wallbox."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .auth import SolplanetAuthManager
from .const import CONF_DEVICE_SN, CONF_EMAIL, CONF_PASSWORD, CONF_PLANT_ID, DOMAIN

STEP_SCHEMA = vol.Schema({
    vol.Required(CONF_EMAIL): str,
    vol.Required(CONF_PASSWORD): str,
    vol.Required(CONF_DEVICE_SN): str,
    vol.Required(CONF_PLANT_ID): str,
})


class SolplanetWallboxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                session = async_get_clientsession(self.hass)
                auth_mgr = SolplanetAuthManager(
                    session,
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
                )
                await auth_mgr.async_login()
            except Exception as err:
                _LOGGER = __import__('logging').getLogger(__name__)
                _LOGGER.warning("Login failed: %s", err)
                errors["base"] = "invalid_auth"
            else:
                await self.async_set_unique_id(user_input[CONF_DEVICE_SN])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Wallbox {user_input[CONF_DEVICE_SN]}",
                    data=user_input,
                )
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_SCHEMA,
            errors=errors,
        )

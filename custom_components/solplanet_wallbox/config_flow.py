"""Config flow for Solplanet Wallbox."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries

from .const import CONF_COOKIE, CONF_DEVICE_SN, CONF_PLANT_ID, CONF_TOKEN, DOMAIN

STEP_SCHEMA = vol.Schema({
    vol.Required(CONF_DEVICE_SN): str,
    vol.Required(CONF_PLANT_ID): str,
    vol.Required(CONF_TOKEN): str,
    vol.Required(CONF_COOKIE): str,
})


class SolplanetWallboxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_DEVICE_SN])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"Wallbox {user_input[CONF_DEVICE_SN]}",
                data=user_input,
            )
        return self.async_show_form(step_id="user", data_schema=STEP_SCHEMA)

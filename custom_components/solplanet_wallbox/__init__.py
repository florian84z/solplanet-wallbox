"""Solplanet Wallbox integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import SolplanetWallboxClient
from .const import CONF_DEVICE_SN, CONF_PLANT_ID, CONF_TOKEN, DOMAIN
from .coordinator import SolplanetWallboxCoordinator

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.NUMBER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    client = SolplanetWallboxClient(
        session=session,
        token=entry.data[CONF_TOKEN],
        device_sn=entry.data[CONF_DEVICE_SN],
        plant_id=entry.data[CONF_PLANT_ID],
    )
    coordinator = SolplanetWallboxCoordinator(hass, client, entry.data[CONF_DEVICE_SN])
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

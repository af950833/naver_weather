"""Naver Weather integration for Home Assistant."""
import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api_nweather import NWeatherAPI as API
from .const import DOMAIN, PLATFORMS


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up Naver Weather from configuration.yaml."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Naver Weather from a config entry."""
    hass.data.setdefault(DOMAIN, {"api": {}})
    api = API(hass, entry, len(hass.data[DOMAIN]["api"]) + 1)
    hass.data[DOMAIN]["api"][entry.entry_id] = api

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN]["api"].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]["api"]:
            hass.data.pop(DOMAIN, None)

    return unload_ok

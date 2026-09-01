"""SolaX Cloud integration for Home Assistant."""

import logging
from datetime import timedelta
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_API_REGION,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_INVERTER_SN,
    DOMAIN,
)
from .coordinator import SolaXCloudCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: Final = [Platform.BINARY_SENSOR, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SolaX Cloud from a config entry."""
    client_id = entry.data[CONF_CLIENT_ID]
    client_secret = entry.data[CONF_CLIENT_SECRET]
    api_region = entry.data.get(CONF_API_REGION, "global")
    inverter_sn = entry.data[CONF_INVERTER_SN]
    coordinator = SolaXCloudCoordinator(
        hass,
        client_id=client_id,
        client_secret=client_secret,
        api_region=api_region,
        inverter_sn=inverter_sn,
        update_interval=timedelta(minutes=5),
    )

    # Fetch initial data
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        raise

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

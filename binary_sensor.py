"""Binary sensor platform for SolaX Cloud integration."""

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_INVERTER_SN, DOMAIN

GRID_ISLANDED_STATES = {106, 107, 139}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors from a config entry."""
    async_add_entities(
        [
            SolaXCloudGridConnectedSensor(
                hass.data[DOMAIN][entry.entry_id], entry.data[CONF_INVERTER_SN]
            )
        ]
    )


class SolaXCloudGridConnectedSensor(CoordinatorEntity, BinarySensorEntity):
    """Report whether the inverter is operating in a grid-connected mode."""

    _attr_has_entity_name = True
    _attr_name = "Grid Connected"

    def __init__(self, coordinator, inverter_sn: str) -> None:
        """Initialize the grid connection sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"solax_cloud_{inverter_sn}_grid_connected"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, inverter_sn)},
            manufacturer="SolaX Power",
            name=f"SolaX Inverter {inverter_sn}",
        )

    @property
    def available(self) -> bool:
        """Return whether a device status is available."""
        return self.coordinator.last_update_success and "deviceStatus" in (
            self.coordinator.data or {}
        )

    @property
    def is_on(self) -> bool:
        """Return false only for documented EPS/islanded operating modes."""
        return self.coordinator.data["deviceStatus"] not in GRID_ISLANDED_STATES
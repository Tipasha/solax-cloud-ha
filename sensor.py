"""Sensor platform for SolaX Cloud integration."""

from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, CONF_INVERTER_SN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    inverter_sn = entry.data[CONF_INVERTER_SN]

    sensors = [
        SolaXCloudPowerSensor(
            coordinator, inverter_sn, "MPPTTotalInputPower", "Solar Production Power"
        ),
        SolaXCloudGridPowerSensor(
            coordinator, inverter_sn, "Grid Import Power", exporting=False
        ),
        SolaXCloudGridPowerSensor(
            coordinator, inverter_sn, "Grid Export Power", exporting=True
        ),
        SolaXCloudHomeConsumptionSensor(coordinator, inverter_sn),
        SolaXCloudTotalEnergySensor(
            coordinator, inverter_sn, "totalYield", "Solar Production"
        ),
        SolaXCloudTotalEnergySensor(
            coordinator, inverter_sn, "totalImportEnergy", "Grid Import"
        ),
        SolaXCloudTotalEnergySensor(
            coordinator, inverter_sn, "totalExportEnergy", "Grid Export"
        ),
        SolaXCloudTotalEnergySensor(
            coordinator, inverter_sn, "totalBatteryCharged", "Battery Charged"
        ),
        SolaXCloudTotalEnergySensor(
            coordinator, inverter_sn, "totalBatteryDischarged", "Battery Discharged"
        ),
        SolaXCloudPowerSensor(
            coordinator, inverter_sn, "batteryChargePower", "Battery Charging Power"
        ),
        SolaXCloudPowerSensor(
            coordinator, inverter_sn, "batteryDischargePower", "Battery Discharging Power"
        ),
        SolaXCloudBatteryStateOfChargeSensor(
            coordinator, inverter_sn, "batterySOC", "Battery State of Charge"
        ),
        SolaXCloudBatteryRemainingEnergySensor(
            coordinator, inverter_sn, "batteryRemainingEnergy", "Battery Remaining Energy"
        ),
    ]

    async_add_entities(sensors)


class SolaXCloudSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for SolaX Cloud sensors."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        inverter_sn: str,
        key: str,
        name: str,
        data_key: str | None = None,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.inverter_sn = inverter_sn
        self._key = key
        self._data_key = data_key or key
        self._attr_name = f"SolaX {inverter_sn} {name}"
        self._attr_unique_id = f"solax_cloud_{inverter_sn}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information for this inverter."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.inverter_sn)},
            manufacturer="SolaX Power",
            name=f"SolaX Inverter {self.inverter_sn}",
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self._data_key in (
            self.coordinator.data or {}
        )

    @property
    def native_value(self) -> Any:
        """Return the native value."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._data_key)


class SolaXCloudPowerSensor(SolaXCloudSensorBase):
    """Power sensor for SolaX Cloud."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT


class SolaXCloudGridPowerSensor(SolaXCloudPowerSensor):
    """Expose the appropriate direction of signed grid power."""

    def __init__(self, coordinator, inverter_sn: str, name: str, exporting: bool) -> None:
        """Initialize the directional grid power sensor."""
        direction = "export" if exporting else "import"
        super().__init__(
            coordinator,
            inverter_sn,
            f"grid_{direction}_power",
            name,
            data_key="gridPower",
        )
        self._exporting = exporting

    @property
    def native_value(self) -> float | None:
        """Return exported power or imported power as a positive value."""
        value = super().native_value
        if value is None:
            return None
        signed_power = float(value)
        return max(signed_power, 0) if self._exporting else max(-signed_power, 0)


class SolaXCloudHomeConsumptionSensor(SolaXCloudPowerSensor):
    """Estimate household consumption from the documented energy flows."""

    def __init__(self, coordinator, inverter_sn: str) -> None:
        """Initialize the calculated household consumption sensor."""
        super().__init__(
            coordinator,
            inverter_sn,
            "home_consumption_power",
            "Home Consumption Power",
            data_key="gridPower",
        )

    @property
    def available(self) -> bool:
        """Return whether all values needed for the calculation are available."""
        return self.coordinator.last_update_success and all(
            key in (self.coordinator.data or {})
            for key in (
                "MPPTTotalInputPower",
                "gridPower",
                "batteryChargePower",
                "batteryDischargePower",
            )
        )

    @property
    def native_value(self) -> float | None:
        """Estimate load from solar, grid, and battery power flows."""
        if not self.available:
            return None
        data = self.coordinator.data
        grid_power = float(data["gridPower"])
        return max(
            float(data["MPPTTotalInputPower"] or 0)
            + float(data["batteryDischargePower"] or 0)
            + max(-grid_power, 0)
            - float(data["batteryChargePower"] or 0)
            - max(grid_power, 0),
            0,
        )


class SolaXCloudTotalEnergySensor(SolaXCloudSensorBase):
    """Total energy sensor for SolaX Cloud."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR


class SolaXCloudBatteryStateOfChargeSensor(SolaXCloudSensorBase):
    """Battery state of charge sensor for SolaX Cloud."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE


class SolaXCloudBatteryRemainingEnergySensor(SolaXCloudSensorBase):
    """Battery energy currently available for use."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR


class SolaXCloudStatusSensor(SolaXCloudSensorBase):
    """Status sensor for SolaX Cloud."""

    _attr_state_class = None

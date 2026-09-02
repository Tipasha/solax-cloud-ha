"""Data update coordinator for SolaX Cloud integration."""

import logging
from datetime import timedelta
from typing import Any, Dict

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    SOLAX_DEVICE_INFO_PATH,
    SOLAX_OPENAPI_URLS,
    SOLAX_REALTIME_DATA_PATH,
)

_LOGGER = logging.getLogger(__name__)


def _number(value: Any) -> float:
    """Return a numeric API value, treating missing values as zero."""
    return float(value) if value is not None else 0


async def async_validate_credentials(
    hass: HomeAssistant, client_id: str, client_secret: str, api_region: str
) -> str:
    """Obtain an OAuth access token using SolaX developer credentials."""
    session = async_get_clientsession(hass)
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    try:
        async with session.post(
            f"{SOLAX_OPENAPI_URLS[api_region]}/auth/oauth/token",
            data=payload,
            timeout=10,
        ) as response:
            response_data = await response.json(content_type=None)
    except (aiohttp.ClientError, TimeoutError) as err:
        raise ConnectionError from err

    token = response_data.get("result", {}).get("access_token")
    if response.status != 200 or response_data.get("code") != 0 or not token:
        raise ValueError("SolaX Cloud rejected the developer credentials")
    return token


class SolaXCloudCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch data from SolaX Cloud API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client_id: str,
        client_secret: str,
        api_region: str,
        inverter_sn: str,
        update_interval: timedelta,
    ):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="SolaX Cloud",
            update_interval=update_interval,
        )
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_region = api_region
        self.inverter_sn = inverter_sn
        self._session: aiohttp.ClientSession | None = None
        self._token: str | None = None

    async def _async_login(self) -> str:
        """Login to SolaX Cloud and return auth token."""
        if self._token:
            return self._token

        try:
            self._token = await async_validate_credentials(
                self.hass, self.client_id, self.client_secret, self.api_region
            )
        except ConnectionError as err:
            raise UpdateFailed("Unable to connect to SolaX Cloud") from err
        except ValueError as err:
            raise UpdateFailed("SolaX Cloud rejected the developer credentials") from err
        return self._token

    async def _async_get_inverter_data(self, token: str) -> Dict[str, Any]:
        """Fetch inverter data from SolaX Cloud."""
        try:
            session = async_get_clientsession(self.hass)
            async with session.get(
                f"{SOLAX_OPENAPI_URLS[self.api_region]}{SOLAX_REALTIME_DATA_PATH}",
                params={
                    "snList": self.inverter_sn,
                    "deviceType": 1,
                    "businessType": 1,
                },
                headers={"Authorization": f"bearer {token}"},
                timeout=10,
            ) as resp:
                data = await resp.json(content_type=None)
                if resp.status == 200 and data.get("code") == 10000:
                    records = data.get("result", [])
                    for record in records:
                        if record.get("deviceSn") == self.inverter_sn:
                            return record
                    available_serials = await self._async_get_inverter_serials(token)
                    if available_serials:
                        raise UpdateFailed(
                            "No data was returned for the configured serial number. "
                            f"Available inverter serial numbers: {', '.join(available_serials)}"
                        )
                    raise UpdateFailed(
                        "No inverter devices are authorized for this Developer Portal application"
                    )
                raise UpdateFailed(f"API request failed: {resp.status}")
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Unexpected error fetching data: {err}") from err

    async def _async_get_battery_data(self, token: str) -> Dict[str, Any]:
        """Fetch aggregate battery data associated with the inverter."""
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                f"{SOLAX_OPENAPI_URLS[self.api_region]}{SOLAX_REALTIME_DATA_PATH}",
                params={
                    "snList": self.inverter_sn,
                    "deviceType": 2,
                    "requestSnType": 1,
                    "businessType": 1,
                },
                headers={"Authorization": f"bearer {token}"},
                timeout=10,
            ) as response:
                data = await response.json(content_type=None)
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Connection error: {err}") from err

        if response.status != 200 or data.get("code") != 10000:
            raise UpdateFailed(f"Battery data request failed: {response.status}")

        records = data.get("result", [])
        if not records:
            return {}
        battery_soc_values = [
            _number(record.get("batterySOC"))
            for record in records
            if record.get("batterySOC") is not None
        ]
        return {
            "batteryChargePower": sum(
                max(_number(record.get("chargeDischargePower")), 0) for record in records
            ),
            "batteryDischargePower": sum(
                max(-_number(record.get("chargeDischargePower")), 0) for record in records
            ),
            "totalBatteryCharged": sum(
                _number(record.get("totalDeviceCharge")) for record in records
            ),
            "totalBatteryDischarged": sum(
                _number(record.get("totalDeviceDischarge")) for record in records
            ),
            "batteryRemainingEnergy": sum(
                _number(record.get("batteryRemainings")) for record in records
            ),
            "batterySOC": (
                sum(battery_soc_values) / len(battery_soc_values)
                if battery_soc_values
                else None
            ),
        }

    async def _async_get_inverter_serials(self, token: str) -> list[str]:
        """Return inverter serial numbers authorized for the application."""
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(
                f"{SOLAX_OPENAPI_URLS[self.api_region]}{SOLAX_DEVICE_INFO_PATH}",
                params={"deviceType": 1, "businessType": 1},
                headers={"Authorization": f"bearer {token}"},
                timeout=10,
            ) as response:
                data = await response.json(content_type=None)
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Connection error: {err}") from err

        if response.status != 200 or data.get("code") != 10000:
            raise UpdateFailed(f"Device information request failed: {response.status}")
        return [
            serial
            for record in data.get("result", {}).get("records", [])
            if (serial := record.get("deviceSn"))
        ]

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from SolaX Cloud API."""
        try:
            token = await self._async_login()
            inverter_data = await self._async_get_inverter_data(token)
            battery_data = await self._async_get_battery_data(token)
            return {**inverter_data, **battery_data}
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

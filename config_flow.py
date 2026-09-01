"""Config flow for SolaX Cloud integration."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_API_REGION,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_INVERTER_SN,
    DEFAULT_API_REGION,
    DOMAIN,
)
from .coordinator import async_validate_credentials

_LOGGER = logging.getLogger(__name__)


SETUP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CLIENT_ID): TextSelector(),
        vol.Required(CONF_CLIENT_SECRET): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
        vol.Required(CONF_API_REGION, default=DEFAULT_API_REGION): SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(value="global", label="Global"),
                    SelectOptionDict(value="china", label="China"),
                ]
            )
        ),
        vol.Required(CONF_INVERTER_SN): TextSelector(),
    }
)


class SolaXCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SolaX Cloud."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await async_validate_credentials(
                    self.hass,
                    user_input[CONF_CLIENT_ID],
                    user_input[CONF_CLIENT_SECRET],
                    user_input[CONF_API_REGION],
                )
            except ValueError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected error during SolaX Cloud authentication")
                errors["base"] = "cannot_connect"
            else:
                inverter_sn = user_input[CONF_INVERTER_SN]
                await self.async_set_unique_id(inverter_sn)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"SolaX Cloud ({inverter_sn})", data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=SETUP_SCHEMA,
            errors=errors,
        )

    async def async_step_import(self, import_data: dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_data)

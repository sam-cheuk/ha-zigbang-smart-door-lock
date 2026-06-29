from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_IMEI, PUSH_TOKEN, DOMAIN, FCM_SENDER_ID
from .coordinator import ZigbangClient

_LOGGER = logging.getLogger(__name__)


class ZigbangConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            client = ZigbangClient(
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                imei=user_input.get(CONF_IMEI),
            )
            try:
                await client.async_get_devices()
            except Exception as err:  # noqa: BLE001
                _LOGGER.exception("Unable to connect to Zigbang")
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(user_input[CONF_USERNAME])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_USERNAME],
                    data={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_IMEI: user_input.get(CONF_IMEI),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Optional(CONF_IMEI, default=""): str,
                }
            ),
            errors=errors,
        )

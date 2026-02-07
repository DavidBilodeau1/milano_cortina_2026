"""Config flow for Milano Cortina 2026 Olympics integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    CONF_LOCALE,
    LOCALE_ENGLISH,
    LOCALE_FRENCH,
    AVAILABLE_LOCALES,
    API_BASE_URL,
    API_ENDPOINT,
)

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.
    
    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    locale = data[CONF_LOCALE]
    
    # Test API connection
    url = f"{API_BASE_URL}/{locale}/{API_ENDPOINT}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    raise CannotConnect(f"API returned status {response.status}")
                
                data = await response.json()
                
                # Validate response structure
                if "medalStandings" not in data:
                    raise InvalidData("Invalid API response structure")
                    
        except aiohttp.ClientError as err:
            raise CannotConnect(f"Failed to connect to API: {err}") from err
        except Exception as err:
            raise CannotConnect(f"Unexpected error: {err}") from err
    
    return {"title": f"Milano Cortina 2026 ({locale})"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Milano Cortina 2026 Olympics."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidData:
                errors["base"] = "invalid_data"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_LOCALE])
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(title=info["title"], data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_LOCALE, default=LOCALE_ENGLISH): vol.In(
                    {
                        LOCALE_ENGLISH: "English",
                        LOCALE_FRENCH: "Français",
                    }
                ),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidData(HomeAssistantError):
    """Error to indicate there is invalid data."""


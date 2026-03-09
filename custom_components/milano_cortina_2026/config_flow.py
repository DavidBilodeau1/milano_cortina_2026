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
    CONF_TRACK_OLYMPICS,
    CONF_TRACK_PARALYMPICS,
    LOCALE_ENGLISH,
    LOCALE_FRENCH,
    AVAILABLE_LOCALES,
    API_OLYMPICS_BASE_URL,
    API_PARALYMPICS_BASE_URL,
    API_ENDPOINT,
)

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    locale = data[CONF_LOCALE]
    track_olympics = data.get(CONF_TRACK_OLYMPICS, True)
    track_paralympics = data.get(CONF_TRACK_PARALYMPICS, False)

    # Validate at least one event type is selected
    if not track_olympics and not track_paralympics:
        raise InvalidData("Must select at least one event type (Olympics or Paralympics)")

    headers = {
        "User-Agent": "HomeAssistant/Milano-Cortina-2026",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }

    connector = aiohttp.TCPConnector(force_close=True, enable_cleanup_closed=True)
    timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)

    async with aiohttp.ClientSession(connector=connector) as session:
        # Test Olympics API if selected
        if track_olympics:
            url = f"{API_OLYMPICS_BASE_URL}/{locale}/{API_ENDPOINT}"
            try:
                async with session.get(url, headers=headers, timeout=timeout, ssl=False) as response:
                    if response.status != 200:
                        raise CannotConnect(f"Olympics API returned status {response.status}")

                    response_data = await response.json()

                    # Validate response structure
                    if "medalStandings" not in response_data:
                        raise InvalidData("Invalid Olympics API response structure")

            except aiohttp.ClientError as err:
                _LOGGER.error("Failed to connect to Olympics API: %s", err)
                raise CannotConnect(f"Failed to connect to Olympics API: {err}") from err
            except Exception as err:
                _LOGGER.error("Unexpected error connecting to Olympics API: %s", err)
                raise CannotConnect(f"Unexpected error with Olympics API: {err}") from err

        # Test Paralympics API if selected
        if track_paralympics:
            url = f"{API_PARALYMPICS_BASE_URL}/{locale}/{API_ENDPOINT}"
            try:
                async with session.get(url, headers=headers, timeout=timeout, ssl=False) as response:
                    if response.status != 200:
                        raise CannotConnect(f"Paralympics API returned status {response.status}")

                    response_data = await response.json()

                    # Validate response structure
                    if "medalStandings" not in response_data:
                        raise InvalidData("Invalid Paralympics API response structure")

            except aiohttp.ClientError as err:
                _LOGGER.error("Failed to connect to Paralympics API: %s", err)
                raise CannotConnect(f"Failed to connect to Paralympics API: {err}") from err
            except Exception as err:
                _LOGGER.error("Unexpected error connecting to Paralympics API: %s", err)
                raise CannotConnect(f"Unexpected error with Paralympics API: {err}") from err

    # Build title based on selections
    events = []
    if track_olympics:
        events.append("Olympics")
    if track_paralympics:
        events.append("Paralympics")

    title = f"Milano Cortina 2026 {' + '.join(events)} ({locale})"

    return {"title": title}


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
                # Create unique ID based on locale and event types
                track_olympics = user_input.get(CONF_TRACK_OLYMPICS, True)
                track_paralympics = user_input.get(CONF_TRACK_PARALYMPICS, False)
                unique_id = f"{user_input[CONF_LOCALE]}_{'o' if track_olympics else ''}{'p' if track_paralympics else ''}"

                await self.async_set_unique_id(unique_id)
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
                vol.Required(CONF_TRACK_OLYMPICS, default=True): bool,
                vol.Required(CONF_TRACK_PARALYMPICS, default=False): bool,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidData(HomeAssistantError):
    """Error to indicate there is invalid data."""


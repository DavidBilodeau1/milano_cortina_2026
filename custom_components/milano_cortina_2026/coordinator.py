"""Data update coordinator for Milano Cortina 2026 Olympics."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    CONF_LOCALE,
    CONF_TRACK_OLYMPICS,
    CONF_TRACK_PARALYMPICS,
    API_OLYMPICS_BASE_URL,
    API_PARALYMPICS_BASE_URL,
    API_ENDPOINT,
    UPDATE_INTERVAL_MINUTES,
    EVENT_TYPE_OLYMPICS,
    EVENT_TYPE_PARALYMPICS,
)

_LOGGER = logging.getLogger(__name__)


class OlympicsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Olympics data from the API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.locale = entry.data[CONF_LOCALE]
        self.track_olympics = entry.data.get(CONF_TRACK_OLYMPICS, True)
        self.track_paralympics = entry.data.get(CONF_TRACK_PARALYMPICS, False)
        self.entry = entry

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )

    async def _fetch_event_data(
        self, session: aiohttp.ClientSession, base_url: str, event_type: str
    ) -> dict[str, Any]:
        """Fetch data for a specific event type."""
        url = f"{base_url}/{self.locale}/{API_ENDPOINT}"

        headers = {
            "User-Agent": "HomeAssistant/Milano-Cortina-2026",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
        }

        timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)

        try:
            async with session.get(url, headers=headers, timeout=timeout, ssl=False) as response:
                if response.status != 200:
                    raise UpdateFailed(
                        f"Error communicating with {event_type} API: {response.status}"
                    )

                data = await response.json()

                if "medalStandings" not in data:
                    raise UpdateFailed(f"Invalid {event_type} API response structure")

                # Add event type to the data
                data["event_type"] = event_type
                return data

        except aiohttp.ClientError as err:
            _LOGGER.error("Error communicating with %s API: %s", event_type, err)
            raise UpdateFailed(f"Error communicating with {event_type} API: {err}") from err

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        connector = aiohttp.TCPConnector(force_close=True, enable_cleanup_closed=True)

        combined_data = {}

        try:
            async with async_timeout.timeout(35):
                async with aiohttp.ClientSession(connector=connector) as session:
                    # Fetch Olympics data if enabled
                    if self.track_olympics:
                        olympics_data = await self._fetch_event_data(
                            session, API_OLYMPICS_BASE_URL, EVENT_TYPE_OLYMPICS
                        )
                        combined_data[EVENT_TYPE_OLYMPICS] = olympics_data

                    # Fetch Paralympics data if enabled
                    if self.track_paralympics:
                        paralympics_data = await self._fetch_event_data(
                            session, API_PARALYMPICS_BASE_URL, EVENT_TYPE_PARALYMPICS
                        )
                        combined_data[EVENT_TYPE_PARALYMPICS] = paralympics_data

                    return combined_data

        except Exception as err:
            _LOGGER.error("Unexpected error fetching data: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err


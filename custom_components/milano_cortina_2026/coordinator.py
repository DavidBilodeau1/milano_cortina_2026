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
    API_BASE_URL,
    API_ENDPOINT,
    UPDATE_INTERVAL_MINUTES,
)

_LOGGER = logging.getLogger(__name__)


class OlympicsDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Olympics data from the API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.locale = entry.data[CONF_LOCALE]
        self.entry = entry
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API."""
        url = f"{API_BASE_URL}/{self.locale}/{API_ENDPOINT}"
        
        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status != 200:
                            raise UpdateFailed(
                                f"Error communicating with API: {response.status}"
                            )
                        
                        data = await response.json()
                        
                        if "medalStandings" not in data:
                            raise UpdateFailed("Invalid API response structure")
                        
                        return data
                        
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err


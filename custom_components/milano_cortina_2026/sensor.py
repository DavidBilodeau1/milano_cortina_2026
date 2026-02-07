"""Sensor platform for Milano Cortina 2026 Olympics."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ATTR_RANK,
    ATTR_GOLD,
    ATTR_SILVER,
    ATTR_BRONZE,
    ATTR_TOTAL,
    ATTR_COUNTRY_CODE,
    ATTR_COUNTRY_NAME,
    ATTR_DISCIPLINES,
    ATTR_MEDAL_WINNERS,
    ATTR_TOTAL_EVENTS,
    ATTR_FINISHED_EVENTS,
    ATTR_LAST_UPDATE,
)
from .coordinator import OlympicsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: OlympicsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities: list[SensorEntity] = []
    
    # Add event info sensor
    entities.append(OlympicsEventInfoSensor(coordinator, entry))
    
    # Add a sensor for each country in the medal standings
    if coordinator.data and "medalStandings" in coordinator.data:
        medal_table = coordinator.data["medalStandings"].get("medalsTable", [])
        
        for country_data in medal_table:
            entities.append(OlympicsCountryMedalSensor(coordinator, entry, country_data))
    
    async_add_entities(entities)


class OlympicsEventInfoSensor(CoordinatorEntity, SensorEntity):
    """Sensor for Olympics event information."""

    def __init__(
        self,
        coordinator: OlympicsDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = "Milano Cortina 2026 Event Info"
        self._attr_unique_id = f"{entry.entry_id}_event_info"
        self._attr_icon = "mdi:information"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        
        event_info = self.coordinator.data.get("medalStandings", {}).get("eventInfo", {})
        return event_info.get("finishedEvents")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}
        
        event_info = self.coordinator.data.get("medalStandings", {}).get("eventInfo", {})
        
        return {
            ATTR_TOTAL_EVENTS: event_info.get("totalEvents"),
            ATTR_FINISHED_EVENTS: event_info.get("finishedEvents"),
            ATTR_LAST_UPDATE: event_info.get("dateTime"),
        }


class OlympicsCountryMedalSensor(CoordinatorEntity, SensorEntity):
    """Sensor for a country's medal count."""

    def __init__(
        self,
        coordinator: OlympicsDataUpdateCoordinator,
        entry: ConfigEntry,
        country_data: dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._country_code = country_data.get("organisation")
        self._attr_name = f"{country_data.get('description')} Medals"
        self._attr_unique_id = f"{entry.entry_id}_{self._country_code}_medals"
        self._attr_icon = "mdi:medal"

    @property
    def native_value(self) -> int | None:
        """Return the total medal count."""
        country_data = self._get_country_data()
        if not country_data:
            return None
        
        medals_number = country_data.get("medalsNumber", [])
        for medal_type in medals_number:
            if medal_type.get("type") == "Total":
                return medal_type.get("total", 0)
        
        return 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        country_data = self._get_country_data()
        if not country_data:
            return {}

        # Get total medals breakdown
        medals_number = country_data.get("medalsNumber", [])
        gold = 0
        silver = 0
        bronze = 0

        for medal_type in medals_number:
            if medal_type.get("type") == "Total":
                gold = medal_type.get("gold", 0)
                silver = medal_type.get("silver", 0)
                bronze = medal_type.get("bronze", 0)
                break

        # Get disciplines with medals
        disciplines = []
        for discipline in country_data.get("disciplines", []):
            disciplines.append({
                "code": discipline.get("code"),
                "name": discipline.get("name"),
                "gold": discipline.get("gold", 0),
                "silver": discipline.get("silver", 0),
                "bronze": discipline.get("bronze", 0),
                "total": discipline.get("total", 0),
            })

        # Get medal winners details
        medal_winners = []
        for discipline in country_data.get("disciplines", []):
            for winner in discipline.get("medalWinners", []):
                medal_winners.append({
                    "athlete": winner.get("competitorDisplayName"),
                    "discipline": discipline.get("name"),
                    "event": winner.get("eventDescription"),
                    "medal": winner.get("medalType", "").replace("ME_", ""),
                    "date": winner.get("date"),
                    "gender": winner.get("eventCategory"),
                })

        return {
            ATTR_RANK: country_data.get("rank"),
            ATTR_COUNTRY_CODE: country_data.get("organisation"),
            ATTR_COUNTRY_NAME: country_data.get("description"),
            ATTR_GOLD: gold,
            ATTR_SILVER: silver,
            ATTR_BRONZE: bronze,
            ATTR_TOTAL: gold + silver + bronze,
            ATTR_DISCIPLINES: disciplines,
            ATTR_MEDAL_WINNERS: medal_winners,
        }

    def _get_country_data(self) -> dict[str, Any] | None:
        """Get the country data from coordinator."""
        if not self.coordinator.data:
            return None

        medal_table = self.coordinator.data.get("medalStandings", {}).get("medalsTable", [])

        for country in medal_table:
            if country.get("organisation") == self._country_code:
                return country

        return None


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
    ATTR_EVENT_TYPE,
    EVENT_TYPE_OLYMPICS,
    EVENT_TYPE_PARALYMPICS,
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

    # Track which country codes we've already created entities for (per event type)
    created_countries: dict[str, set[str]] = {
        EVENT_TYPE_OLYMPICS: set(),
        EVENT_TYPE_PARALYMPICS: set(),
    }

    def add_new_countries() -> None:
        """Add sensors for any new countries that have won medals."""
        if not coordinator.data:
            return

        new_entities: list[SensorEntity] = []

        # Process each event type
        for event_type, event_data in coordinator.data.items():
            if not event_data or "medalStandings" not in event_data:
                continue

            medal_table = event_data["medalStandings"].get("medalsTable", [])

            for country_data in medal_table:
                country_code = country_data.get("organisation")
                if country_code and country_code not in created_countries[event_type]:
                    created_countries[event_type].add(country_code)
                    new_entities.append(
                        OlympicsCountryMedalSensor(coordinator, entry, country_data, event_type)
                    )

        if new_entities:
            async_add_entities(new_entities)

    # Add event info sensors (one per event type)
    event_info_sensors = []
    if coordinator.track_olympics:
        event_info_sensors.append(OlympicsEventInfoSensor(coordinator, entry, EVENT_TYPE_OLYMPICS))
    if coordinator.track_paralympics:
        event_info_sensors.append(OlympicsEventInfoSensor(coordinator, entry, EVENT_TYPE_PARALYMPICS))

    async_add_entities(event_info_sensors)

    # Add initial country sensors
    add_new_countries()

    # Register listener to add new countries when data updates
    coordinator.async_add_listener(add_new_countries)


class OlympicsEventInfoSensor(CoordinatorEntity, SensorEntity):
    """Sensor for Olympics event information."""

    def __init__(
        self,
        coordinator: OlympicsDataUpdateCoordinator,
        entry: ConfigEntry,
        event_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._event_type = event_type
        event_name = "Olympics" if event_type == EVENT_TYPE_OLYMPICS else "Paralympics"
        self._attr_name = f"Milano Cortina 2026 {event_name} Event Info"
        self._attr_unique_id = f"{entry.entry_id}_{event_type}_event_info"
        self._attr_icon = "mdi:information"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if not self.coordinator.data or self._event_type not in self.coordinator.data:
            return None

        event_data = self.coordinator.data[self._event_type]
        event_info = event_data.get("medalStandings", {}).get("eventInfo", {})
        return event_info.get("finishedEvents")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data or self._event_type not in self.coordinator.data:
            return {}

        event_data = self.coordinator.data[self._event_type]
        event_info = event_data.get("medalStandings", {}).get("eventInfo", {})

        return {
            ATTR_EVENT_TYPE: self._event_type,
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
        event_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._country_code = country_data.get("organisation")
        self._event_type = event_type
        event_suffix = "Olympics" if event_type == EVENT_TYPE_OLYMPICS else "Paralympics"
        self._attr_name = f"{country_data.get('description')} {event_suffix} Medals"
        self._attr_unique_id = f"{entry.entry_id}_{self._country_code}_{event_type}_medals"
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
            ATTR_EVENT_TYPE: self._event_type,
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
        if not self.coordinator.data or self._event_type not in self.coordinator.data:
            return None

        event_data = self.coordinator.data[self._event_type]
        medal_table = event_data.get("medalStandings", {}).get("medalsTable", [])

        for country in medal_table:
            if country.get("organisation") == self._country_code:
                return country

        return None


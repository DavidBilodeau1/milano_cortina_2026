"""Constants for the Milano Cortina 2026 Olympics integration."""

DOMAIN = "milano_cortina_2026"

# Configuration
CONF_LOCALE = "locale"

# API
API_BASE_URL = "https://www.olympics.com/wmr-owg2026/competition/api"
API_ENDPOINT = "medals"

# Locales
LOCALE_ENGLISH = "ENG"
LOCALE_FRENCH = "FRA"
AVAILABLE_LOCALES = [LOCALE_ENGLISH, LOCALE_FRENCH]

# Update interval
UPDATE_INTERVAL_MINUTES = 5

# Attributes
ATTR_RANK = "rank"
ATTR_GOLD = "gold"
ATTR_SILVER = "silver"
ATTR_BRONZE = "bronze"
ATTR_TOTAL = "total"
ATTR_COUNTRY_CODE = "country_code"
ATTR_COUNTRY_NAME = "country_name"
ATTR_DISCIPLINES = "disciplines"
ATTR_MEDAL_WINNERS = "medal_winners"
ATTR_TOTAL_EVENTS = "total_events"
ATTR_FINISHED_EVENTS = "finished_events"
ATTR_LAST_UPDATE = "last_update"


# Milano Cortina 2026 Olympics - Home Assistant Integration

A custom Home Assistant integration to track medal counts and results from the Milano Cortina 2026 Winter Olympics.

## Features

- 🥇 Track medal counts for all countries
- 🌍 Support for English (ENG) and French (FRA) locales
- 📊 Detailed medal information including:
  - Total medals (gold, silver, bronze)
  - Medal breakdown by discipline
  - Individual medal winners with athlete names and events
  - Country rankings
- 🔄 Automatic updates every 5 minutes
- 📈 Event progress tracking (total events vs finished events)

## Installation

1. Copy the `custom_components/milano_cortina_2026` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration
4. Search for "Milano Cortina 2026 Olympics"
5. Select your preferred language (English or French)

## Entities Created

### Event Info Sensor
- **Entity**: `sensor.milano_cortina_2026_event_info`
- **State**: Number of finished events
- **Attributes**:
  - `total_events`: Total number of events in the Olympics
  - `finished_events`: Number of completed events
  - `last_update`: Last update timestamp from the API

### Country Medal Sensors
For each country with medals, a sensor is created:
- **Entity**: `sensor.<country_name>_medals`
- **State**: Total medal count
- **Attributes**:
  - `rank`: Country's rank in medal standings
  - `country_code`: Three-letter country code (e.g., "ITA", "USA")
  - `country_name`: Full country name
  - `gold`: Number of gold medals
  - `silver`: Number of silver medals
  - `bronze`: Number of bronze medals
  - `total`: Total medal count
  - `disciplines`: List of disciplines with medal counts
  - `medal_winners`: Detailed list of all medal winners with:
    - Athlete name
    - Discipline
    - Event description
    - Medal type (GOLD, SILVER, BRONZE)
    - Date
    - Gender category

## Example Usage with Table Card

You can create a beautiful medal table using the attributes. Here's an example configuration:

```yaml
type: custom:auto-entities
card:
  type: markdown
  content: |
    ## 🏅 Milano Cortina 2026 Medal Standings
    
    | Rank | Country | 🥇 | 🥈 | 🥉 | Total |
    |------|---------|----|----|----|----|
    {% for state in states.sensor 
       if 'milano_cortina_2026' in state.entity_id 
       and state.entity_id != 'sensor.milano_cortina_2026_event_info' -%}
    | {{ state.attributes.rank }} | {{ state.attributes.country_name }} | {{ state.attributes.gold }} | {{ state.attributes.silver }} | {{ state.attributes.bronze }} | {{ state.state }} |
    {% endfor %}
filter:
  include:
    - entity_id: sensor.*_medals
```

## API Information

This integration uses the official Olympics API:
- **Base URL**: `https://www.olympics.com/wmr-owg2026/competition/api`
- **Endpoint**: `/{LOCALE}/medals`
- **Update Interval**: 5 minutes

## Troubleshooting

If you encounter issues:
1. Check your Home Assistant logs for errors
2. Verify internet connectivity
3. Ensure the Olympics API is accessible
4. Try removing and re-adding the integration

## License

This is an unofficial integration and is not affiliated with the International Olympic Committee (IOC).


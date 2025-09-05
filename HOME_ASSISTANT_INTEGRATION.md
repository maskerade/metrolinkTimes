# Home Assistant Integration for Metrolink Times

This guide shows how to integrate Manchester Metrolink real-time data into Home Assistant using the REST sensor platform.

## Quick Start

1. **Run the API** (choose one method):
   ```bash
   # Using Docker (recommended)
   docker run -d -p 5050:5050 -e TFGM_API_KEY="your_api_key" ghcr.io/maskerade/metrolink-times:latest
   
   # Or using Python directly
   TFGM_API_KEY="your_api_key" python -m metrolinkTimes
   ```

2. **Add to Home Assistant** - Copy the configuration from `homeassistant_config.yaml` to your `configuration.yaml`

3. **Replace the host** - Change `your-api-host:5050` to your actual API host (e.g., `192.168.1.100:5050`)

4. **Restart Home Assistant**

## Available Endpoints

### Station Summary
- **URL**: `/homeassistant/station/{station_name}/`
- **Purpose**: Get total tram count and platform overview
- **Example**: `http://localhost:5050/homeassistant/station/Altrincham/`

### Outgoing Trams
- **URL**: `/homeassistant/station/{station_name}/outgoing/`
- **Purpose**: Get outgoing trams with flattened attributes (perfect for the forum example)
- **Example**: `http://localhost:5050/homeassistant/station/Altrincham/outgoing/`

### Incoming Trams
- **URL**: `/homeassistant/station/{station_name}/incoming/`
- **Purpose**: Get incoming trams with flattened attributes
- **Example**: `http://localhost:5050/homeassistant/station/Altrincham/incoming/`

## Response Format

The endpoints return data in Home Assistant's expected format:

```json
{
  "state": 3,
  "attributes": {
    "station_name": "Altrincham",
    "direction": "outgoing",
    "last_updated": "2025-08-31T17:10:21Z",
    "message": "Normal service",
    "dest0": "Piccadilly",
    "status0": "Departing", 
    "wait0": "0",
    "carriages0": "Double",
    "dest1": "Manchester Airport",
    "status1": "Due",
    "wait1": "9", 
    "carriages1": "Single",
    "friendly_name": "Metrolink Altrincham Outgoing",
    "icon": "mdi:train-variant"
  }
}
```

## Station Names

Use the exact station names from the TfGM API. Common stations include:
- `Altrincham`
- `Manchester Airport`
- `Piccadilly`
- `Victoria`
- `Deansgate-Castlefield`
- `MediaCityUK`
- `Chorlton`
- `Bury`

Get the full list: `http://localhost:5050/homeassistant/stations/`

## Handling Spaces in URLs

The TfGM API uses spaces in station names. The REST sensor handles this automatically, but if you need to manually encode URLs:
- `Deansgate-Castlefield` → `Deansgate-Castlefield` (no spaces)
- `Newton Heath and Moston` → `Newton%20Heath%20and%20Moston`

## Example Sensors

After configuration, you'll have these sensors:
- `sensor.metrolink_altrincham_outgoing` - Number of outgoing trams
- `sensor.metrolink_altrincham_incoming` - Number of incoming trams  
- `sensor.next_outgoing_tram` - Next outgoing destination
- `sensor.next_incoming_tram` - Next incoming destination

## Attributes Available

Each sensor provides these attributes:
- `dest0`, `dest1`, `dest2`, `dest3` - Destinations
- `status0`, `status1`, `status2`, `status3` - Status (Due, Departing, etc.)
- `wait0`, `wait1`, `wait2`, `wait3` - Wait times in minutes
- `carriages0`, `carriages1`, `carriages2`, `carriages3` - Single/Double
- `message` - Service messages (engineering works, disruptions, etc.)
- `last_updated` - When data was last refreshed

## Service Messages

The `message` attribute contains important service information like:
- Engineering works notifications
- Service disruptions
- Route changes
- General service updates

Example message:
```
"ENGINEERING WORKS: Friday 5th - Monday 8th September. Altrincham services will operate to Bury ONLY. No Services will operate into Piccadilly Station. Please visit TfGM.com for more info"
```

Access the message in templates:
```yaml
{{ state_attr('sensor.metrolink_altrincham_outgoing', 'message') }}
```

## Troubleshooting

### No Data Returned
- Check your TfGM API key is valid
- Verify the station name is correct (case-sensitive)
- Check API logs: `docker logs <container_name>`

### Sensor Shows "Unknown"
- Verify the API is running and accessible
- Check Home Assistant logs for REST sensor errors
- Test the endpoint directly in a browser

### Old Data
- The API updates every 30 seconds by default
- Home Assistant sensors refresh every 30 seconds
- Check the `last_updated` attribute for data freshness

## Advanced Usage

### Custom Scan Intervals
```yaml
rest:
  - resource: "http://your-api-host:5050/homeassistant/station/Altrincham/outgoing/"
    scan_interval: 15  # Update every 15 seconds
```

### Multiple Stations
```yaml
rest:
  - resource: "http://your-api-host:5050/homeassistant/station/Altrincham/outgoing/"
    # ... Altrincham config
  - resource: "http://your-api-host:5050/homeassistant/station/Piccadilly/outgoing/"
    # ... Piccadilly config
```

### Template Sensors for Complex Logic
```yaml
template:
  - sensor:
      - name: "Next Tram Wait Time"
        state: >
          {% set wait = state_attr('sensor.metrolink_altrincham_outgoing', 'wait0') %}
          {% if wait == '0' %}
            Due
          {% elif wait == '' %}
            No data
          {% else %}
            {{ wait }} min
          {% endif %}
```

This integration solves the exact problem described in the Home Assistant community forum - providing grouped sensor data with flattened attributes for easy access in automations and dashboards!
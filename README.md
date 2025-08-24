# Metrolink Times

Metrolink Times provides a FastAPI-based REST API that serves real-time estimates for tram arrival times on the Manchester Metrolink network. The system uses rolling averages for transit times between stops and dwell times at platforms to provide accurate predictions that adapt to traffic, speed limit changes, and crowding conditions.

## Installation

### Installation with uv (Recommended)

This project uses [uv](https://docs.astral.sh/uv/) for fast, reliable Python package management.

1. **Install uv**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Clone and setup the project**:
```bash
git clone https://github.com/maskerade/metrolinkTimes.git
cd metrolinkTimes
uv sync  # Installs Python 3.12 and all dependencies automatically
```

3. **Run the application**:
```bash
uv run python -m metrolinkTimes
```

### Alternative Installation with pip

If you prefer traditional pip installation:

```bash
# Requires Python 3.12+
pip install -e .
python -m metrolinkTimes
```

### Docker Installation

Build and run with Docker:

```bash
docker build -t metrolink-times .
docker run -p 5000:5000 -v $(pwd)/config:/app/config metrolink-times
```

### Configure

The application looks for configuration files in the following order:
1. `config/metrolinkTimes.conf` (local to project - **recommended**)
2. `metrolinkTimes.conf` (current directory)
3. `/etc/metrolinkTimes/metrolinkTimes.conf` (system-wide)

Create a config file with your TfGM API key:

```json
{
    "Ocp-Apim-Subscription-Key": "your-tfgm-api-key-here",
    "Access-Control-Allow-Origin": "*",
    "port": 5000
}
```

Get your API key from the [TfGM API](https://developer.tfgm.com/). The API **will not work** without a valid TfGM API key.

## Usage

The API runs on port 5000 by default and provides automatic interactive documentation.

### Running the Application

```bash
# Run with uv (recommended)
uv run python -m metrolinkTimes

# Development with auto-reload
python dev.py dev

# Or run uvicorn directly
uv run uvicorn metrolinkTimes.api:app --host 0.0.0.0 --port 5000 --reload

# Run with traditional Python
python -m metrolinkTimes
```

### Development Commands

```bash
# Development server with auto-reload
python dev.py dev

# Run tests
python dev.py test

# Lint code
python dev.py lint

# Format code
python dev.py format
```

### Deployment Modes

The application supports two deployment modes:

**Polling Mode (Default - for containers/servers):**
- Continuously polls TfGM API every second
- Fast API responses with cached data
- Set `METROLINK_MODE=polling` or `"polling_enabled": true` in config

**On-Demand Mode (for AWS Lambda/serverless):**
- Fetches fresh data on each API request
- No background processes
- Set `METROLINK_MODE=lambda` or `"polling_enabled": false` in config

### API Documentation

FastAPI provides automatic interactive documentation:
- **Swagger UI**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc

### /

Returns

```
{
    "paths": ["debug/", "station/"]
}
```

### /debug/

Returns

```
{
  "missingAverages": {
    "edges": [
      <edges without average transit times>
    ],
    "platforms": [
      <platforms without average dwell times>
    ]
  },
  "trams": {
    "departed": {
      <platform name>: [
        {
          "arriveTime": <time arrived at platform>,
          "averageDwell": <average dwell time at platform>,
          "carriages": <Single|Double>,
          "departTime": <time departed platform>,
          "dest": <destination station>,
          "dwellTime": <this trams dwell time at platform>,
          "predictions": {
            <platform name>: <predicted arrival time>
            },
          "via": <station TfGM data says this tram is going via>
        }
      ]
    },
    "here": {
      <platform name>: [
        {
          "arriveTime": <time arrived at platform>,
          "carriages": <Single|Double>,
          "dest": <destination station>,
          "via": <station TfGM data says this tram is going via>,
          "predictions": {
            <platform name>: <predicted arrival time>
            }
        }
      ]
    }
```

Platforms are identified as `<station name>_<platform atco code>`. Trams 'departing' have left the station and are in transet to to the next. Trams 'here' are either arriving at a station (As shown by flashing 'Arriving' on the displays at stations) or are at the platform. Unfortunately, the TfGM data doesn't provide seperate states for these. They do provide an 'arrived' and 'departing' state but the difference between these isn't clear and may be based on timetabled departure times.

### /station/

Returns

```
{
    "stations": ["<station names>/"]
}
```

### /station/\<station name>/

Returns

```
{
    "platforms": ["<platform atco codes>/"]
}
```

Setting `verbose=true` in the query string will return a dict of platforms with the data for each. You can also use the platform quer strings for this data.

### /station/\<station name>/\<platform atco code>/

Returns

```
{
  "averageDwellTime": <average dwell time in secs>,
  "dwellTimes": [
    <5 most recent dwell times in secs>
  ],
  "mapPos": {
    "x": <a vaguely sensible map x co-ordinate>,
    "y": <a vaguely sensible map y co-ordinate>
  },
  "predecessors": {
    <platform that can reach this platform>: {
      "averageTransitTime": <average transit time from predecessor platform to this in secs>,
      "transitTimes": [
        <5 most recent transit times from predecessor platform to this in secs>
      ]
    }
  },
  "message": <message displayed at the bottom of platform displays>,
  "predictions": [
    {
      "carriages": <Single|Double>,
      "curLoc": {
        "platform": <platform name>,
        "status": <dueStartsHere|here|departed>
      },
      "dest": <destination station>,
      "predictedArriveTime": <predicted arrival time>,
      "predictions": {
        <platform name>: <predicted arrival time>
      },
      "via": <station TfGM data says this tram is going via>
    }
  ],
  "here": [
    {
      "arriveTime": <time arrived at platform>,
      "carriages": <Single|Double>,
      "dest": <destination station>,
      "predictions": {
        <platform name>: <predicted arrival time>
      },
      "via": <station TfGM data says this tram is going via>
    }
  ],
  "departed": [
    {
      "arriveTime": <time tram arrived at platform>,
      "averageDwell": <average dwell at platform in secs>,
      "carriages": <Single|Double>,
      "departTime": <time tram departed platform>,
      "dest": <destination station>,
      "dwellTime": <dwell time of this tram at platform>,
      "predictions": {
        <platform name>: <predicted arrival time>
      },
      "via": <station TfGM data says this tram is going via>
    }
  ],
  "updateTime": <time TfGM data says this data was updated>
}
```

The following query strings can be set to `true` or `false` to enable/disable some data items in the returned json.

| parameter       | default | data items this affects                            |
| --------------- | ------- | -------------------------------------------------- |
| pedictions      | true    | predictions, here                                  |
| tramPredictions | true    | predictions within tram's data                     |
| message         | true    | message                                            |
| meta            | false   | mapPos, dwellTimes, averageDwellTime, predecessors |
| departed        | false   | departed                                           |

## Random scripts

### tramGraph.py

Running this on its own will bring up a render of the platforms and their connections to each other

### genStations.py

This is the script that was used to generate stations.json. It requires manually selection which stations feed into others among other things. It's slow, tedious, and almost certainly the wrong way to go about it. Some of the data in stations.json was added manually after using this script. Mainly because once I generated it, I didn't want to face using the script again....

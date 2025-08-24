#!/usr/bin/python3
import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from metrolinkTimes.tfgmMetrolinksAPI import TFGMMetrolinksAPI
from metrolinkTimes.tramGraph import TramGraph

# Configure logging
logFormat = "%(asctime)s %(levelname)s %(pathname)s %(lineno)s %(message)s"
logLevel = logging.INFO  # Changed from ERROR to INFO to see our polling logs
logFile = f"{os.path.dirname(__file__)}/metrolinkTimes.log"

if Path(logFile).parent.exists():
    logging.basicConfig(filename=logFile, format=logFormat, level=logLevel)
else:
    logging.basicConfig(format=logFormat, level=logLevel)


# Pydantic models for API responses
class TramPrediction(BaseModel):
    dest: str
    via: str | None = None
    carriages: str
    curLoc: dict[str, Any]
    predictedArriveTime: datetime
    predictions: dict[str, datetime]


class PlatformData(BaseModel):
    updateTime: datetime
    predictions: list[TramPrediction] | None = None
    here: list[dict[str, Any]] | None = None
    message: str | None = None
    mapPos: dict[str, float] | None = None
    dwellTimes: list[timedelta] | None = None
    averageDwellTime: timedelta | None = None
    predecessors: dict[str, dict[str, Any]] | None = None
    departed: list[dict[str, Any]] | None = None


class StationList(BaseModel):
    stations: list[str]


class PlatformList(BaseModel):
    platforms: list[str]


class DebugInfo(BaseModel):
    missingAverages: dict[str, list[Any]]  # edges are tuples, platforms are strings
    trams: dict[str, dict[str, list[dict[str, Any]]]]
    stations: dict[str, dict[str, dict[str, Any]]] | None = None


class GraphUpdater:
    def __init__(self, graph: TramGraph):
        self.api = TFGMMetrolinksAPI()
        self.graph = graph
        self.stationMappings = {
            "Ashton-under-Lyne": "Ashton-Under-Lyne",
            "Deansgate Castlefield": "Deansgate - Castlefield",
            "Deansgate": "Deansgate - Castlefield",
            "Ashton": "Ashton-Under-Lyne",
            "MCUK": "MediaCityUK",
            "Newton Heath": "Newton Heath and Moston",
            "Victoria Millgate Siding": "Victoria",
            "Rochdale Stn": "Rochdale Railway Station",
            "Trafford Centre": "The Trafford Centre",
            "intu Trafford Centre": "The Trafford Centre",
            "Wythen. Town": "Wythenshawe Town Centre",
        }

    def update(self):
        data = self.api.getData()

        if data is None:
            return

        tramsVia = []

        for station in data:
            for platform in data[station]:
                nodeID = f"{station}_{platform}"
                if nodeID not in self.graph.getNodes():
                    logging.error(f"ERROR: Unknown platform {nodeID}")
                    continue

                pidTramData = []
                message = None
                updateTime = None

                apiPID = data[station][platform][0]
                if not (
                    apiPID["MessageBoard"].startswith("^F0")
                    or (apiPID["MessageBoard"] == "<no message>")
                ):
                    message = apiPID["MessageBoard"]

                if message is not None:
                    message = message.replace("^$", "")

                updateTime = datetime.strptime(
                    apiPID["LastUpdated"], "%Y-%m-%dT%H:%M:%SZ"
                )

                if self.graph.getLastUpdateTime(nodeID) == updateTime:
                    return

                for i in range(4):
                    if apiPID[f"Dest{i}"] != "":
                        stationName = apiPID[f"Dest{i}"]
                        validDests = list(self.graph.getStations()) + [
                            "Terminates Here",
                            "See Tram Front",
                            "Not in Service",
                        ]
                        viaName = None

                        if " via " in stationName:
                            splitName = stationName.split(" via ")
                            stationName = splitName[0]
                            viaName = splitName[1]

                        if stationName in self.stationMappings:
                            stationName = self.stationMappings[stationName]
                        if viaName in self.stationMappings:
                            viaName = self.stationMappings[viaName]
                            if viaName not in tramsVia:
                                tramsVia.append(viaName)

                        if stationName not in validDests:
                            logging.error(f"Unknown station {stationName}")
                            continue
                        if (viaName is not None) and (viaName not in validDests):
                            logging.error(f"Unknown station {viaName}")
                            viaName = None

                        pidTramData.append(
                            {
                                "dest": stationName,
                                "via": viaName,
                                "carriages": apiPID[f"Carriages{i}"],
                                "status": apiPID[f"Status{i}"],
                                "wait": int(apiPID[f"Wait{i}"]),
                            }
                        )

                self.graph.updatePlatformPID(nodeID, pidTramData, message, updateTime)

        self.graph.decodePIDs()
        self.graph.clearOldDeparted()
        self.graph.locateDepartingTrams()
        self.graph.locateTramsAt()
        self.graph.clearNodePredictions()

        self.graph.predictTramTimes(["tramsHere", "tramsDeparted"])
        self.graph.debounceNew()
        self.graph.gatherTramPredictions(["tramsHere", "tramsDeparted"])
        self.graph.locateApproachingTrams()
        self.graph.predictTramTimes(["tramsApproaching"])
        self.graph.gatherTramPredictions(["tramsApproaching"])
        self.graph.locateApproachingTrams()
        self.graph.clearNodePredictions()
        self.graph.gatherTramPredictions(
            ["tramsHere", "tramsDeparted", "tramsApproaching"]
        )
        self.graph.finalisePredictions()
        self.graph.setLocalUpdateTime(datetime.now())

        # Logging stats
        tramsAts = self.graph.getTramsHeres()
        tramsAt = sum(len(tramsAts[node]) for node in tramsAts)

        tramsDeparteds = self.graph.getTramsDeparteds()
        tramsDeparted = sum(len(tramsDeparteds[node]) for node in tramsDeparteds)

        tramsStartings = self.graph.getTramsStarting()
        tramsStarting = sum(len(tramsStartings[node]) for node in tramsStartings)
        platformsStarting = sum(
            1 for node in tramsStartings if len(tramsStartings[node])
        )
        stationsStarting = {
            self.graph.DG.nodes[node]["stationName"]
            for node in tramsStartings
            if len(tramsStartings[node])
        }

        logging.info(f"Nodes without average: {len(self.graph.nodesNoAvDwell())}")
        logging.info(f"Edges without average: {len(self.graph.edgesNoAvTrans())}")
        logging.info(f"Trams at stations: {tramsAt}")
        logging.info(f"Trams departed stations: {tramsDeparted}")
        logging.info(f"Trams yet to start: {tramsStarting}")
        logging.info(
            f"Platforms with trams starting: {platformsStarting}/{len(self.graph.getNodes())}"
        )
        logging.info(
            f"Stations with trams starting ({len(stationsStarting)}/{len(self.graph.getStations())}): {stationsStarting}"
        )
        logging.info(f"Trams are going via {tramsVia}")

    async def update_loop(self):
        while True:
            try:
                logging.info("Starting TfGM API poll cycle")
                self.update()
                logging.info("Completed TfGM API poll cycle")
            except Exception as e:
                logging.error(f"Error in update loop: {e}")
            await asyncio.sleep(1)


# Global instances - initialized lazily
graph = None
graph_updater = None


def get_graph():
    """Get or create the global graph instance"""
    global graph, graph_updater
    if graph is None:
        graph = TramGraph()
        graph_updater = GraphUpdater(graph)
    return graph, graph_updater


def should_use_polling_mode():
    """Check if we should run in polling mode or on-demand mode"""
    # Check environment variable first
    mode = os.getenv("METROLINK_MODE", "").lower()
    if mode in ["polling", "container"]:
        return True
    elif mode in ["ondemand", "lambda"]:
        return False

    # Check config file
    polling_enabled = config.get("polling_enabled", True)
    return polling_enabled


# Load CORS configuration
def load_config():
    # Look for config file in multiple locations (local first, then system)
    config_paths = [
        "config/metrolinkTimes.conf",  # Local to project
        "metrolinkTimes.conf",  # Current directory
        "/etc/metrolinkTimes/metrolinkTimes.conf",  # System-wide
    ]

    for config_path in config_paths:
        try:
            with open(config_path) as conf_file:
                config = json.load(conf_file)
                logging.info(f"Loaded config from {config_path}")
                return config
        except FileNotFoundError:
            continue
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in config file {config_path}: {e}")
            continue

    logging.warning("No config file found, using defaults")
    return {"Access-Control-Allow-Origin": "*", "port": 5000}


config = load_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # Startup
    task = None
    try:
        if should_use_polling_mode():
            logging.info("Starting in polling mode (continuous updates)")
            _, updater = get_graph()
            task = asyncio.create_task(updater.update_loop())
        else:
            logging.info("Starting in on-demand mode (Lambda/serverless)")
            # Just initialize the graph without starting the polling loop
            get_graph()
        yield
    except Exception as e:
        logging.error(f"Failed to start application: {e}")
        # Continue for testing/development
        yield
    finally:
        # Shutdown - cancel the background task if it exists
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


# Create FastAPI app
app = FastAPI(
    title="Metrolink Times API",
    description="Real-time tram arrival predictions for Manchester Metrolink",
    version="2.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.get("Access-Control-Allow-Origin", "*")],
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/", response_model=dict[str, list[str]])
async def root():
    """Get available API paths"""
    return {"paths": ["debug/", "health/", "station/"]}


async def ensure_fresh_data():
    """Ensure we have fresh data - either from polling or on-demand fetch"""
    tram_graph, updater = get_graph()

    if not should_use_polling_mode():
        # On-demand mode: always fetch fresh data
        logging.info("On-demand mode: fetching fresh data from TfGM API")
        updater.update()
        return

    # Polling mode: check if data is fresh
    now = datetime.now()
    lastUpdated = tram_graph.getLocalUpdateTime()

    if lastUpdated is None:
        raise HTTPException(status_code=503, detail="Service not yet initialized")

    updateDelta = now - lastUpdated
    if updateDelta > timedelta(seconds=30):
        raise HTTPException(status_code=503, detail="Service not updating")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        await ensure_fresh_data()
        return "ok"
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}") from e


@app.get("/debug/", response_model=DebugInfo)
async def debug_info(meta: bool = Query(False, description="Include station metadata")):
    """Get debug information about the network state"""
    await ensure_fresh_data()
    tram_graph, _ = get_graph()
    here = tram_graph.getTramsHeres()
    dep = tram_graph.getTramsDeparteds()
    start = tram_graph.getTramsStarting()

    ret = DebugInfo(
        missingAverages={
            "platforms": tram_graph.nodesNoAvDwell(),
            "edges": tram_graph.edgesNoAvTrans(),
        },
        trams={
            "here": {k: here[k] for k in here if here[k] != []},
            "departed": {k: dep[k] for k in dep if dep[k] != []},
            "starting": {k: start[k] for k in start if start[k] != []},
        },
    )

    if meta:
        stations = {}
        for stationName in tram_graph.getStations():
            stations[stationName] = {}
            for platID in tram_graph.getStationPlatforms(stationName):
                nodeID = f"{stationName}_{platID}"
                stations[stationName][platID] = {
                    "x": tram_graph.getMapPos(nodeID)[0],
                    "y": tram_graph.getMapPos(nodeID)[1],
                    "averageDwellTime": tram_graph.getAverageDwell(nodeID),
                    "predecessors": {
                        pNode: {
                            "averageTransit": tram_graph.getAverageTransit(
                                pNode, nodeID
                            )
                        }
                        for pNode in tram_graph.getNodePreds(nodeID)
                    },
                }
        ret.stations = stations

    return ret


@app.get("/station/", response_model=StationList)
async def list_stations():
    """Get list of all stations"""
    await ensure_fresh_data()
    tram_graph, _ = get_graph()
    stations = [f"{station}/" for station in tram_graph.getStations()]
    return StationList(stations=stations)


@app.get("/station/{station_name}/", response_model=dict[str, Any])
async def get_station_info(
    station_name: str,
    verbose: bool = Query(False, description="Return detailed platform data"),
    predictions: bool = Query(True, description="Include predictions"),
    tram_predictions: bool = Query(True, description="Include tram prediction details"),
    message: bool = Query(True, description="Include platform messages"),
    meta: bool = Query(False, description="Include metadata"),
    departed: bool = Query(False, description="Include departed trams"),
):
    """Get information about a specific station"""
    await ensure_fresh_data()
    tram_graph, _ = get_graph()
    if station_name not in tram_graph.getStations():
        raise HTTPException(status_code=404, detail="Station not found")

    if not verbose:
        station_platforms = tram_graph.getStationPlatforms(station_name)
        return {"platforms": [f"{platID}/" for platID in station_platforms]}

    ret = {"platforms": {}}
    for platID in tram_graph.getStationPlatforms(station_name):
        nodeID = f"{station_name}_{platID}"
        platform_data = {"updateTime": tram_graph.getLastUpdateTime(nodeID)}

        if predictions:
            platform_predictions = tram_graph.getNodePredictions()[nodeID]
            if not tram_predictions:
                for tram in platform_predictions:
                    tram.pop("predictions", None)
            platform_data["predictions"] = platform_predictions
            platform_data["here"] = tram_graph.getTramsHeres()[nodeID]

        if message:
            platform_data["message"] = tram_graph.getMessage(nodeID)

        if meta:
            dwellTimes = tram_graph.getDwellTimes()[nodeID]
            averageDwell = timedelta()
            for dwellTime in dwellTimes:
                averageDwell = averageDwell + dwellTime
            if len(dwellTimes) > 0:
                averageDwell = averageDwell / len(dwellTimes)
            else:
                averageDwell = None

            pred = {}
            for pNodeID in tram_graph.getNodePreds(nodeID):
                pred[pNodeID] = {
                    "transitTimes": tram_graph.getTransit(pNodeID, nodeID),
                    "averageTransitTime": tram_graph.getAverageTransit(pNodeID, nodeID)[
                        0
                    ],
                }

            platform_data.update(
                {
                    "mapPos": {
                        "x": tram_graph.getMapPos(nodeID)[0],
                        "y": tram_graph.getMapPos(nodeID)[1],
                    },
                    "dwellTimes": dwellTimes,
                    "averageDwellTime": averageDwell,
                    "predecessors": pred,
                }
            )

        if departed:
            platform_data["departed"] = tram_graph.getTramsDeparteds()[nodeID]

        ret["platforms"][platID] = platform_data

    return ret


@app.get("/station/{station_name}/{platform_id}/", response_model=dict[str, Any])
async def get_platform_info(
    station_name: str,
    platform_id: str,
    predictions: bool = Query(True, description="Include predictions"),
    tram_predictions: bool = Query(True, description="Include tram prediction details"),
    message: bool = Query(True, description="Include platform messages"),
    meta: bool = Query(False, description="Include metadata"),
    departed: bool = Query(False, description="Include departed trams"),
):
    """Get information about a specific platform"""
    await ensure_fresh_data()
    tram_graph, _ = get_graph()
    nodeID = f"{station_name}_{platform_id}"
    if nodeID not in tram_graph.getNodes():
        raise HTTPException(status_code=404, detail="Platform not found")

    ret = {"updateTime": tram_graph.getLastUpdateTime(nodeID)}

    if predictions:
        platform_predictions = tram_graph.getNodePredictions()[nodeID]
        if not tram_predictions:
            for tram in platform_predictions:
                tram.pop("predictions", None)
        ret["predictions"] = platform_predictions
        ret["here"] = tram_graph.getTramsHeres()[nodeID]

    if message:
        ret["message"] = tram_graph.getMessage(nodeID)

    if meta:
        dwellTimes = tram_graph.getDwellTimes()[nodeID]
        averageDwell = timedelta()
        for dwellTime in dwellTimes:
            averageDwell = averageDwell + dwellTime
        if len(dwellTimes) > 0:
            averageDwell = averageDwell / len(dwellTimes)
        else:
            averageDwell = None

        pred = {}
        for pNodeID in tram_graph.getNodePreds(nodeID):
            pred[pNodeID] = {
                "transitTimes": tram_graph.getTransit(pNodeID, nodeID),
                "averageTransitTime": tram_graph.getAverageTransit(pNodeID, nodeID)[0],
            }

        ret.update(
            {
                "mapPos": {
                    "x": tram_graph.getMapPos(nodeID)[0],
                    "y": tram_graph.getMapPos(nodeID)[1],
                },
                "dwellTimes": dwellTimes,
                "averageDwellTime": averageDwell,
                "predecessors": pred,
            }
        )

    if departed:
        ret["departed"] = tram_graph.getTramsDeparteds()[nodeID]

    return ret

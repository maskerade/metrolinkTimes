#!/usr/bin/env python3

import http.client
import json
import logging
from time import sleep


class TFGMMetrolinksAPI:
    def __init__(self):
        # Look for config file in multiple locations (local first, then system)
        config_paths = [
            "config/metrolinkTimes.conf",  # Local to project
            "metrolinkTimes.conf",  # Current directory
            "/etc/metrolinkTimes/metrolinkTimes.conf",  # System-wide
        ]

        self.conf = {"Ocp-Apim-Subscription-Key": None}

        for config_path in config_paths:
            try:
                with open(config_path) as conf_file:
                    self.conf = json.load(conf_file)
                    logging.info(f"Loaded config from {config_path}")
                    break
            except FileNotFoundError:
                continue
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON in config file {config_path}: {e}")
                continue
        else:
            logging.warning("No config file found. Checked: " + ", ".join(config_paths))
            logging.warning("API will not work without TfGM API key")

    def getData(self):
        if not self.conf.get("Ocp-Apim-Subscription-Key"):
            logging.warning("No TfGM API key configured, returning None")
            return None

        try:
            logging.info("Fetching data from TfGM API at api.tfgm.com/odata/Metrolinks")
            headers = {
                # Request headers
                "Ocp-Apim-Subscription-Key": self.conf["Ocp-Apim-Subscription-Key"],
            }
            conn = http.client.HTTPSConnection("api.tfgm.com")
            conn.request("GET", "/odata/Metrolinks", "{body}", headers)
            response = conn.getresponse()

            logging.info(f"TfGM API response status: {response.status}")

            data = json.loads(response.read().decode("utf-8"))
            conn.close()

            retData = {}
            for platform in data["value"]:
                sl = platform["StationLocation"]
                if sl not in retData:
                    retData[sl] = {}

                ac = platform["AtcoCode"]
                if platform["AtcoCode"] not in retData[sl]:
                    retData[sl][ac] = []

                retData[sl][ac].append(platform)

            logging.info(
                f"Successfully processed TfGM data: {len(retData)} stations, {len(data['value'])} platforms"
            )
            return retData

        except Exception as e:
            logging.error(f"Error fetching TfGM data: {e}")
            return None


def dataTest(api):
    data = api.getData()

    with open("/tmp/metrolink.json", "w") as outfile:
        json.dump(data, outfile)

    stations = data.keys()
    print(len(stations))

    # directions = set([s["Direction"] for s in data["value"]])
    # print(directions)

    # updated = set([s["LastUpdated"] for s in data["value"]])
    # print(updated)

    # stat0 = set([s["Status0"] for s in data["value"]])
    # print(stat0)


def printEvents(api):
    data = api.getData()

    print("================")

    for station in data:
        for platform in data[station]:
            pid = data[station][platform][0]
            for tram in [0, 1, 2, 3]:
                if pid[f"Status{tram}"] not in ["Due", ""]:
                    print(
                        "{} to {} {} {}".format(
                            pid[f"Carriages{tram}"],
                            pid[f"Dest{tram}"],
                            pid[f"Status{tram}"],
                            station,
                        )
                    )


def main():
    api = TFGMMetrolinksAPI()
    while True:
        printEvents(api)
        sleep(10)
    # dataTest(api)


if __name__ == "__main__":
    main()

"""
Fetch Official SXSW events, geocode them, and write to `events.json`.

Events that have been modified are re-geocoded.

Events that have no `venue_address` are ignored.
"""
import json
import pdb
from pprint import pprint as print

import agolutil
import requests

from secrets import AGOL_CREDENTIALS, SXSW_TOKEN, SXSW_ENDPOINT

# filename where events data is stored
FNAME = "events.json"

# fields in the even object that we evaluate for changes
COMPARE_FIELDS = ["event_id", "event_name", "event_type", "venue_name", "venue_address", "venue_capacity", "start_time", "end_time", "url"]

# agol feature service
SERVICE_ID = "99ca53094fcf4d868d2bb67975b97556"
LAYER_ID = 0

def compare_events(new, old):
    """
    Identify new and changed events.
    """
    events = []

    for en in new:
        matched = False
        eid = en.get("event_id")
         
        if not eid:
            continue

        for eo in old:
            if eo.get("event_id") == eid:
                # match found
                matched = True

                diff = [en[field] for field in COMPARE_FIELDS if eo[field] != en[field]]
                    
                if diff:
                    matched = False
                
                break

        # we want to preserve old events, because they have already been geocoded
        # if the event is new/changed, we drop the old event so that the new/changed can be geocoded
        if matched:
            events.append(eo)
        else:
            events.append(en)

    return events


def save_events(events, fname):
    with open(fname, "w") as fout:
        fout.write(json.dumps(events))


def load_events(fname):
    with open(fname, "r") as fin:
        return json.loads(fin.read())


def get_events(token, url):
    headers = {"Authorization" : f"Token token=\"{token}\""}
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    return res.json()



def get_agol_token(auth):

    url = "https://austin.maps.arcgis.com/sharing/rest/generateToken"

    params = {
        "username": auth["user"],
        "password": auth["password"],
        "referer": "https://www.arcgis.com",
        "f": "pjson",
    }

    res = requests.post(url, params=params)
    res.raise_for_status()
    res = res.json()
    return res.get("token")


def get_address(token, address):
    url = "http://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"

    res = requests.get(url, params={"token" : token})

    params = {
        "referer": "https://www.arcgis.com",
        "f": "pjson",
        "address" : address,
        "city" : "Austin",
        "region" : "Texas",
        "maxLocations" : 1
    }

    res = requests.get(url, params)
    res.raise_for_status()
    return res.json()


def main():
    events_old = load_events(FNAME)

    events_new = get_events(SXSW_TOKEN, SXSW_ENDPOINT)

    events = compare_events(events_new, events_old)

    token = get_agol_token(AGOL_CREDENTIALS)

    for e in events:
        
        if e.get("geocode_status"):
            # skip addresses that have already been attempted
            continue

        address = e.get("venue_address")

        if not address:
            # skip events that are missing an address
            continue

        agol_response = get_address(token, address)

        if agol_response.get("candidates"):
            """
            Geocode status codes:
            0 / null: not processed
            1: match found
            9: no result found
            """
            geocode = agol_response["candidates"][0]
            e["geocode_status"] = 1
            e["location"] = geocode["location"]
            e["match_score"] = geocode["score"]
            e["found_address"]= geocode["address"]
            print(geocode["score"])
        else:
            print(f"FAIL: {address}")
            e["geocode_status"] = 9

        save_events(events, FNAME)

    return len(events)

if __name__ == "__main__":
    results = main()
    print(f"{results} events processed.")
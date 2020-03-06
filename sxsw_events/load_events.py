"""
Upload SXSW Official Events to AGOL feature service.

Events which already have an OBJECTID are skipped.

Events which have changed will not have an OBJECTID. The object ID was dropped in `get_events.py`
"""
import json
import pdb
from pprint import pprint as print

import agolutil
import requests

from secrets import AGOL_CREDENTIALS

# filename where events data is stored
FNAME = "events.json"

# fields in the event object that we push to feature service
DESTINATION_FIELDS = ["event_id", "event_name", "event_type", "venue_name", "venue_address", "venue_capacity", "start_time", "end_time", "url"]

# agol feature service
SERVICE_ID = "99ca53094fcf4d868d2bb67975b97556"
LAYER_ID = 0



def save_events(events, fname):
    with open(fname, "w") as fout:
        fout.write(json.dumps(events))


def load_events(fname):
    with open(fname, "r") as fin:
        return json.loads(fin.read())


def get_layer(service_id, layer_id, auth):

    return agolutil.get_item(
        auth=auth,
        service_id=service_id,
        layer_id=layer_id,
        item_type="layer",
    )

def delete_features(layer, events):
    """
    identify which features (if any) are no longer in the events data, and delete them
    events which have already been created will have an "OBJECTID" field
    new/changed events will not
    """
    existing_features = layer.query(
        return_geometry=False, out_fields="OBJECTID"
    )

    if not existing_features:
        return None

    oids = [
        str(f.attributes.get("OBJECTID")) for f in existing_features.features
    ]

    delete_oids = []

    for oid in oids:
        matched = False
        for e in events:
            # identify existing features
            if str(e.get("OBJECTID")) == oid:
                matched = True
                break

        # feature not found in events data, so delete it
        if not matched:
            delete_oids.append(oid)

    if not delete_oids:
        return None

    # format string of OIDs for AGOL query
    deletes = ", ".join(delete_oids)

    # delete features
    res = layer.delete_features(deletes=deletes)
    return res


def feature_collection(events):
    """
    Construct an ArcGIS Feature collection that can be sent to AGOL as a new feature.
    
    Feature is saved to events data under `feature` key.

    Events with no geocode (`location`) are ignored
    """
    for e in events:

        if not e.get("location"):
            #skip records with no geocode
            continue

        feature = {
            "attributes": {},
            "geometry": {"spatialReference": {"wkid": 4326}}, # 4326 = WGS84
        }
        
        feature["attributes"] = {k:v for (k,v) in e.items() if k in DESTINATION_FIELDS}
        

        feature["geometry"]["x"] = e.get("location").get("x")
        feature["geometry"]["y"] = e.get("location").get("y")
        e["feature"] = feature

    return events


def add_event(layer, event):

    res = layer.edit_features(adds=[event])

    if not res.get("addResults"):
        print("ERROR")
        return None
    else:
        print("OK")
        return res.get("addResults")[0].get("objectId")
    

def main():
    events = load_events(FNAME)

    layer = get_layer(SERVICE_ID, LAYER_ID, AGOL_CREDENTIALS)
    
    delete_response = delete_features(layer, events)
    
    features = feature_collection(events)

    features_added = 0
    features_failed = 0

    for e in events:
        if not e.get("feature") or e.get("OBJECTID"):
            # skip features which already exist
            # also skip events with no geocode, and hence, no 'feature'
            continue

        # create feature in agol
        # if the feature fails to add, the object ID will be None
        object_id = add_event(layer, e.get("feature"))
        

        e["OBJECTID"] = object_id

        if not object_id:
            features_failed +=1
        else:
            features_added +=1
        # we don't need to save the feature data, so remove it
        e.pop("feature")
        save_events(events, FNAME)
    return len(events), features_added, features_failed

if __name__ == "__main__":
    features_processed, features_added, features_failed = main()
    print(f"{features_processed} events processed. {features_added} features created. {features_failed} failed.")
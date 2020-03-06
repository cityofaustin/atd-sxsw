# SXSW Events

This code extracts official SXSW events, geocodes them, and uploads them to an ArcGIS Feature Service.

## Run the Scripts

*Requires python v3.6+*

1. Install the requirements from `requirements.txt` in your Python environment. 

```bash
$ pip install -r requirements.txt
```

2. Create a `secrets.py` file following the `secrets_template.py` structure. Save it in the same directory as these scripts.


3. Run `get_events.py` to download and geocode the events. Events are written to `events.json`.

The first time you run this, it will take a while to geocode all the events. Future runs will only geocode new/modified events.

4. In `load_events.py`, update with the `SERVICE_ID` and `LAYER_ID` variables to match the destination feature service in ArcGIS Online. Your feature service should match the schema of the data returned by the SXSW event api. In 2020, it was:

```
- OBJECTID (type: esriFieldTypeOID, alias: OBJECTID, SQL Type: sqlTypeOther, length: 0, nullable: false, editable: false)
- event_id (type: esriFieldTypeString, alias: event_id, SQL Type: sqlTypeOther, length: 50, nullable: true, editable: true)
- event_name (type: esriFieldTypeString, alias: event_name, SQL Type: sqlTypeOther, length: 255, nullable: true, editable: true)
- event_type (type: esriFieldTypeString, alias: event_type, SQL Type: sqlTypeOther, length: 50, nullable: true, editable: true)
- venue_name (type: esriFieldTypeString, alias: venue_name, SQL Type: sqlTypeOther, length: 50, nullable: true, editable: true)
- venue_address (type: esriFieldTypeString, alias: venue_address, SQL Type: sqlTypeOther, length: 50, nullable: true, editable: true)
- venue_capacity (type: esriFieldTypeInteger, alias: venue_capacity, SQL Type: sqlTypeOther, nullable: true, editable: true)
- start_time (type: esriFieldTypeDate, alias: start_time, SQL Type: sqlTypeOther, length: 8, nullable: true, editable: true)
- end_time (type: esriFieldTypeDate, alias: end_time, SQL Type: sqlTypeOther, length: 8, nullable: true, editable: true)
- url (type: esriFieldTypeString, alias: url, SQL Type: sqlTypeOther, length: 255, nullable: true, editable: true)
```

5. Run `load_events.py` to create the event features on ArcGIS Online. Any features which are not found in `events.json` will be deleted. New and changed events will then be added. These changes will only be detected/handled as expected if you run `get_events.py` *before* running `load_events.py`.

The first time you run this, it will take a while to load each event (We load them individually so that we can capture the feature's `OBJECTID`). On future runs, only new/modified features will be loaded.

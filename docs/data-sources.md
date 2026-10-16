# Data sources

Live positions can come from more than one feed at once. `POSITION_SOURCES`
lists the enabled providers in priority order; when there's more than one we
fetch them concurrently and merge the results by `icao24` (see
[Merging](#merging-multiple-sources) below).

## OpenSky Network (live positions)

Base url: `https://opensky-network.org/api`.

The endpoint we use is `/states/all`, optionally clipped with
`lamin/lomin/lamax/lomax`. It returns a list of state vectors - one per
aircraft. We map those into `StateVector` in `providers/opensky.py`.

Field order in each state vector row (the format has been stable):

```
0  icao24            7  baro_altitude      14 squawk
1  callsign          8  on_ground          15 spi
2  origin_country    9  velocity           16 position_source
3  time_position    10  true_track
4  last_contact     11  vertical_rate
5  longitude        12  sensors
6  latitude         13  geo_altitude
```

### Rate limits

Anonymous access gets a small daily credit budget (a few hundred
requests). Authenticated access through an OAuth2 client is much larger.
If you're going to run this continuously, register an API client and put
the id/secret in `.env`.

Credits are the real limit, and they get spent by two things: how often we
poll (`POSITION_REFRESH_SECONDS`) and how much we ask for. A whole-world
`/states/all` costs several times what a boxed one does, so set
`OPENSKY_BOUNDS` to the region you care about (format
`lamin,lomin,lamax,lomax`). Whole-world polling every 15s will exhaust the
daily quota in well under an hour even with credentials; a boxed feed at
30-60s runs all day.

The provider fetches a token via the OpenSky keycloak endpoint and reuses
it until it's about to expire. Credentials are optional - without them we
just call anonymously.

If we hit a 429 the provider raises `ProviderError`, the refresh loop logs
it, records an error row, and tries again next interval. It does not crash.

### What it does not give us

- No schedule data (scheduled/actual departure times). `/states/all` is
  purely "where is this aircraft right now".
- No reliable origin/destination. There's `/flights/aircraft` which gives
  estimated departure/arrival airports for flights in roughly the last
  day, but those are estimates and only cover recent history. We use it
  as a best-effort route lookup and never treat the result as certain.

## adsb.lol (live positions)

Base url: `https://api.adsb.lol`. This is a community network of ADS-B
receivers serving a readsb/tar1090 style JSON api. It's the second live
source and, unlike OpenSky, needs no account or key.

We use `/v2/point/{lat}/{lon}/{radius_nm}` for a circular area and
`/v2/mil` for the global military feed (opt in with `ADSB_MILITARY`). The
response is `{"ac": [...], "now", "total", ...}`; we map each entry in
`ac` into `StateVector` in `providers/adsb.py`.

readsb reports aviation units, so we convert on the way in: feet to
meters, knots to m/s, feet-per-minute to m/s. `alt_baro` can be the string
`"ground"`, which we surface as `on_ground=True` with no altitude.

Notable readsb fields we currently use:

```
hex         icao24               gs          ground speed (knots)
flight      callsign             track       heading (deg)
lat / lon   position             baro_rate   climb rate (ft/min)
alt_baro    barometric altitude  squawk      transponder code
alt_geom    geometric altitude   seen        secs since last message
                                 seen_pos    secs since last position
```

Two quirks worth knowing:

- there is **no whole-world endpoint**. Give it an area via `OPENSKY_BOUNDS`
  (reused when set) or `ADSB_CENTER` + `ADSB_RADIUS_NM`. Without either, the
  source returns nothing rather than guessing.
- some deployments reject the default `httpx` user agent with a 403, so we
  send an identifying `ADSB_USER_AGENT`.

## Merging multiple sources

`providers/multi.py` fans one fetch out across every enabled source and
merges the answers in `providers/merge.py`. The rules:

- group by `icao24`; per aircraft the most recent fix (`time_position`,
  then `last_contact`) becomes the base, and ties go to the higher-priority
  source (earlier in `POSITION_SOURCES`).
- fill the base's still-empty fields from the other sources, so a fresher
  feed that happens to omit a field can't blank out one we already had.
- a source that errors (rate limit, timeout, 5xx) is logged and skipped.
  We only raise `ProviderError` when *every* source fails, which is what
  the refresh loop reacts to.

That last rule is the whole point: an OpenSky 429 no longer means an empty
map as long as another feed is configured and healthy.

## Airports (OurAirports CSV, optional)

Set `AIRPORTS_DATASET_PATH` to an OurAirports `airports.csv` export.
`providers/airport_data.py` loads it once and indexes by ICAO and IATA.

Without the file, airport search and lookup return empty. That's on
purpose - shipping a fake airport list would be worse than admitting we
don't have one.

## Aircraft identities (OpenSky database CSV, optional)

Set `AIRCRAFT_DATASET_PATH` to the OpenSky aircraft database export
(`aircraftDatabase.csv`). `providers/aircraft_data.py` loads it once and
indexes by icao24.

On each persist pass we look up the aircraft we've heard from and fill in
`registration`, `type_code`, `model` and `operator` - but only when those
fields are still empty, so anything observed live always wins.

Header casing has drifted between OpenSky exports, so columns are matched
case-insensitively. Without the file, enrichment is simply skipped.

## Routes, identities and photos (adsbdb)

Base url: `https://api.adsbdb.com`, no key. `providers/adsbdb.py` uses two
endpoints:

- `/v0/callsign/{callsign}` gives the airline plus origin and destination
  airports, each with icao/iata codes, names, city and coordinates. This is
  the main route source now; OpenSky's flight history is only a fallback.
- `/v0/aircraft/{icao24}` gives registration, type, manufacturer, operator
  and a photo url.

Both are looked up lazily when someone opens an aircraft, never in bulk -
that would be thousands of requests. Results are cached in memory for hours
(routes 6h, frames 24h, misses 1h) because they barely change. Whatever
identity we learn is written back onto the aircraft row, but only into
fields that are still empty, so live observations still win.

Set `ADSBDB_ENABLED=false` to keep everything local. If adsbdb is down the
detail view still renders, just without the extra fields.

## Adding a source

1. Implement `FlightDataProvider` in `providers/`.
2. Normalize into `StateVector` (see `utils/validation.py` and
   `utils/coordinates.py` for the shared helpers).
3. Register it in `position_service._KNOWN_SOURCES` so `POSITION_SOURCES`
   can name it.

Because routes and services only ever see `StateVector`, nothing else has
to change - and if you list the new source alongside existing ones, the
merge layer wires it in for free.

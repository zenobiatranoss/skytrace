# Architecture

## Layers

The backend is split so that changing a data source doesn't ripple through
the whole app.

```
api/routes      -> http endpoints, thin. parse input, call a service
services        -> the actual logic: positions, tracks, search, flights
providers       -> talk to external data sources (opensky, airport csv)
repositories    -> all database reads and writes
models          -> sqlalchemy tables
schemas         -> pydantic shapes crossing the api boundary
cache           -> in-memory current state + small ttl cache
websocket       -> push updates to connected clients
tasks           -> scheduled jobs (cleanup, one-shot refresh)
```

The rule of thumb: a route never touches the database or a provider
directly, and a provider never knows about http or the database.

## The position flow

1. `data_refresh_service` polls the provider on a timer
   (`POSITION_REFRESH_SECONDS`).
2. The normalized `StateVector` list replaces the in-memory
   `aircraft_cache`. Clients always read the cache - we never make one
   upstream request per request or per aircraft.
3. Connected websocket clients get the whole snapshot pushed after each
   refresh. The client replaces its aircraft set; it doesn't merge deltas.
4. Roughly once a minute, the cache is persisted: identities are touched,
   the active flight moves forward, and a track point is stored if one is
   due for that aircraft.

Track points aren't stored on every update. `track_service` samples at most
one point per aircraft per minute, which is enough to draw a believable
path and keeps the table from ballooning. Old points age out via the
cleanup job.

## Providers

`FlightDataProvider` (in `providers/base.py`) is the contract. OpenSky is
the current implementation. Adding another source means implementing that
interface and pointing `position_service` at it.

Airport data comes from a separate provider that reads an OurAirports CSV
if one is configured. Without it, airport lookups return nothing - we don't
ship a hardcoded list pretending to be authoritative.

## Freshness

Every position carries `last_contact` from the source. `age_seconds` and
`is_stale` are derived from it. A missing field is `null` end to end. This
is deliberate: the UI must be able to say "we don't know" instead of
filling the gap.

## Why SQLite

It's enough for a single-instance deployment and zero setup. Everything
talks to the database through repositories and SQLAlchemy, so swapping to
Postgres later is a config change plus a migration, not a rewrite.

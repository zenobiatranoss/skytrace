# SkyTrace

A small flight tracker. Live aircraft on a world map, click one to see its
details and the path it has flown, plus a few warnings for odd stuff like
emergency squawks.

Let's be honest about it: the idea isn't special, and this is nowhere near
the real thing. FlightAware (https://www.flightaware.com) and the sites like
it do all of this far better, with more data and better coverage. This is a
hobby project, mostly an excuse to see what you can pull off with free,
public ADS-B data.

That data comes from a couple of public feeds (adsb.lol, and OpenSky when
it's not rate limited), merged so that one source being down doesn't empty
the map. If a field is missing it stays missing - we don't make values up,
and a route is always from aircraft we actually watched, never a straight
line between two guessed airports.

## Running it

    cp .env.example .env
    ./scripts/dev.sh

Backend lands on http://localhost:8000, frontend on http://localhost:5173,
API docs at http://localhost:8000/docs. Tests run with ./scripts/test.sh.

backend/ is Python + FastAPI, frontend/ is React + TypeScript + MapLibre.
The longer notes live in docs/.

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

## Used for OSINT

This is an OSINT tool. Everything it shows is open, public data - ADS-B
broadcasts that aircraft send out in the clear, plus public reference
records for callsigns, routes and airframes. Nothing here comes from a
private or restricted source, and there's no scraping behind a login. It's
meant for open-source intelligence work, research, situational awareness
and just learning what free aviation data can do. How you use it is up to
you, so keep it legal where you are.

## Running it

    cp .env.example .env
    ./scripts/dev.sh

Backend lands on http://localhost:8000, frontend on http://localhost:5173,
API docs at http://localhost:8000/docs. Tests run with ./scripts/test.sh.

backend/ is Python + FastAPI, frontend/ is React + TypeScript + MapLibre.
The longer notes live in docs/.

## Deploying

The Dockerfile builds the frontend and serves it from the backend, so the
whole thing runs as one web service. render.yaml is a Render Blueprint that
sets that up: in the Render dashboard pick New > Blueprint, point it at this
repo, and it reads the file and deploys. Free services spin down after a
while without traffic and wake on the next visit.

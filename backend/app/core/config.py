from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# the repo root, so .env is found whether we're started from backend/ or
# the project root (both are normal here)
_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ROOT_ENV),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SkyTrace"
    debug: bool = False
    log_level: str = "INFO"

    # sqlite while we're small, swap the url once load grows
    database_url: str = "sqlite:///./skytrace.db"

    # opensky lets anonymous users in, but the daily credit budget is tiny.
    # credentials are optional and only widen the limits + add state vectors.
    opensky_base_url: str = "https://opensky-network.org/api"
    opensky_token_url: str = (
        "https://auth.opensky-network.org/auth/realms/opensky-network/"
        "protocol/openid-connect/token"
    )
    opensky_client_id: str = ""
    opensky_client_secret: str = ""
    opensky_timeout: float = 20.0
    # clip the feed to a box to stay inside the daily credit budget: a boxed
    # /states/all costs a fraction of the whole-world call. format is
    # "lamin,lomin,lamax,lomax"; empty means the whole world.
    opensky_bounds: str = ""

    # which position feeds to use, in priority order (first wins ties).
    # "opensky" and "adsb" are the known ones; more than one is merged.
    position_sources: str = "opensky"

    # adsb: any readsb/tar1090 style json api. adsb.lol runs one in the open
    # and needs no key, so it works as a second source right away.
    adsb_base_url: str = "https://api.adsb.lol"
    # these feeds 403 the default httpx agent, so we identify ourselves
    adsb_user_agent: str = "SkyTrace/0.1"
    # adsb.fi's open data feed, a regional add-on (250nm per query)
    adsbfi_base_url: str = "https://opendata.adsb.fi"
    # readsb has no whole-world feed, so it needs an area. when no opensky
    # bounds are set we fall back to this "lat,lon" center and radius.
    adsb_center: str = ""
    adsb_radius_nm: int = 250
    # also pull adsb's military feed (globally scoped, small)
    adsb_military: bool = False

    # adsbdb supplies routes, aircraft identity and photos, no key required.
    # set adsbdb_enabled=false to keep everything local / csv only.
    adsbdb_enabled: bool = True
    adsbdb_base_url: str = "https://api.adsbdb.com"
    adsbdb_timeout: float = 10.0

    # optional local dataset (ourAirports csv export). when missing, airport
    # lookups simply come back empty instead of us making up entries
    airports_dataset_path: str = ""
    # optional opensky aircraft database export, used to fill in registration,
    # type and operator on the aircraft we track
    aircraft_dataset_path: str = ""

    # how often the background refresh pulls fresh positions. keep this in
    # step with the opensky credit budget - a slower poll stretches the day.
    position_refresh_seconds: int = 30
    # a position older than this gets flagged as stale in the ui
    position_stale_seconds: int = 60
    # how long recorded track points stick around
    history_retention_hours: int = 24

    # anomaly detection. the thresholds are signals worth a look, not proof.
    anomaly_enabled: bool = True
    # keep an anomaly "active" this long after it was last seen so brief
    # events don't flicker in and out of the feed
    anomaly_hold_seconds: int = 180
    # window of recent movement we keep per aircraft for pattern checks
    anomaly_history_minutes: int = 10

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def opensky_bounds_tuple(self) -> tuple[float, float, float, float] | None:
        parts = [p.strip() for p in (self.opensky_bounds or "").split(",") if p.strip()]
        if len(parts) != 4:
            return None
        try:
            lamin, lomin, lamax, lomax = (float(p) for p in parts)
        except ValueError:
            return None
        return (lamin, lomin, lamax, lomax)

    @property
    def position_source_list(self) -> list[str]:
        return [s.strip().lower() for s in self.position_sources.split(",") if s.strip()]

    @property
    def adsb_center_tuple(self) -> tuple[float, float] | None:
        parts = [p.strip() for p in (self.adsb_center or "").split(",") if p.strip()]
        if len(parts) != 2:
            return None
        try:
            lat, lon = (float(p) for p in parts)
        except ValueError:
            return None
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return None
        return (lat, lon)


settings = Settings()

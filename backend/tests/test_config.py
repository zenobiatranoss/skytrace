from app.core.config import Settings


def test_bounds_parses_valid_box():
    settings = Settings(opensky_bounds="35,-12,60,30")
    assert settings.opensky_bounds_tuple == (35.0, -12.0, 60.0, 30.0)


def test_bounds_empty_means_whole_world():
    assert Settings(opensky_bounds="").opensky_bounds_tuple is None


def test_bounds_rejects_malformed_values():
    assert Settings(opensky_bounds="35,-12,60").opensky_bounds_tuple is None
    assert Settings(opensky_bounds="a,b,c,d").opensky_bounds_tuple is None


def test_position_sources_defaults_to_opensky():
    assert Settings().position_source_list == ["opensky"]


def test_position_sources_parses_and_lowercases():
    settings = Settings(position_sources=" ADSB , opensky ")
    assert settings.position_source_list == ["adsb", "opensky"]


def test_adsb_center_parses_point():
    assert Settings(adsb_center="51.5,-0.1").adsb_center_tuple == (51.5, -0.1)


def test_adsb_center_empty_is_none():
    assert Settings(adsb_center="").adsb_center_tuple is None


def test_adsb_center_rejects_bad_values():
    assert Settings(adsb_center="51.5").adsb_center_tuple is None
    assert Settings(adsb_center="x,y").adsb_center_tuple is None
    assert Settings(adsb_center="200,0").adsb_center_tuple is None

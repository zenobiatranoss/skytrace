from app.providers.aircraft_data import AircraftDataProvider

HEADER = (
    "icao24,registration,manufacturericao,manufacturername,model,typecode,"
    "serialnumber,operator,owner\n"
)


def _write(tmp_path, body: str) -> str:
    path = tmp_path / "aircraft.csv"
    path.write_text(HEADER + body, encoding="utf-8")
    return str(path)


def test_loads_and_normalises_rows(tmp_path):
    path = _write(
        tmp_path,
        "39DE57,F-GABC,BOEING,Boeing,737-800,B738,12345,Air France,Barclays\n"
        "3c6444,D-AIXA,AIRBUS,Airbus,A321,A321,999,Lufthansa,Deutsche Bank\n",
    )
    provider = AircraftDataProvider(path=path)
    provider.load()

    meta = provider.get("39de57")  # lookup is case-insensitive
    assert meta is not None
    assert meta.registration == "F-GABC"
    assert meta.type_code == "B738"
    assert meta.model == "737-800"
    assert meta.operator == "Air France"

    # empty columns stay None instead of bare strings
    assert provider.get("000000") is None


def test_missing_dataset_is_empty(tmp_path):
    provider = AircraftDataProvider(path=str(tmp_path / "nope.csv"))
    assert provider.is_available() is False
    provider.load()
    assert provider.get("39de57") is None


def test_skips_rows_without_valid_icao(tmp_path):
    path = _write(tmp_path, ",,,,,,,,\nabc1234,N12345,,,,,,\n")
    provider = AircraftDataProvider(path=path)
    provider.load()
    assert provider.get("abc1234") is None

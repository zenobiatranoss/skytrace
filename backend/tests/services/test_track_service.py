from app.repositories import flight_repository
from app.services import track_service


def test_records_a_point(db, sample_state):
    flight = flight_repository.upsert_active(db, sample_state)
    db.flush()

    recorded = track_service.maybe_record(db, flight, sample_state)
    db.commit()

    assert recorded is True
    points = track_service.get_track(db, sample_state.icao24).points
    assert len(points) == 1
    assert points[0].latitude == sample_state.latitude


def test_sample_interval_blocks_immediate_dupe(db, sample_state):
    flight = flight_repository.upsert_active(db, sample_state)
    db.flush()

    track_service.maybe_record(db, flight, sample_state)
    # a second call in the same instant shouldn't add another point
    again = track_service.maybe_record(db, flight, sample_state)
    db.commit()

    assert again is False
    assert len(track_service.get_track(db, sample_state.icao24).points) == 1

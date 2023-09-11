from datetime import datetime, timedelta
from pathlib import Path

from ttrack.ttrack import _Database, get_elapsed


def test():
    _DATABASE_TEST_PATH = Path("tests/database_test.json").expanduser()

    if _DATABASE_TEST_PATH.exists():
        _DATABASE_TEST_PATH.unlink()

    database: _Database = _Database()

    start_time = datetime.utcnow()

    # Emulate tracking for a couple of hours.
    end_time = start_time + timedelta(days=1, hours=3.2, seconds=55.333)

    # Compute elapsed time and encode to JSON.
    database.log_hours(start_time, end_time)
    database.save_to_file(_DATABASE_TEST_PATH)

    elapsed_hours, elapsed_minutes = get_elapsed(end_time - start_time)
    print(f"Time tracked in session: {elapsed_hours} hours {elapsed_minutes} minutes.")

    # Decode from JSON.
    database_decoded = _Database.load_from_file(_DATABASE_TEST_PATH)

    assert database._database == database_decoded._database

    _DATABASE_TEST_PATH.unlink()


if __name__ == "__main__":
    test()

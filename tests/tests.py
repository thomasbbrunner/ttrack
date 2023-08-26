from datetime import datetime, timedelta
from pathlib import Path

from ttrack.ttrack import (
    DatabaseType,
    get_elapsed,
    load_database,
    log_hours,
    save_database,
)


def test():
    _DATABASE_TEST_PATH = Path("tests/database_test.json").expanduser()

    if _DATABASE_TEST_PATH.exists():
        _DATABASE_TEST_PATH.unlink()

    database: DatabaseType
    database = {}

    start_time = datetime.utcnow()

    # Emulate tracking for a couple of hours.
    end_time = start_time + timedelta(days=1, hours=3.2, seconds=55.333)

    log_hours(database, start_time, end_time)

    elapsed_hours, elapsed_minutes = get_elapsed(start_time, end_time)
    print(f"Time tracked in session: {elapsed_hours} hours {elapsed_minutes} minutes.")

    # Encode to JSON.
    save_database(database, _DATABASE_TEST_PATH)

    # Decode from JSON.
    database_decoded = load_database(_DATABASE_TEST_PATH)
    print(database)

    assert database == database_decoded

    _DATABASE_TEST_PATH.unlink()


if __name__ == "__main__":
    test()

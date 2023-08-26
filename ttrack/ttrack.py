"""Ttrack: A lightweight time tracker.

Vision:
>>> ./ttrack.py
Tracking work hours...

(dynamic image)

2/8 hours today
20/40 hours this week
80/160 hours this month
Credit: +2 hours

(KeyboardInterrupt)
Time tracked in session: 4 hours 32 minutes.
"""
import atexit
import json
import signal
import sys
import threading
from datetime import date, datetime, timedelta
from enum import StrEnum, auto
from pathlib import Path


class Cathegory(StrEnum):
    WORK = auto()


DatabaseType = dict[date, dict[Cathegory, timedelta]]
DatabaseReprType = dict[str, dict[str, str]]


def database_to_repr(database: DatabaseType) -> DatabaseReprType:
    # Database with string representations of unserializable types.
    database_repr = {}

    for key, value in database.items():
        if isinstance(key, date):
            key_repr = repr(key)
        elif isinstance(key, Cathegory):
            key_repr = Cathegory.__name__ + "." + key.name
        else:
            raise RuntimeError(f"Unexpected database key '{key}'.")

        if isinstance(value, dict):
            value_repr = database_to_repr(value)
        elif isinstance(value, timedelta):
            value_repr = repr(value)
        else:
            raise RuntimeError(f"Unexpected database value '{value}'.")

        database_repr[key_repr] = value_repr

    return database_repr


def repr_to_database(database_repr: DatabaseReprType):
    # Required import for the evals to work.
    import datetime

    database = {}

    for key_repr, value_repr in database_repr.items():
        if key_repr.startswith("datetime.date("):
            key = eval(key_repr)
        elif key_repr.startswith("Cathegory."):
            key = eval(key_repr)
        else:
            raise RuntimeError(f"Unexpected database key '{key_repr}'.")

        if isinstance(value_repr, dict):
            value = repr_to_database(value_repr)
        elif value_repr.startswith("datetime.timedelta("):
            value = eval(value_repr)
        else:
            raise RuntimeError(f"Unexpected database value '{value_repr}'.")

        database[key] = value

    return database


def get_elapsed(start_time: datetime, end_time: datetime):
    elapsed_time = end_time - start_time

    # Get number of completed hours.
    elapsed_hours, remaining_delta = divmod(elapsed_time, timedelta(hours=1))
    # Get rounded number of minutes.
    elapsed_minutes = remaining_delta / timedelta(minutes=1)
    elapsed_minutes = round(elapsed_minutes)

    return elapsed_hours, elapsed_minutes


def save_database(database: DatabaseType, path: Path):
    database_repr = database_to_repr(database)
    database_json = json.dumps(database_repr, indent=2)
    path.write_text(database_json)


def load_database(path: Path):
    database_json = path.read_text()
    database_repr = json.loads(database_json)
    database = repr_to_database(database_repr)
    return database


def log_to_database(
    database: DatabaseType, date: date, cathegory: Cathegory, delta: timedelta
):
    if date not in database:
        database[date] = {}

    if cathegory not in database[date.today()]:
        database[date][cathegory] = timedelta()

    database[date][cathegory] += delta


def log_hours(
    database: DatabaseType, start_time: datetime, end_time: datetime, path: Path
):
    start_date = start_time.date()
    end_date = end_time.date()

    if end_date >= start_date:
        elapsed_time = end_time - start_time
        log_to_database(database, start_date, Cathegory.WORK, elapsed_time)
        save_database(database, path)

    # TODO Assign tracked hours to the correct date.
    # Requires considering timezones, as start and end times might be on the
    # same day in the local timezone, but different days in UTC.
    # elif end_date > start_date:

    else:
        raise RuntimeError("Unexpected condition: end date is before start date.")


def main():
    _DATABASE_PATH = Path("~/.local/share/ttrack/database.json").expanduser()

    database: DatabaseType
    if _DATABASE_PATH.is_file() and _DATABASE_PATH.stat().st_size != 0:
        database = load_database(_DATABASE_PATH)
    else:
        _DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _DATABASE_PATH.touch()
        database = {}

    print("Tracking work hours...")

    start_time = datetime.utcnow()

    def log_hours_():
        cur_time = datetime.utcnow()
        log_hours(database, start_time, cur_time, _DATABASE_PATH)

    # Call function to log hours in every occasion that the program exists.
    atexit.register(log_hours_)

    try:
        forever = threading.Event()
        forever.wait()

    except KeyboardInterrupt:
        # Ignore KeyboardInterrupt while handling exit.
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        print("Stopping tracking.")

        end_time = datetime.utcnow()
        elapsed_hours, elapsed_minutes = get_elapsed(start_time, end_time)

        print(
            f"Time tracked in session: {elapsed_hours} hours {elapsed_minutes} minutes."
        )

        # Set KeyboardInterrupt to default handler.
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        # Exit normally, as KeyboardInterrupt is the intended method to exit
        # the tracker.
        sys.exit(0)


if __name__ == "__main__":
    main()

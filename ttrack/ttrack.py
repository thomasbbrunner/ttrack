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
import curses
import json
import signal
import time
from datetime import date, datetime, timedelta
from enum import Enum, auto
from pathlib import Path


class Cathegory(str, Enum):
    WORK = auto()


def get_elapsed(start_time: datetime, end_time: datetime):
    elapsed_time = end_time - start_time

    # Get number of completed hours.
    elapsed_hours, remaining_delta = divmod(elapsed_time, timedelta(hours=1))
    # Get rounded number of minutes.
    elapsed_minutes = remaining_delta / timedelta(minutes=1)
    elapsed_minutes = round(elapsed_minutes)

    return elapsed_hours, elapsed_minutes


class _Database:
    _DbType = dict[date, dict[Cathegory, timedelta]]
    _EncodedDbType = dict[str, dict[str, str]]

    def __init__(self):
        self._database: self._DbType = {}

    def log_hours(self, start_time: datetime, end_time: datetime):
        start_date = start_time.date()
        end_date = end_time.date()

        if end_date >= start_date:
            elapsed_time = end_time - start_time
            self._log_entry(start_date, Cathegory.WORK, elapsed_time)

        # TODO Assign tracked hours to the correct date.
        # Requires considering timezones, as start and end times might be on the
        # same day in the local timezone, but different days in UTC.
        # elif end_date > start_date:

        else:
            raise RuntimeError("Unexpected condition: end date is before start date.")

    def _log_entry(self, date: date, cathegory: Cathegory, delta: timedelta):
        if date not in self._database:
            self._database[date] = {}

        if cathegory not in self._database[date]:
            self._database[date][cathegory] = timedelta()

        self._database[date][cathegory] += delta

    def save_to_file(self, path: Path):
        database_encoded = self._encode()
        database_json = json.dumps(database_encoded, indent=2)
        path.write_text(database_json)

    @classmethod
    def load_from_file(cls, path: Path):
        database_json = path.read_text()
        database_encoded = json.loads(database_json)
        database = cls()
        database._database = cls._decode(database_encoded)

        return database

    def _encode(self) -> _EncodedDbType:
        database_encoded = {}
        for date, cathegories in self._database.items():
            date_repr = repr(date)
            database_encoded[date_repr] = {}

            for cathegory, timedelta in cathegories.items():
                cathegory_repr = Cathegory.__name__ + "." + cathegory.name
                timedelta_repr = repr(timedelta)

                database_encoded[date_repr][cathegory_repr] = timedelta_repr

        return database_encoded

    @classmethod
    def _decode(cls, database_encoded: _EncodedDbType):
        # Required import for the evals to work.
        import datetime

        database = {}
        for date_repr, cathegories in database_encoded.items():
            assert date_repr.startswith("datetime.date(")
            date = eval(date_repr)
            database[date] = {}

            for cathegory_repr, timedelta_repr in cathegories.items():
                assert cathegory_repr.startswith("Cathegory.")
                cathegory = eval(cathegory_repr)

                assert timedelta_repr.startswith("datetime.timedelta(")
                timedelta = eval(timedelta_repr)

                database[date][cathegory] = timedelta

        return database


def ttrack(stdscr: curses.window):
    _DATABASE_PATH = Path("~/.local/share/ttrack/database.json").expanduser()

    database: _Database
    if _DATABASE_PATH.is_file() and _DATABASE_PATH.stat().st_size != 0:
        database = _Database.load_from_file(_DATABASE_PATH)
    else:
        _DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _DATABASE_PATH.touch()
        database = _Database()

    start_time = datetime.utcnow()

    try:
        while True:
            stdscr.addstr(0, 0, "Tracking work hours...")
            cur_time = datetime.utcnow()
            elapsed_hours, elapsed_minutes = get_elapsed(start_time, cur_time)
            stdscr.addstr(1, 0, f"Time tracked in this session: {elapsed_hours} hours {elapsed_minutes} minutes.")
            stdscr.refresh()
            time.sleep(60)

    except KeyboardInterrupt:
        # Ignore KeyboardInterrupt while handling exit.
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        end_time = datetime.utcnow()
        elapsed_hours, elapsed_minutes = get_elapsed(start_time, end_time)

        # Return normally, as KeyboardInterrupt is the intended method to exit
        # the tracker.
        return elapsed_hours, elapsed_minutes

    finally:
        # Log hours and save database when program exists.
        end_time = datetime.utcnow()
        database.log_hours(start_time, end_time)
        database.save_to_file(_DATABASE_PATH)

        # Set KeyboardInterrupt to default handler.
        signal.signal(signal.SIGINT, signal.SIG_DFL)


if __name__ == "__main__":
    curses.wrapper(ttrack)

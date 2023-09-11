import curses
import sys

from ttrack.ttrack import ttrack


def main():
    print("Tracking work hours...")

    # Wrap application to make sure terminal is restored in case of unhandled
    # exceptions (taken from curses.wrapper).
    try:
        # Initialize curses
        stdscr = curses.initscr()
        curses.start_color()

        # Turn off echoing of keys, and enter cbreak mode,
        # where no buffering is performed on keyboard input
        # noecho()
        # cbreak()

        # In keypad mode, escape sequences for special keys
        # (like the cursor keys) will be interpreted and
        # a special value like curses.KEY_LEFT will be returned
        # stdscr.keypad(1)

        elapsed_hours, elapsed_minutes = ttrack(stdscr=stdscr)

    finally:
        # Set everything back to normal
        if "stdscr" in locals():
            stdscr.keypad(0)
            curses.echo()
            curses.nocbreak()
            curses.endwin()

    print("Stopping tracking.")

    print(f"Time tracked in this session: {elapsed_hours} hours {elapsed_minutes} minutes.")
    sys.exit(0)

"""Single-keypress and arrow-key terminal input handler for Linux."""

from __future__ import annotations

import os
import sys
from typing import Optional


class KeyReader:
    """Reads single keypresses and arrow keys from the terminal without requiring Enter."""

    KEY_UP = "UP"
    KEY_DOWN = "DOWN"
    KEY_LEFT = "LEFT"
    KEY_RIGHT = "RIGHT"
    KEY_ENTER = "ENTER"
    KEY_BACKSPACE = "BACKSPACE"
    KEY_ESC = "ESC"
    KEY_TAB = "TAB"

    @classmethod
    def read_key(cls) -> str:
        """
        Reads a single keypress.
        Returns 'UP', 'DOWN', 'LEFT', 'RIGHT', 'ENTER', 'ESC', 'BACKSPACE',
        or the pressed character (e.g. 's', 't', '1', '?').
        """
        if not sys.stdin.isatty():
            # Non-interactive / pipe fallback
            line = sys.stdin.readline()
            return line.strip() if line else "ENTER"

        import termios
        import tty

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch1 = sys.stdin.read(1)

            # Ctrl+C
            if ch1 == "\x03":
                raise KeyboardInterrupt

            # Enter
            if ch1 in ("\r", "\n"):
                return cls.KEY_ENTER

            # Tab
            if ch1 == "\t":
                return cls.KEY_TAB

            # Backspace
            if ch1 in ("\x7f", "\x08"):
                return cls.KEY_BACKSPACE

            # Escape Sequences (Arrows, PageUp, etc.)
            if ch1 == "\x1b":
                # Check if there are more characters
                import select
                r, _, _ = select.select([sys.stdin], [], [], 0.05)
                if r:
                    ch2 = sys.stdin.read(1)
                    if ch2 == "[":
                        ch3 = sys.stdin.read(1)
                        if ch3 == "A":
                            return cls.KEY_UP
                        elif ch3 == "B":
                            return cls.KEY_DOWN
                        elif ch3 == "C":
                            return cls.KEY_RIGHT
                        elif ch3 == "D":
                            return cls.KEY_LEFT
                return cls.KEY_ESC

            return ch1

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

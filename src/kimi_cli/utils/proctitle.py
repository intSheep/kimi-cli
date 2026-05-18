from __future__ import annotations

import contextlib
import os
import sys


def set_process_title(title: str) -> None:
    """Set the OS-level process title visible in ps/top/terminal panels."""
    try:
        import setproctitle

        setproctitle.setproctitle(title)
    except ImportError:
        pass


_last_title: str = ""
_tty_fd: int | None = None


def _get_tty_fd() -> int | None:
    """Return a file descriptor for the controlling terminal.

    Prefers /dev/tty so OSC writes bypass Python's stdout/stderr buffering
    and don't interfere with prompt-toolkit's screen management.
    Falls back to stderr fileno on Windows or when /dev/tty is unavailable.
    """
    global _tty_fd
    if _tty_fd is not None:
        return _tty_fd
    try:
        _tty_fd = os.open("/dev/tty", os.O_WRONLY | os.O_NOCTTY)
        return _tty_fd
    except OSError:
        try:
            _tty_fd = sys.stderr.fileno()
            return _tty_fd
        except (OSError, ValueError):
            return None


def set_terminal_title(title: str) -> None:
    """Set the terminal tab/window title via ANSI OSC escape sequence.

    Writes directly to the controlling terminal (/dev/tty when available)
    to avoid interfering with prompt-toolkit's TUI rendering on stdout/stderr.
    Skips duplicate writes to prevent terminal flicker.
    """
    global _last_title
    if title == _last_title:
        return
    _last_title = title
    fd = _get_tty_fd()
    if fd is None:
        return
    with contextlib.suppress(OSError):
        os.write(fd, f"\033]0;{title}\007".encode())


def init_process_name(name: str = "Kimi Code") -> None:
    """Initialize process name: OS process title + terminal tab title."""
    set_process_title(name)
    set_terminal_title(name)

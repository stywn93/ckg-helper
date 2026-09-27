import os
import signal
import shutil
import sys
import threading
import time
from contextlib import contextmanager


STOP_FOOTER_COLOR = "\033[38;2;120;120;120m"
RESET = "\033[0m"


def _listen_for_stop(stop_event: threading.Event, request_stop) -> None:
    stop_requested = False
    if os.name == "nt":
        import msvcrt

        while not stop_event.is_set():
            if msvcrt.kbhit():
                if msvcrt.getwch().lower() == "s":
                    stop_requested = True
                    break
            time.sleep(0.1)
    else:
        import select
        import termios
        import tty

        fd = sys.stdin.fileno()
        settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            while not stop_event.is_set():
                ready, _, _ = select.select([sys.stdin], [], [], 0.1)
                if ready and sys.stdin.read(1).lower() == "s":
                    stop_requested = True
                    break
        except (OSError, ValueError):
            return
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, settings)

    if stop_requested:
        request_stop()


@contextmanager
def sticky_stop_footer():
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        yield
        return

    terminal_height = shutil.get_terminal_size((80, 24)).lines
    if terminal_height < 3:
        yield
        return

    scroll_bottom = terminal_height - 1
    stop_event = threading.Event()
    cleaned = threading.Event()

    def clear_footer() -> None:
        if cleaned.is_set():
            return
        cleaned.set()
        print(f"\033[r\033[{terminal_height};1H\033[2K", end="", flush=True)

    def request_stop() -> None:
        stop_event.set()
        clear_footer()
        os.kill(os.getpid(), signal.SIGINT)

    print(
        f"\033[1;{scroll_bottom}r\033[{terminal_height};1H\033[2K"
        f"{STOP_FOOTER_COLOR}S Stop{RESET}\033[{scroll_bottom};1H",
        end="",
        flush=True,
    )
    listener = threading.Thread(
        target=_listen_for_stop,
        args=(stop_event, request_stop),
        daemon=True,
    )
    listener.start()
    try:
        yield
    finally:
        stop_event.set()
        listener.join(timeout=0.5)
        clear_footer()

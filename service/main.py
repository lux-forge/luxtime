"""Console entry point for watchdog development and diagnostics."""

from __future__ import annotations

import signal
import threading

from service.watchdog import LuxTimeWatchdog


def main() -> None:
    stop_event = threading.Event()

    def stop(*_: object) -> None:
        stop_event.set()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    LuxTimeWatchdog().run(stop_event)


if __name__ == "__main__":
    main()

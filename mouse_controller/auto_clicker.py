"""Threaded mouse click worker."""

import threading
from typing import Optional

from pynput.mouse import Button, Controller


class AutoClicker:
    """Click at a configurable rate without blocking the Tk event loop."""

    def __init__(self):
        self._mouse = Controller()
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop_event: Optional[threading.Event] = None
        self._clicks_per_second = 8.0

    @property
    def running(self) -> bool:
        with self._lock:
            return self._thread is not None and self._thread.is_alive() and not self._stop_event.is_set()

    def set_speed(self, clicks_per_second: float) -> None:
        with self._lock:
            self._clicks_per_second = max(1.0, float(clicks_per_second))

    def start(self) -> bool:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return False
            stop_event = threading.Event()
            self._stop_event = stop_event
            self._thread = threading.Thread(
                target=self._run,
                args=(stop_event,),
                name="neon-auto-clicker",
                daemon=True,
            )
            self._thread.start()
            return True

    def stop(self) -> None:
        with self._lock:
            if self._stop_event is not None:
                self._stop_event.set()

    def _run(self, stop_event: threading.Event) -> None:
        while not stop_event.is_set():
            try:
                self._mouse.click(Button.left)
            except Exception:
                stop_event.set()
                break
            with self._lock:
                interval = 1.0 / self._clicks_per_second
            if stop_event.wait(interval):
                break
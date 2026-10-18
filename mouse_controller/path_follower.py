"""Threaded, interruptible path-following worker."""

import math
import threading
from typing import Callable, List, Optional, Sequence, Tuple

from pynput.mouse import Controller

Point = Tuple[int, int]


class PathFollower:
    """Move smoothly through a path at a configurable pixel rate."""

    def __init__(self, on_position: Callable[[Point], None]):
        self._mouse = Controller()
        self._on_position = on_position
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop_event: Optional[threading.Event] = None
        self._speed = 700.0
        self._step_seconds = 0.01

    @property
    def running(self) -> bool:
        with self._lock:
            return self._thread is not None and self._thread.is_alive() and not self._stop_event.is_set()

    def set_speed(self, pixels_per_second: float) -> None:
        with self._lock:
            self._speed = max(50.0, float(pixels_per_second))

    def start(self, points: Sequence[Point]) -> bool:
        path = [(int(x), int(y)) for x, y in points]
        if not path:
            return False
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return False
            stop_event = threading.Event()
            self._stop_event = stop_event
            self._thread = threading.Thread(
                target=self._run,
                args=(stop_event, path),
                name="neon-path-follower",
                daemon=True,
            )
            self._thread.start()
            return True

    def stop(self) -> None:
        with self._lock:
            if self._stop_event is not None:
                self._stop_event.set()

    def _run(self, stop_event: threading.Event, path: List[Point]) -> None:
        try:
            while not stop_event.is_set():
                for target_x, target_y in path:
                    if stop_event.is_set():
                        return
                    position = self._mouse.position
                    start_x, start_y = int(position[0]), int(position[1])
                    distance = math.hypot(target_x - start_x, target_y - start_y)
                    with self._lock:
                        speed = self._speed
                    steps = max(1, math.ceil(distance / max(1.0, speed * self._step_seconds)))
                    for step in range(1, steps + 1):
                        if stop_event.is_set():
                            return
                        fraction = step / steps
                        point = (
                            round(start_x + (target_x - start_x) * fraction),
                            round(start_y + (target_y - start_y) * fraction),
                        )
                        self._mouse.position = point
                        self._on_position(point)
                        if stop_event.wait(self._step_seconds):
                            return
        except Exception:
            stop_event.set()
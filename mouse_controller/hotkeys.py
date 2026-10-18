"""Global hotkey registration and lifecycle management."""

from typing import Callable, Dict, Optional

from pynput.keyboard import GlobalHotKeys


class HotkeyManager:
    """Register the app's start, stop, and toggle shortcuts."""

    def __init__(self, on_auto_toggle: Callable[[], None], on_path_toggle: Callable[[], None], on_stop: Callable[[], None]):
        self._callbacks: Dict[str, Callable[[], None]] = {
            "<ctrl>+<alt>+a": on_auto_toggle,
            "<ctrl>+<alt>+p": on_path_toggle,
            "<ctrl>+<alt>+s": on_stop,
        }
        self._listener: Optional[GlobalHotKeys] = None

    def start(self) -> None:
        if self._listener is not None:
            return
        self._listener = GlobalHotKeys(self._callbacks)
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener.join(timeout=1.0)
            self._listener = None
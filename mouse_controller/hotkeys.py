"""Global hotkey registration and lifecycle management."""

import platform
from typing import Callable, Dict, Optional, Set

from pynput import keyboard
from pynput.keyboard import GlobalHotKeys, Listener


class HotkeyManager:
    """Register the app's start, stop, and toggle shortcuts."""

    def __init__(
        self,
        on_auto_toggle: Callable[[], None],
        on_path_toggle: Callable[[], None],
        on_stop: Callable[[], None],
        on_circle: Callable[[], None],
        on_triangle: Callable[[], None],
        on_square: Callable[[], None],
        on_random: Callable[[], None],
    ):
        self._callbacks: Dict[str, Callable[[], None]] = {
            "<ctrl>+<alt>+a": on_auto_toggle,
            "<ctrl>+<alt>+p": on_path_toggle,
            "<ctrl>+<alt>+s": on_stop,
        }
        shape_callbacks = {
            1: on_circle,
            2: on_triangle,
            3: on_square,
            4: on_random,
        }
        self._numpad_callbacks = {
            key_code: shape_callbacks[number]
            for key_code, number in self._numpad_key_codes().items()
            if number in shape_callbacks
        }
        self._pressed_modifiers: Set[str] = set()
        self._held_numpad_keys: Set[int] = set()
        self._listener: Optional[GlobalHotKeys] = None
        self._numpad_listener: Optional[Listener] = None

    def start(self) -> None:
        if self._listener is not None:
            return
        self._listener = GlobalHotKeys(self._callbacks)
        self._listener.start()
        if self._numpad_callbacks:
            self._numpad_listener = Listener(
                on_press=self._on_numpad_press,
                on_release=self._on_numpad_release,
            )
            self._numpad_listener.start()

    def stop(self) -> None:
        if self._numpad_listener is not None:
            self._numpad_listener.stop()
            self._numpad_listener.join(timeout=1.0)
            self._numpad_listener = None
        if self._listener is not None:
            self._listener.stop()
            self._listener.join(timeout=1.0)
            self._listener = None

    @staticmethod
    def _numpad_key_codes() -> Dict[int, int]:
        system = platform.system()
        if system == "Windows":
            return {0x61: 1, 0x62: 2, 0x63: 3, 0x64: 4}
        if system == "Darwin":
            return {83: 1, 84: 2, 85: 3, 86: 4}
        return {0xFFB1: 1, 0xFFB2: 2, 0xFFB3: 3, 0xFFB4: 4}

    @staticmethod
    def _modifier_name(key) -> Optional[str]:
        if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            return "ctrl"
        if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
            return "alt"
        return None

    def _on_numpad_press(self, key) -> None:
        modifier = self._modifier_name(key)
        if modifier is not None:
            self._pressed_modifiers.add(modifier)
            return
        key_code = getattr(key, "vk", None)
        if key_code is None or key_code in self._held_numpad_keys:
            return
        self._held_numpad_keys.add(key_code)
        callback = self._numpad_callbacks.get(key_code)
        if callback is not None and {"ctrl", "alt"}.issubset(self._pressed_modifiers):
            callback()

    def _on_numpad_release(self, key) -> None:
        modifier = self._modifier_name(key)
        if modifier is not None:
            self._pressed_modifiers.discard(modifier)
            return
        key_code = getattr(key, "vk", None)
        if key_code is not None:
            self._held_numpad_keys.discard(key_code)
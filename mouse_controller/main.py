"""Entry point and application controller for Neon Mouse Controller."""

import tkinter as tk
from tkinter import messagebox
from typing import Callable, List, Optional, Tuple

from pynput.mouse import Controller

from auto_clicker import AutoClicker
from hotkeys import HotkeyManager
from neon_theme import BACKGROUND, CYAN, ERROR, MUTED, PANEL, TEXT, WARNING
from neon_widgets import NeonBorderFrame, NeonGlowButton, NeonSlider, NeonToggle
from path_canvas import PathCanvas
from path_follower import PathFollower
from shapes import ShapePaths

Point = Tuple[int, int]
ShapeFactory = Callable[..., List[Point]]


class NeonMouseControllerApp:
    """Own the UI, worker lifecycle, hotkeys, and mouse safety monitor."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Neon Mouse Controller")
        self.root.geometry("860x840")
        self.root.minsize(700, 740)
        self.root.configure(background=BACKGROUND)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self._mouse = Controller()
        cursor = self._mouse.position
        self._last_observed: Point = (int(cursor[0]), int(cursor[1]))
        self._expected_position: Point = self._last_observed
        self._selected_path: Optional[List[Point]] = None
        self._selected_path_relative = False
        self._closing = False

        self.auto_clicker = AutoClicker()
        self.path_follower = PathFollower(self._record_expected_position)

        self._build_ui()
        self._set_status("Ready. Activate from a toggle or hotkey.", MUTED)
        self.hotkeys = HotkeyManager(
            on_auto_toggle=lambda: self.root.after(0, self._toggle_auto_from_hotkey),
            on_path_toggle=lambda: self.root.after(0, self._toggle_path_from_hotkey),
            on_stop=lambda: self.root.after(0, lambda: self._stop_all("Stopped by hotkey.")),
            on_circle=lambda: self.root.after(0, lambda: self._use_shape(ShapePaths.circle, "Circle")),
            on_triangle=lambda: self.root.after(0, lambda: self._use_shape(ShapePaths.triangle, "Triangle")),
            on_square=lambda: self.root.after(0, lambda: self._use_shape(ShapePaths.square, "Square")),
            on_random=lambda: self.root.after(0, self._use_random_path),
        )
        try:
            self.hotkeys.start()
        except Exception as error:
            self._set_status(f"Global hotkeys unavailable: {error}", WARNING)
        self.root.after(100, self._monitor_mouse)

    def _build_ui(self) -> None:
        container = tk.Frame(self.root, background=BACKGROUND, padx=18, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        header = tk.Frame(container, background=BACKGROUND)
        header.pack(fill=tk.X, pady=(0, 14))
        tk.Label(
            header,
            text="NEON MOUSE CONTROLLER",
            background=BACKGROUND,
            foreground=CYAN,
            font=("TkDefaultFont", 17, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text=(
                "Ctrl+Alt+A clicker  |  Ctrl+Alt+P path  |  Ctrl+Alt+S stop\n"
                "Ctrl+Alt+Num1 circle  |  Ctrl+Alt+Num2 triangle  |  "
                "Ctrl+Alt+Num3 square  |  Ctrl+Alt+Num4 random"
            ),
            background=BACKGROUND,
            foreground=MUTED,
            font=("TkDefaultFont", 9),
            wraplength=810,
            justify=tk.LEFT,
        ).pack(anchor="w", pady=(4, 0))

        controls = tk.Frame(container, background=BACKGROUND)
        controls.pack(fill=tk.X)
        controls.columnconfigure(0, weight=1, uniform="controls")
        controls.columnconfigure(1, weight=1, uniform="controls")

        click_section = NeonBorderFrame(controls, "Auto Clicker")
        click_section.grid(row=0, column=0, sticky="nsew", padx=(0, 7), pady=(0, 12))
        click_row = tk.Frame(click_section.content, background=PANEL)
        click_row.pack(fill=tk.X, pady=(0, 10))
        tk.Label(click_row, text="Clicking", background=PANEL, foreground=TEXT).pack(side=tk.LEFT)
        self.click_toggle = NeonToggle(click_row, command=self._on_click_toggle)
        self.click_toggle.pack(side=tk.RIGHT)
        self.click_speed = NeonSlider(
            click_section.content,
            "Clicks per second",
            1,
            30,
            8,
            command=self.auto_clicker.set_speed,
        )
        self.click_speed.pack(fill=tk.X)

        path_section = NeonBorderFrame(controls, "Path Follower")
        path_section.grid(row=0, column=1, sticky="nsew", padx=(7, 0), pady=(0, 12))
        path_row = tk.Frame(path_section.content, background=PANEL)
        path_row.pack(fill=tk.X, pady=(0, 10))
        tk.Label(path_row, text="Following", background=PANEL, foreground=TEXT).pack(side=tk.LEFT)
        self.path_toggle = NeonToggle(path_row, command=self._on_path_toggle)
        self.path_toggle.pack(side=tk.RIGHT)
        self.path_speed = NeonSlider(
            path_section.content,
            "Movement speed (px/s)",
            100,
            1800,
            700,
            command=self.path_follower.set_speed,
            resolution=50,
        )
        self.path_speed.pack(fill=tk.X, pady=(0, 10))
        max_shape_size = max(
            160,
            min(1000, min(self.root.winfo_screenwidth(), self.root.winfo_screenheight()) - 32),
        )
        self.shape_size = NeonSlider(
            path_section.content,
            "Shape size (px)",
            80,
            max_shape_size,
            min(240, max_shape_size),
            resolution=20,
        )
        self.shape_size.pack(fill=tk.X, pady=(0, 10))
        shape_row = tk.Frame(path_section.content, background=PANEL)
        shape_row.pack(fill=tk.X)
        for name, shape in (
            ("Circle", ShapePaths.circle),
            ("Triangle", ShapePaths.triangle),
            ("Square", ShapePaths.square),
            ("Random", None),
        ):
            NeonGlowButton(
                shape_row,
                name,
                command=(
                    self._use_random_path
                    if shape is None
                    else lambda shape=shape, name=name: self._use_shape(shape, name)
                ),
            ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=3)

        draw_section = NeonBorderFrame(container, "Custom Path Canvas")
        draw_section.pack(fill=tk.BOTH, expand=True)
        tk.Label(
            draw_section.content,
            text="Draw a stroke; its canvas position will scale across the full display.",
            background=PANEL,
            foreground=MUTED,
            anchor="w",
        ).pack(fill=tk.X, pady=(0, 8))
        self.path_canvas = PathCanvas(draw_section.content)
        self.path_canvas.pack(fill=tk.BOTH, expand=True)
        canvas_buttons = tk.Frame(draw_section.content, background=PANEL)
        canvas_buttons.pack(fill=tk.X, pady=(10, 0))
        NeonGlowButton(
            canvas_buttons,
            "Use Drawn Path",
            command=self._use_drawn_path,
        ).pack(side=tk.LEFT)
        NeonGlowButton(
            canvas_buttons,
            "Clear",
            command=self.path_canvas.clear,
        ).pack(side=tk.LEFT, padx=(8, 0))

        footer = tk.Frame(container, background=BACKGROUND)
        footer.pack(fill=tk.X, pady=(12, 0))
        self.status_label = tk.Label(
            footer,
            text="",
            background=BACKGROUND,
            foreground=MUTED,
            anchor="w",
            font=("TkDefaultFont", 9),
            wraplength=710,
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        NeonGlowButton(footer, "Stop All", command=lambda: self._stop_all("Stopped by user.")).pack(side=tk.RIGHT)

    def _record_expected_position(self, point: Point) -> None:
        self._expected_position = (int(point[0]), int(point[1]))

    def _monitor_mouse(self) -> None:
        if self._closing:
            return
        try:
            position = self._mouse.position
            current = (int(position[0]), int(position[1]))
            moved = current != self._last_observed
            expected_distance = ((current[0] - self._expected_position[0]) ** 2 +
                                 (current[1] - self._expected_position[1]) ** 2) ** 0.5
            user_moved = moved and (
                self.auto_clicker.running or
                (self.path_follower.running and expected_distance > 35)
            )
            if user_moved:
                    self._stop_all("Mouse moved. Motion stopped; reactivate from the UI or a hotkey.", WARNING)
            self._last_observed = current
        except Exception as error:
            self._set_status(f"Mouse monitor error: {error}", ERROR)
        self.root.after(100, self._monitor_mouse)

    def _on_click_toggle(self, enabled: bool) -> None:
        if enabled:
            self._stop_path_worker()
            self.path_toggle.set(False)
            if self.auto_clicker.start():
                cursor = self._mouse.position
                self._last_observed = (int(cursor[0]), int(cursor[1]))
                self._expected_position = self._last_observed
                self._set_status("Auto-clicker active. Move the mouse to disengage.", CYAN)
            else:
                self.click_toggle.set(False)
                self._set_status("Clicker is stopping; try again in a moment.", WARNING)
        else:
            self.auto_clicker.stop()
            self._set_status("Auto-clicker stopped.", MUTED)

    def _on_path_toggle(self, enabled: bool) -> None:
        if enabled:
            if not self._selected_path:
                self.path_toggle.set(False)
                self._set_status("Choose a built-in shape or draw a path first.", WARNING)
                return
            self.auto_clicker.stop()
            self.click_toggle.set(False)
            path = self._path_for_activation()
            if self.path_follower.start(path):
                cursor = self._mouse.position
                self._last_observed = (int(cursor[0]), int(cursor[1]))
                self._expected_position = self._last_observed
                self._set_status("Path follower active. Move the mouse to disengage.", CYAN)
            else:
                self.path_toggle.set(False)
                self._set_status("Path follower is stopping; try again in a moment.", WARNING)
        else:
            self.path_follower.stop()
            self._set_status("Path follower stopped.", MUTED)

    def _path_for_activation(self) -> List[Point]:
        if not self._selected_path:
            return []
        if not self._selected_path_relative:
            return list(self._selected_path)
        position = self._mouse.position
        center_x, center_y = int(position[0]), int(position[1])
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        min_x = min(point[0] for point in self._selected_path)
        max_x = max(point[0] for point in self._selected_path)
        min_y = min(point[1] for point in self._selected_path)
        max_y = max(point[1] for point in self._selected_path)
        center_x = min(max(center_x, -min_x), screen_width - 1 - max_x)
        center_y = min(max(center_y, -min_y), screen_height - 1 - max_y)
        return [(center_x + x, center_y + y) for x, y in self._selected_path]

    def _use_shape(self, shape: ShapeFactory, name: str) -> None:
        shape_size = int(self.shape_size.get())
        shape_dimension = shape_size // 2 if name == "Circle" else shape_size
        self._selected_path = shape(shape_dimension)
        self._selected_path_relative = True
        self._set_status(f"{name} path selected ({shape_size}px). Starting its path.", CYAN)
        self._start_selected_path()

    def _use_random_path(self) -> None:
        self._selected_path = ShapePaths.random_path(
            self.root.winfo_screenwidth(),
            self.root.winfo_screenheight(),
        )
        self._selected_path_relative = False
        self._set_status("Random full-screen path selected. Starting its path.", CYAN)
        self._start_selected_path()

    def _start_selected_path(self) -> None:
        if self.path_follower.running or self.path_toggle.get():
            self.path_follower.stop()
            self.path_toggle.set(False)
            self.root.after(100, lambda: self.path_toggle.set(True, notify=True))
        else:
            self.path_toggle.set(True, notify=True)

    def _use_drawn_path(self) -> None:
        path = self.path_canvas.get_screen_path(
            self.root.winfo_screenwidth(),
            self.root.winfo_screenheight(),
        )
        if len(path) < 2:
            self._set_status("Draw a path with at least two points first.", WARNING)
            return
        self._selected_path = list(path)
        self._selected_path_relative = False
        self._set_status("Custom full-screen path selected. Starting its path.", CYAN)
        self._start_selected_path()

    def _toggle_auto_from_hotkey(self) -> None:
        self.click_toggle.set(not self.click_toggle.get(), notify=True)

    def _toggle_path_from_hotkey(self) -> None:
        self.path_toggle.set(not self.path_toggle.get(), notify=True)

    def _stop_path_worker(self) -> None:
        self.path_follower.stop()
        self.path_toggle.set(False)

    def _stop_all(self, message: str, color=MUTED) -> None:
        self.auto_clicker.stop()
        self.path_follower.stop()
        self.click_toggle.set(False)
        self.path_toggle.set(False)
        self._set_status(message, color)

    def _set_status(self, message: str, color: str) -> None:
        if self.status_label.winfo_exists():
            self.status_label.configure(text=message, foreground=color)

    def close(self) -> None:
        if self._closing:
            return
        self._closing = True
        self.auto_clicker.stop()
        self.path_follower.stop()
        self.hotkeys.stop()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    try:
        NeonMouseControllerApp(root)
    except Exception as error:
        messagebox.showerror("Neon Mouse Controller", str(error))
        root.destroy()
        raise
    root.mainloop()


if __name__ == "__main__":
    main()
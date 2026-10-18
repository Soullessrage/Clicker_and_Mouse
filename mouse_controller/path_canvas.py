"""Canvas for drawing and exporting custom desktop paths."""

import tkinter as tk
from typing import List, Tuple

from neon_theme import BACKGROUND, CYAN, PURPLE

Point = Tuple[int, int]


class PathCanvas(tk.Frame):
    """Capture drag strokes in canvas coordinates and convert them to screen points."""

    def __init__(self, master: tk.Misc, **kwargs):
        super().__init__(master, background=CYAN, padx=2, pady=2, **kwargs)
        self.canvas = tk.Canvas(
            self,
            background=BACKGROUND,
            highlightthickness=0,
            height=190,
            cursor="crosshair",
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self._points: List[Point] = []
        self._drawing = False
        self.canvas.bind("<ButtonPress-1>", self._begin_stroke)
        self.canvas.bind("<B1-Motion>", self._extend_stroke)
        self.canvas.bind("<ButtonRelease-1>", self._end_stroke)

    @property
    def has_path(self) -> bool:
        return len(self._points) > 1

    def clear(self) -> None:
        self._points.clear()
        self._drawing = False
        self.canvas.delete("stroke")

    def get_screen_path(self, screen_width: int, screen_height: int) -> List[Point]:
        """Scale the drawn stroke to cover the full primary display."""
        if not self.has_path:
            return []
        canvas_width = max(1, self.canvas.winfo_width() - 1)
        canvas_height = max(1, self.canvas.winfo_height() - 1)
        display_width = max(1, screen_width - 1)
        display_height = max(1, screen_height - 1)
        return [
            (
                min(display_width, max(0, round(x * display_width / canvas_width))),
                min(display_height, max(0, round(y * display_height / canvas_height))),
            )
            for x, y in self._points
        ]

    def _begin_stroke(self, event: tk.Event) -> None:
        self.clear()
        self._drawing = True
        self._points.append((int(event.x), int(event.y)))
        self.canvas.create_oval(
            event.x - 2,
            event.y - 2,
            event.x + 2,
            event.y + 2,
            fill=CYAN,
            outline=CYAN,
            tags="stroke",
        )

    def _extend_stroke(self, event: tk.Event) -> None:
        if not self._drawing:
            return
        point = (int(event.x), int(event.y))
        if point == self._points[-1]:
            return
        previous = self._points[-1]
        self._points.append(point)
        self.canvas.create_line(
            previous[0],
            previous[1],
            point[0],
            point[1],
            fill=CYAN,
            width=3,
            capstyle=tk.ROUND,
            joinstyle=tk.ROUND,
            tags="stroke",
        )
        self.canvas.create_oval(
            point[0] - 2,
            point[1] - 2,
            point[0] + 2,
            point[1] + 2,
            fill=PURPLE,
            outline=PURPLE,
            tags="stroke",
        )

    def _end_stroke(self, _event: tk.Event) -> None:
        self._drawing = False
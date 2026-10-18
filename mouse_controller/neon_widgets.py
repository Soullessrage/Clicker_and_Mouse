"""Animated Tkinter controls used by the main window."""

import math
import tkinter as tk
from tkinter import font as tkfont
from typing import Callable, Optional

from neon_theme import (
    BORDER_COLORS,
    BUTTON_COLORS,
    CYAN,
    MUTED,
    PANEL,
    PANEL_HIGHLIGHT,
    PURPLE,
    SLIDER_COLORS,
    TEXT,
)


def _draw_rounded_rect(
    canvas: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    radius: float,
    fill: str,
    tags: str = "surface",
) -> None:
    radius = max(0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    corners = (
        (x2 - radius, y1 + radius, -90),
        (x2 - radius, y2 - radius, 0),
        (x1 + radius, y2 - radius, 90),
        (x1 + radius, y1 + radius, 180),
    )
    points = []
    for center_x, center_y, start_angle in corners:
        for step in range(9):
            angle = math.radians(start_angle + step * 90 / 8)
            points.extend((
                center_x + radius * math.cos(angle),
                center_y + radius * math.sin(angle),
            ))
    canvas.create_polygon(*points, fill=fill, outline=fill, smooth=True, splinesteps=24, tags=tags)


class NeonGlowButton(tk.Canvas):
    """A rounded canvas button with a restrained animated accent rim."""

    def __init__(self, master: tk.Misc, text: str, command: Callable[[], None], **kwargs):
        self._glow_index = 0
        self._glow_job: Optional[str] = None
        self._normal_background = kwargs.pop("background", PANEL_HIGHLIGHT)
        self._text = text
        self._command = command
        self._hovered = False
        parent_background = master.cget("background")
        super().__init__(
            master,
            width=kwargs.pop("width", 132),
            height=kwargs.pop("height", 42),
            background=parent_background,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
            takefocus=True,
            **kwargs,
        )
        self._font = tkfont.Font(
            self,
            family=tkfont.nametofont("TkDefaultFont").actual("family"),
            size=10,
            weight="bold",
        )
        self.bind("<Configure>", self._draw, add="+")
        self.bind("<Enter>", self._on_enter, add="+")
        self.bind("<Leave>", self._on_leave, add="+")
        self.bind("<Button-1>", self._invoke, add="+")
        self.bind("<Return>", self._invoke, add="+")
        self.bind("<space>", self._invoke, add="+")
        self.bind("<Destroy>", self._on_destroy, add="+")
        self._animate_glow()

    def _draw(self, _event: Optional[tk.Event] = None) -> None:
        width = self.winfo_width()
        height = self.winfo_height()
        if width < 2 or height < 2:
            return
        self.delete("surface")
        for depth, inset in enumerate((0, 1, 3)):
            color = BUTTON_COLORS[(self._glow_index + depth * 2) % len(BUTTON_COLORS)]
            _draw_rounded_rect(self, inset, inset, width - inset - 1, height - inset - 1, 12, color)
        face = PANEL_HIGHLIGHT if self._hovered else self._normal_background
        _draw_rounded_rect(self, 5, 5, width - 6, height - 6, 10, face)
        self.create_text(
            width / 2,
            height / 2,
            text=self._text,
            fill=CYAN if self._hovered else TEXT,
            font=self._font,
            tags="surface",
        )

    def _invoke(self, _event: tk.Event) -> None:
        if self._command is not None:
            self._command()

    def _animate_glow(self) -> None:
        if not self.winfo_exists():
            return
        self._glow_index = (self._glow_index + 1) % len(BUTTON_COLORS)
        self._draw()
        self._glow_job = self.after(240, self._animate_glow)

    def _on_enter(self, _event: tk.Event) -> None:
        self._hovered = True
        self._draw()

    def _on_leave(self, _event: tk.Event) -> None:
        self._hovered = False
        self._draw()

    def _on_destroy(self, _event: tk.Event) -> None:
        if self._glow_job is not None:
            try:
                self.after_cancel(self._glow_job)
            except tk.TclError:
                pass


class NeonToggle(tk.Canvas):
    """Compact animated toggle with a conventional Boolean interface."""

    def __init__(
        self,
        master: tk.Misc,
        command: Optional[Callable[[bool], None]] = None,
        initial: bool = False,
        **kwargs,
    ):
        super().__init__(
            master,
            width=58,
            height=30,
            background=kwargs.pop("background", PANEL),
            highlightthickness=0,
            bd=0,
            **kwargs,
        )
        self._value = bool(initial)
        self._enabled = True
        self._command = command
        self._pulse_index = 0
        self._pulse_job: Optional[str] = None
        self.bind("<Button-1>", self._toggle)
        self.bind("<space>", self._toggle)
        self.bind("<Destroy>", self._on_destroy, add="+")
        self._draw()
        self._animate()

    def get(self) -> bool:
        return self._value

    def set(self, value: bool, notify: bool = False) -> None:
        changed = self._value != bool(value)
        self._value = bool(value)
        self._draw()
        if changed and notify and self._command is not None:
            self._command(self._value)

    def configure(self, cnf=None, **kwargs):  # type: ignore[override]
        state = kwargs.pop("state", None)
        result = super().configure(cnf, **kwargs)
        if state is not None:
            self._enabled = state != tk.DISABLED
            self._draw()
        return result

    config = configure

    def _toggle(self, _event: tk.Event) -> None:
        if not self._enabled:
            return
        self._value = not self._value
        self._draw()
        if self._command is not None:
            self._command(self._value)

    def _draw(self) -> None:
        self.delete("all")
        color = CYAN if self._value else "#42516a"
        if not self._enabled:
            color = "#354155"
        self.create_oval(2, 2, 56, 28, fill="#0a1020", outline=color, width=2)
        knob_x = 40 if self._value else 18
        knob_color = color if self._value else "#a3b2c5"
        self.create_oval(knob_x - 8, 7, knob_x + 8, 23, fill=knob_color, outline="")

    def _animate(self) -> None:
        if not self.winfo_exists():
            return
        if self._value and self._enabled:
            self._pulse_index = (self._pulse_index + 1) % len(SLIDER_COLORS)
            self.delete("pulse")
            self.create_oval(
                1,
                1,
                57,
                29,
                outline=SLIDER_COLORS[self._pulse_index],
                width=1,
                tags="pulse",
            )
            self.tag_lower("pulse")
        self._pulse_job = self.after(260, self._animate)

    def _on_destroy(self, _event: tk.Event) -> None:
        if self._pulse_job is not None:
            try:
                self.after_cancel(self._pulse_job)
            except tk.TclError:
                pass


class NeonBorderFrame(tk.Canvas):
    """A rounded panel with a soft animated edge and regular Tk content."""

    def __init__(self, master: tk.Misc, title: str, **kwargs):
        background = kwargs.pop("background", PANEL)
        height = kwargs.pop("height", 270)
        parent_background = master.cget("background")
        super().__init__(
            master,
            background=parent_background,
            width=320,
            height=height,
            highlightthickness=0,
            bd=0,
            **kwargs,
        )
        self._border_index = 0
        self._border_job: Optional[str] = None
        self._panel_background = background
        self._content_frame = tk.Frame(self, background=background)
        self._content_window = self.create_window(
            8,
            8,
            anchor="nw",
            window=self._content_frame,
            width=1,
            height=1,
            tags="content-window",
        )
        self.title_label = tk.Label(
            self._content_frame,
            text=title,
            background=background,
            foreground=CYAN,
            anchor="w",
            font=(tkfont.nametofont("TkDefaultFont").actual("family"), 10, "bold"),
            padx=14,
            pady=10,
        )
        self.title_label.pack(fill=tk.X)
        self.content = tk.Frame(self._content_frame, background=background, padx=14, pady=10)
        self.content.pack(fill=tk.BOTH, expand=True)
        self.bind("<Configure>", self._draw_surface, add="+")
        self.bind("<Destroy>", self._on_destroy, add="+")
        self.after_idle(self._draw_surface)
        self._animate_border()

    def _draw_surface(self, _event: Optional[tk.Event] = None) -> None:
        width = self.winfo_width()
        height = self.winfo_height()
        if width < 2 or height < 2:
            return
        self.delete("surface")
        for depth, inset in enumerate((0, 1, 3)):
            color = BORDER_COLORS[(self._border_index + depth * 2) % len(BORDER_COLORS)]
            _draw_rounded_rect(self, inset, inset, width - inset - 1, height - inset - 1, 17, color)
        _draw_rounded_rect(self, 5, 5, width - 6, height - 6, 14, self._panel_background)
        self.coords(self._content_window, 9, 9)
        self.itemconfigure(
            self._content_window,
            width=max(1, width - 18),
            height=max(1, height - 18),
        )
        self.tag_lower("surface")

    def _animate_border(self) -> None:
        if not self.winfo_exists():
            return
        self._border_index = (self._border_index + 1) % len(BORDER_COLORS)
        self._draw_surface()
        self._border_job = self.after(420, self._animate_border)

    def _on_destroy(self, _event: tk.Event) -> None:
        if self._border_job is not None:
            try:
                self.after_cancel(self._border_job)
            except tk.TclError:
                pass


class NeonSlider(tk.Canvas):
    """A rounded, softly lit Tk scale with a live value readout."""

    def __init__(
        self,
        master: tk.Misc,
        label: str,
        from_: float,
        to: float,
        initial: float,
        command: Optional[Callable[[float], None]] = None,
        resolution: float = 1,
        **kwargs,
    ):
        background = kwargs.pop("background", PANEL)
        parent_background = master.cget("background")
        super().__init__(
            master,
            background=parent_background,
            width=320,
            height=66,
            highlightthickness=0,
            bd=0,
            **kwargs,
        )
        self._color_index = 0
        self._glow_job: Optional[str] = None
        self._command = command
        self._panel_background = background
        self._content_frame = tk.Frame(self, background=background)
        self._content_window = self.create_window(
            7,
            7,
            anchor="nw",
            window=self._content_frame,
            width=1,
            height=1,
            tags="content-window",
        )
        self._value_label = tk.Label(
            self._content_frame,
            text=f"{initial:g}",
            background=background,
            foreground=CYAN,
            font=(tkfont.nametofont("TkFixedFont").actual("family"), 10, "bold"),
            width=6,
            anchor="e",
        )
        tk.Label(
            self._content_frame,
            text=label,
            background=background,
            foreground=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")
        self._value_label.grid(row=0, column=1, sticky="e")
        self.scale = tk.Scale(
            self._content_frame,
            from_=from_,
            to=to,
            resolution=resolution,
            orient=tk.HORIZONTAL,
            showvalue=False,
            command=self._on_change,
            background=background,
            foreground=TEXT,
            activebackground=PURPLE,
            troughcolor="#26334d",
            highlightthickness=0,
            bd=0,
            sliderlength=18,
            sliderrelief=tk.FLAT,
            cursor="hand2",
        )
        self.scale.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(3, 0))
        self._content_frame.columnconfigure(0, weight=1)
        self.scale.set(initial)
        self.bind("<Configure>", self._draw_surface, add="+")
        self.bind("<Destroy>", self._on_destroy, add="+")
        self.after_idle(self._draw_surface)
        self._animate_glow()

    def get(self) -> float:
        return float(self.scale.get())

    def set(self, value: float) -> None:
        self.scale.set(value)

    def _on_change(self, value: str) -> None:
        number = float(value)
        self._value_label.configure(text=f"{number:g}")
        if self._command is not None:
            self._command(number)

    def _animate_glow(self) -> None:
        if not self.winfo_exists():
            return
        self._color_index = (self._color_index + 1) % len(SLIDER_COLORS)
        self._draw_surface()
        self._glow_job = self.after(360, self._animate_glow)

    def _draw_surface(self, _event: Optional[tk.Event] = None) -> None:
        width = self.winfo_width()
        height = self.winfo_height()
        if width < 2 or height < 2:
            return
        self.delete("surface")
        for depth, inset in enumerate((0, 1, 3)):
            color = SLIDER_COLORS[(self._color_index + depth * 2) % len(SLIDER_COLORS)]
            _draw_rounded_rect(self, inset, inset, width - inset - 1, height - inset - 1, 13, color)
        _draw_rounded_rect(self, 5, 5, width - 6, height - 6, 10, self._panel_background)
        self.coords(self._content_window, 9, 8)
        self.itemconfigure(
            self._content_window,
            width=max(1, width - 18),
            height=max(1, height - 16),
        )
        self.tag_lower("surface")

    def _on_destroy(self, _event: tk.Event) -> None:
        if self._glow_job is not None:
            try:
                self.after_cancel(self._glow_job)
            except tk.TclError:
                pass
"""Animated Tkinter controls used by the main window."""

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


def _make_glow_layers(master: tk.Misc, palette: tuple[str, ...]):
    layers = []
    parent = master
    for index in range(3):
        layer = tk.Frame(parent, background=palette[index])
        layer.pack(fill=tk.BOTH, expand=True, padx=1 if index else 0, pady=1 if index else 0)
        layers.append(layer)
        parent = layer
    return parent, layers


class NeonGlowButton(tk.Frame):
    """A flat button whose border color softly cycles while it is visible."""

    def __init__(self, master: tk.Misc, text: str, command: Callable[[], None], **kwargs):
        self._glow_index = 0
        self._glow_job: Optional[str] = None
        self._normal_background = kwargs.pop("background", PANEL_HIGHLIGHT)
        super().__init__(
            master,
            background=self._normal_background,
            highlightthickness=0,
        )
        button_parent, self._glow_layers = _make_glow_layers(self, BORDER_COLORS)
        self.button = tk.Button(
            button_parent,
            text=text,
            command=command,
            background=self._normal_background,
            foreground=TEXT,
            activebackground=PANEL,
            activeforeground=CYAN,
            disabledforeground=MUTED,
            relief=tk.FLAT,
            borderwidth=0,
            padx=12,
            pady=8,
            cursor="hand2",
            font=(tkfont.nametofont("TkDefaultFont").actual("family"), 10, "bold"),
            **kwargs,
        )
        self.button.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        for widget in [self.button, *self._glow_layers]:
            widget.bind("<Enter>", self._on_enter, add="+")
            widget.bind("<Leave>", self._on_leave, add="+")
        self.bind("<Destroy>", self._on_destroy, add="+")
        self._animate_glow()

    def _animate_glow(self) -> None:
        if not self.winfo_exists():
            return
        palette = BUTTON_COLORS
        for depth, layer in enumerate(self._glow_layers):
            color_index = min(self._glow_index + depth, len(palette) - 1)
            layer.configure(background=palette[color_index])
        self._glow_index = (self._glow_index + 1) % len(BUTTON_COLORS)
        self._glow_job = self.after(130, self._animate_glow)

    def _on_enter(self, _event: tk.Event) -> None:
        self.button.configure(background=PURPLE)

    def _on_leave(self, _event: tk.Event) -> None:
        self.button.configure(background=self._normal_background)

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


class NeonBorderFrame(tk.Frame):
    """A padded frame with an animated neon outline."""

    def __init__(self, master: tk.Misc, title: str, **kwargs):
        background = kwargs.pop("background", PANEL)
        super().__init__(master, background=background, highlightthickness=0, **kwargs)
        self._border_index = 0
        self._border_job: Optional[str] = None
        content_parent, self._glow_layers = _make_glow_layers(self, BORDER_COLORS)
        content_parent.configure(background=background)
        self.title_label = tk.Label(
            content_parent,
            text=title.upper(),
            background=background,
            foreground=CYAN,
            anchor="w",
            font=(tkfont.nametofont("TkDefaultFont").actual("family"), 9, "bold"),
            padx=12,
            pady=9,
        )
        self.title_label.pack(fill=tk.X)
        self.content = tk.Frame(content_parent, background=background, padx=12, pady=8)
        self.content.pack(fill=tk.BOTH, expand=True)
        self.bind("<Destroy>", self._on_destroy, add="+")
        self._animate_border()

    def _animate_border(self) -> None:
        if not self.winfo_exists():
            return
        for depth, layer in enumerate(self._glow_layers):
            color_index = min(self._border_index + depth, len(BORDER_COLORS) - 1)
            layer.configure(background=BORDER_COLORS[color_index])
        self._border_index = (self._border_index + 1) % len(BORDER_COLORS)
        self._border_job = self.after(150, self._animate_border)

    def _on_destroy(self, _event: tk.Event) -> None:
        if self._border_job is not None:
            try:
                self.after_cancel(self._border_job)
            except tk.TclError:
                pass


class NeonSlider(tk.Frame):
    """Labeled Tk scale with an animated neon frame and numeric readout."""

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
        super().__init__(master, background=background, highlightthickness=0, **kwargs)
        self._color_index = 0
        self._glow_job: Optional[str] = None
        self._command = command
        content_parent, self._glow_layers = _make_glow_layers(self, SLIDER_COLORS)
        content_parent.configure(background=background)
        self._value_label = tk.Label(
            content_parent,
            text=f"{initial:g}",
            background=background,
            foreground=CYAN,
            font=(tkfont.nametofont("TkFixedFont").actual("family"), 10, "bold"),
            width=6,
            anchor="e",
        )
        tk.Label(
            content_parent,
            text=label,
            background=background,
            foreground=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")
        self._value_label.grid(row=0, column=1, sticky="e")
        self.scale = tk.Scale(
            content_parent,
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
        content_parent.columnconfigure(0, weight=1)
        self.scale.set(initial)
        self.bind("<Destroy>", self._on_destroy, add="+")
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
        for depth, layer in enumerate(self._glow_layers):
            color_index = min(self._color_index + depth, len(SLIDER_COLORS) - 1)
            layer.configure(background=SLIDER_COLORS[color_index])
        self._color_index = (self._color_index + 1) % len(SLIDER_COLORS)
        self._glow_job = self.after(140, self._animate_glow)

    def _on_destroy(self, _event: tk.Event) -> None:
        if self._glow_job is not None:
            try:
                self.after_cancel(self._glow_job)
            except tk.TclError:
                pass
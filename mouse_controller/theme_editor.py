"""Separate editor window for application themes and section colors."""

import tkinter as tk
from tkinter import colorchooser, messagebox, ttk
from typing import Callable

from theme_manager import PRESETS, SECTIONS, TOGGLE_STYLES, ThemeManager


class AppearanceEditor:
    """Edit and persist visual preferences without cluttering the main window."""

    def __init__(self, master: tk.Tk, theme: ThemeManager, on_apply: Callable[[], None]):
        self.master = master
        self.theme = theme
        self.on_apply = on_apply
        self.window = tk.Toplevel(master)
        self.window.title("Appearance Settings")
        self.window.geometry("520x610")
        self.window.minsize(480, 560)
        self.window.transient(master)
        self.window.configure(background=self.theme.colors()["background"])
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.section_var = tk.StringVar(value="Auto Clicker")
        self.preset_var = tk.StringVar(value=self.theme.preset)
        self.mode_var = tk.StringVar(value=self.theme.mode.title())
        self.toggle_var = tk.StringVar(value=self.theme.toggle_style)
        self._build()
        self._refresh_swatches()
        self.window.grab_set()

    def _build(self) -> None:
        colors = self.theme.colors()
        self.window.configure(background=colors["background"])
        style = ttk.Style(self.window)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Appearance.TCombobox",
            fieldbackground=colors["panel_highlight"],
            background=colors["panel"],
            foreground=colors["text"],
            arrowcolor=colors["accent"],
            bordercolor=colors["accent"],
            padding=6,
        )
        style.map(
            "Appearance.TCombobox",
            fieldbackground=[("readonly", colors["panel_highlight"])],
            selectbackground=[("readonly", colors["panel_highlight"])],
            selectforeground=[("readonly", colors["text"])],
        )
        outer = tk.Frame(self.window, background=colors["background"], padx=22, pady=20)
        outer.pack(fill=tk.BOTH, expand=True)
        tk.Label(
            outer,
            text="Appearance",
            background=colors["background"],
            foreground=colors["text"],
            font=("TkDefaultFont", 18, "bold"),
        ).pack(anchor="w")
        tk.Label(
            outer,
            text="Choose a preset, then fine-tune each surface and path color.",
            background=colors["background"],
            foreground=colors["muted"],
            wraplength=450,
            justify=tk.LEFT,
        ).pack(anchor="w", pady=(4, 16))

        preset_row = tk.Frame(outer, background=colors["background"])
        preset_row.pack(fill=tk.X, pady=4)
        self._label(preset_row, "Theme preset", colors).pack(side=tk.LEFT)
        preset_box = ttk.Combobox(
            preset_row,
            textvariable=self.preset_var,
            values=tuple(PRESETS),
            state="readonly",
            width=20,
            style="Appearance.TCombobox",
        )
        preset_box.pack(side=tk.RIGHT)
        preset_box.bind("<<ComboboxSelected>>", self._on_preset)

        mode_row = tk.Frame(outer, background=colors["background"])
        mode_row.pack(fill=tk.X, pady=4)
        self._label(mode_row, "Appearance mode", colors).pack(side=tk.LEFT)
        mode_box = ttk.Combobox(
            mode_row,
            textvariable=self.mode_var,
            values=("Light", "Dark"),
            state="readonly",
            width=20,
            style="Appearance.TCombobox",
        )
        mode_box.pack(side=tk.RIGHT)
        mode_box.bind("<<ComboboxSelected>>", self._on_mode)

        toggle_row = tk.Frame(outer, background=colors["background"])
        toggle_row.pack(fill=tk.X, pady=4)
        self._label(toggle_row, "Toggle switch style", colors).pack(side=tk.LEFT)
        toggle_box = ttk.Combobox(
            toggle_row,
            textvariable=self.toggle_var,
            values=TOGGLE_STYLES,
            state="readonly",
            width=20,
            style="Appearance.TCombobox",
        )
        toggle_box.pack(side=tk.RIGHT)
        toggle_box.bind("<<ComboboxSelected>>", self._on_toggle_style)

        self._section = tk.Frame(
            outer,
            background=colors["panel"],
            padx=14,
            pady=12,
            highlightthickness=1,
            highlightbackground=colors["accent"],
        )
        self._section.pack(fill=tk.X, pady=(18, 0))
        tk.Label(
            self._section,
            text="BOX COLORS",
            background=colors["panel"],
            foreground=colors["accent"],
            font=("TkDefaultFont", 9, "bold"),
        ).pack(anchor="w", pady=(0, 8))
        self.section_box = ttk.Combobox(
            self._section,
            textvariable=self.section_var,
            values=tuple(SECTIONS),
            state="readonly",
            style="Appearance.TCombobox",
        )
        self.section_box.pack(fill=tk.X)
        self.section_box.bind("<<ComboboxSelected>>", lambda _event: self._refresh_swatches())

        self.surface_button = tk.Button(
            self._section,
            text="Box surface",
            anchor="w",
            relief=tk.FLAT,
            padx=10,
            pady=8,
            command=lambda: self._choose_section_color("panel"),
        )
        self.surface_button.pack(fill=tk.X, pady=(10, 0))
        self.border_button = tk.Button(
            self._section,
            text="Frame accent",
            anchor="w",
            relief=tk.FLAT,
            padx=10,
            pady=8,
            command=lambda: self._choose_section_color("accent"),
        )
        self.border_button.pack(fill=tk.X, pady=(6, 0))

        self.path_button = tk.Button(
            outer,
            text="Draw path color",
            anchor="w",
            relief=tk.FLAT,
            padx=10,
            pady=8,
            command=self._choose_path_color,
        )
        self.path_button.pack(fill=tk.X, pady=(10, 0))

        footer = tk.Frame(outer, background=colors["background"])
        footer.pack(fill=tk.X, side=tk.BOTTOM, pady=(20, 0))
        tk.Button(
            footer,
            text="Reset to Windows XP",
            command=self._reset,
            relief=tk.FLAT,
            padx=12,
            pady=8,
        ).pack(side=tk.LEFT)
        tk.Button(
            footer,
            text="Apply",
            command=self._apply,
            relief=tk.FLAT,
            padx=16,
            pady=8,
            background=colors["accent"],
            foreground=colors["text"],
        ).pack(side=tk.RIGHT)

    def _label(self, parent: tk.Misc, text: str, colors):
        return tk.Label(
            parent,
            text=text,
            background=colors["background"],
            foreground=colors["text"],
        )

    def _on_preset(self, _event: tk.Event) -> None:
        self.theme.set_preset(self.preset_var.get())
        self._refresh_swatches()
        self._apply()

    def _on_mode(self, _event: tk.Event) -> None:
        self.theme.set_mode(self.mode_var.get().lower())
        self._refresh_swatches()
        self._apply()

    def _on_toggle_style(self, _event: tk.Event) -> None:
        self.theme.set_toggle_style(self.toggle_var.get())
        self._apply()

    def _choose_section_color(self, key: str) -> None:
        section = SECTIONS[self.section_var.get()]
        current = self.theme.colors(section)[key]
        selected = colorchooser.askcolor(current, parent=self.window, title="Choose a color")[1]
        if selected:
            self.theme.set_section_color(section, key, selected)
            self._refresh_swatches()
            self._apply()

    def _choose_path_color(self) -> None:
        selected = colorchooser.askcolor(
            self.theme.path_color(),
            parent=self.window,
            title="Choose draw path color",
        )[1]
        if selected:
            self.theme.set_path_color(selected)
            self._refresh_swatches()
            self._apply()

    def _refresh_swatches(self) -> None:
        section = SECTIONS[self.section_var.get()]
        colors = self.theme.colors(section)
        self._section.configure(background=colors["panel"], highlightbackground=colors["accent"])
        self.surface_button.configure(
            background=colors["panel"],
            foreground=colors["text"],
            activebackground=colors["panel_highlight"],
        )
        self.border_button.configure(
            background=colors["accent"],
            foreground=colors["text"],
            activebackground=colors["accent_alt"],
        )
        self.path_button.configure(
            background=self.theme.path_color(),
            foreground=colors["text"],
            activebackground=colors["accent_alt"],
        )

    def _apply(self) -> None:
        self.preset_var.set(self.theme.preset)
        self.mode_var.set(self.theme.mode.title())
        self.toggle_var.set(self.theme.toggle_style)
        for child in self.window.winfo_children():
            child.destroy()
        self._build()
        self._refresh_swatches()
        self.on_apply()

    def _reset(self) -> None:
        if not messagebox.askyesno(
            "Reset appearance",
            "Reset presets, custom colors, and toggle style to the Windows XP defaults?",
            parent=self.window,
        ):
            return
        self.theme.reset()
        self.preset_var.set(self.theme.preset)
        self.mode_var.set(self.theme.mode.title())
        self.toggle_var.set(self.theme.toggle_style)
        self._refresh_swatches()
        self._apply()

    def close(self) -> None:
        try:
            self.window.grab_release()
        except tk.TclError:
            pass
        self.window.destroy()
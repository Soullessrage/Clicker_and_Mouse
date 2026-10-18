"""Persistent color presets and per-section appearance settings."""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Optional

ColorMap = Dict[str, str]


def _palette(
    background: str,
    panel: str,
    panel_highlight: str,
    text: str,
    muted: str,
    accent: str,
    accent_alt: str,
    path: str,
    track: str,
    thumb: str,
) -> ColorMap:
    return {
        "background": background,
        "panel": panel,
        "panel_highlight": panel_highlight,
        "text": text,
        "muted": muted,
        "accent": accent,
        "accent_alt": accent_alt,
        "path": path,
        "track": track,
        "thumb": thumb,
        "warning": "#9A5B00" if background.startswith("#E") else "#F4B860",
        "error": "#B42335" if background.startswith("#E") else "#F27387",
    }


PRESETS = {
    "Windows XP": {
        "light": _palette("#ECE9D8", "#F7F5EC", "#FFFFFF", "#17243A", "#59677A", "#1768D2", "#75B5F5", "#C3262D", "#CBD5E3", "#1768D2"),
        "dark": _palette("#171C25", "#222A36", "#2B3543", "#F0F3F7", "#AAB5C4", "#62A9FF", "#A6D2FF", "#FF727A", "#394657", "#62A9FF"),
    },
    "Windows 11": {
        "light": _palette("#F3F3F3", "#FFFFFF", "#F8F8F8", "#202020", "#666666", "#0067C0", "#60CDFF", "#C42B1C", "#E5E5E5", "#0067C0"),
        "dark": _palette("#202020", "#2B2B2B", "#353535", "#F5F5F5", "#B9B9B9", "#60CDFF", "#9ADCFB", "#FF7B72", "#454545", "#60CDFF"),
    },
    "Midnight": {
        "light": _palette("#E8EDF2", "#F4F7FA", "#FFFFFF", "#1C2836", "#687789", "#365D9A", "#7396C7", "#C94C68", "#CED8E3", "#365D9A"),
        "dark": _palette("#101720", "#19232F", "#222F3D", "#E9F0F7", "#9CAFC1", "#83B8FF", "#B5D5FF", "#FF758A", "#334252", "#83B8FF"),
    },
    "Mint": {
        "light": _palette("#EAF3EF", "#F4FAF7", "#FFFFFF", "#19372F", "#607970", "#2E8B71", "#70BEA1", "#C54F60", "#CCDCD5", "#2E8B71"),
        "dark": _palette("#101A18", "#1B2925", "#253833", "#E9F5F0", "#A0B7AE", "#68CDAA", "#A3E7CF", "#FF7C86", "#354A43", "#68CDAA"),
    },
    "Sunset": {
        "light": _palette("#F4EDE7", "#FBF6F1", "#FFFFFF", "#38291F", "#7B695C", "#B86638", "#E3A16D", "#B83F55", "#DFD0C2", "#B86638"),
        "dark": _palette("#1D1716", "#2B211F", "#382925", "#F6EDE8", "#BDA89C", "#F09A68", "#FFC28E", "#FF7180", "#4B3932", "#F09A68"),
    },
    "Dragon's Hoard": {
        "light": _palette("#E9DFC9", "#F7F0DF", "#FFF9E9", "#33271D", "#75624B", "#8C5A22", "#D8A64E", "#9A3535", "#D4C6AA", "#8C5A22"),
        "dark": _palette("#191611", "#282117", "#382D1C", "#F2E4C6", "#B3A17F", "#D8A64E", "#EACB78", "#D96454", "#4B3B25", "#D8A64E"),
    },
    "Arcane": {
        "light": _palette("#E8E5F0", "#F6F3FA", "#FFFFFF", "#292139", "#716783", "#6745A5", "#A181D1", "#B74668", "#D8D0E4", "#6745A5"),
        "dark": _palette("#17131F", "#221B2D", "#30253E", "#F2ECFA", "#B5A9C5", "#BB9AF7", "#D9C2FF", "#FF7C9A", "#443553", "#BB9AF7"),
    },
    "Cyberpunk": {
        "light": _palette("#E8EEF2", "#F6FAFC", "#FFFFFF", "#1B2832", "#637783", "#007E87", "#00AEB2", "#D83E67", "#C9D8DE", "#007E87"),
        "dark": _palette("#10171D", "#18232A", "#213139", "#E8F5F6", "#9DB3B7", "#5FE3D0", "#B0F7E9", "#FF527A", "#30434A", "#5FE3D0"),
    },
}

SECTIONS = {
    "Auto Clicker": "clicker",
    "Path Follower": "path",
    "Draw Path": "canvas",
}
TOGGLE_STYLES = ("XP", "Pill", "Minimal", "Switch", "Checkbox")
BOX_STYLES = ("Soft Rounded", "Windows XP", "Square", "Outlined")
DEFAULT_PRESET = "Windows XP"


class ThemeManager:
    """Load, validate, and persist the app's appearance preferences."""

    def __init__(self, settings_path: Optional[Path] = None):
        self.settings_path = settings_path or self._default_settings_path()
        self.settings = {
            "preset": DEFAULT_PRESET,
            "mode": "light",
            "toggle_style": "XP",
            "box_style": "Windows XP",
            "font_family": "System Default",
            "section_overrides": {},
            "path_color": None,
        }
        self._load()

    @staticmethod
    def _default_settings_path() -> Path:
        if os.name == "nt":
            base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
            return base / "Neon Mouse Controller" / "appearance.json"
        if sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / "Neon Mouse Controller" / "appearance.json"
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        return base / "neon-mouse-controller" / "appearance.json"

    @property
    def preset(self) -> str:
        return self.settings["preset"]

    @property
    def mode(self) -> str:
        return self.settings["mode"]

    @property
    def toggle_style(self) -> str:
        return self.settings["toggle_style"]

    @property
    def box_style(self) -> str:
        return self.settings["box_style"]

    @property
    def font_family(self) -> str:
        return self.settings["font_family"]

    def colors(self, section: Optional[str] = None) -> ColorMap:
        colors = dict(PRESETS[self.preset][self.mode])
        if section:
            override = self.settings["section_overrides"].get(section, {})
            colors.update(override)
        return colors

    def path_color(self) -> str:
        return self.settings.get("path_color") or self.colors("canvas")["path"]

    def glow_colors(self, section: Optional[str] = None) -> tuple[str, ...]:
        colors = self.colors(section)
        background = colors["panel"]
        accent = colors["accent"]
        background_channels = tuple(int(background[index:index + 2], 16) for index in (1, 3, 5))
        accent_channels = tuple(int(accent[index:index + 2], 16) for index in (1, 3, 5))
        levels = (0.25, 0.40, 0.58, 0.76, 0.58, 0.40)
        return tuple(
            "#" + "".join(
                f"{round(base + (glow - base) * level):02x}"
                for base, glow in zip(background_channels, accent_channels)
            )
            for level in levels
        )

    def set_preset(self, preset: str) -> None:
        if preset not in PRESETS:
            raise ValueError(f"Unknown theme preset: {preset}")
        self.settings["preset"] = preset
        self.settings["box_style"] = "Windows XP" if preset == "Windows XP" else "Soft Rounded"
        self.settings["section_overrides"] = {}
        self.settings["path_color"] = None
        self.save()

    def set_mode(self, mode: str) -> None:
        if mode not in ("light", "dark"):
            raise ValueError(f"Unknown appearance mode: {mode}")
        self.settings["mode"] = mode
        self.save()

    def set_toggle_style(self, style: str) -> None:
        if style not in TOGGLE_STYLES:
            raise ValueError(f"Unknown toggle style: {style}")
        self.settings["toggle_style"] = style
        self.save()

    def set_box_style(self, style: str) -> None:
        if style not in BOX_STYLES:
            raise ValueError(f"Unknown box style: {style}")
        self.settings["box_style"] = style
        self.save()

    def set_font_family(self, family: str) -> None:
        family = family.strip()
        if not family or len(family) > 64:
            raise ValueError("Choose a valid installed font")
        self.settings["font_family"] = family
        self.save()

    def set_section_color(self, section: str, key: str, color: str) -> None:
        if section not in SECTIONS.values() or key not in ("panel", "accent"):
            raise ValueError("Choose a valid box and either its surface or frame color")
        self._validate_color(color)
        self.settings["section_overrides"].setdefault(section, {})[key] = color.lower()
        self.save()

    def set_path_color(self, color: str) -> None:
        self._validate_color(color)
        self.settings["path_color"] = color.lower()
        self.save()

    def reset(self) -> None:
        self.settings = {
            "preset": DEFAULT_PRESET,
            "mode": "light",
            "toggle_style": "XP",
            "box_style": "Windows XP",
            "font_family": "System Default",
            "section_overrides": {},
            "path_color": None,
        }
        self.save()

    def save(self) -> None:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.settings_path.with_suffix(".tmp")
        temporary_path.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")
        os.replace(temporary_path, self.settings_path)

    def _load(self) -> None:
        try:
            saved = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(saved, dict):
            return
        preset = saved.get("preset")
        mode = saved.get("mode")
        style = saved.get("toggle_style")
        box_style = saved.get("box_style")
        font_family = saved.get("font_family")
        if preset in PRESETS:
            self.settings["preset"] = preset
        if mode in ("light", "dark"):
            self.settings["mode"] = mode
        if style in TOGGLE_STYLES:
            self.settings["toggle_style"] = style
        if box_style in BOX_STYLES:
            self.settings["box_style"] = box_style
        if isinstance(font_family, str) and font_family.strip() and len(font_family) <= 64:
            self.settings["font_family"] = font_family.strip()
        saved_overrides = saved.get("section_overrides", {})
        if not isinstance(saved_overrides, dict):
            saved_overrides = {}
        for section, overrides in saved_overrides.items():
            if section not in SECTIONS.values() or not isinstance(overrides, dict):
                continue
            for key in ("panel", "accent"):
                color = overrides.get(key)
                if isinstance(color, str) and self._is_valid_color(color):
                    self.settings["section_overrides"].setdefault(section, {})[key] = color.lower()
        path_color = saved.get("path_color")
        if isinstance(path_color, str) and self._is_valid_color(path_color):
            self.settings["path_color"] = path_color.lower()

    @staticmethod
    def _is_valid_color(color: str) -> bool:
        return re.fullmatch(r"#[0-9a-fA-F]{6}", color) is not None

    @classmethod
    def _validate_color(cls, color: str) -> None:
        if not cls._is_valid_color(color):
            raise ValueError("Colors must use the #RRGGBB format")
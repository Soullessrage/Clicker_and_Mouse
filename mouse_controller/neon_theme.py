"""Shared colors and dimensions for the Neon Mouse Controller UI."""

BACKGROUND = "#0a0f1f"
PANEL = "#111a2e"
PANEL_HIGHLIGHT = "#18243b"
CYAN = "#7df9ff"
CYAN_DIM = "#287f8a"
PURPLE = "#9d4bff"
PURPLE_DIM = "#5b338a"
TEXT = "#e8f4ff"
MUTED = "#91a4bc"
WARNING = "#ffb454"
ERROR = "#ff5c8a"
FONT = "TkDefaultFont"
MONO_FONT = "TkFixedFont"

def _blend_with_background(color: str, amount: float) -> str:
	background = tuple(int(BACKGROUND[index:index + 2], 16) for index in (1, 3, 5))
	foreground = tuple(int(color[index:index + 2], 16) for index in (1, 3, 5))
	channels = [round(base + (light - base) * amount) for base, light in zip(background, foreground)]
	return "#" + "".join(f"{channel:02x}" for channel in channels)


def _feathered_palette(color: str) -> tuple[str, ...]:
	levels = (0.24, 0.34, 0.48, 0.64, 0.78, 0.64, 0.48, 0.34)
	return tuple(_blend_with_background(color, level) for level in levels)


CYAN_GLOW = _feathered_palette(CYAN)
PURPLE_GLOW = _feathered_palette(PURPLE)
BUTTON_COLORS = CYAN_GLOW + PURPLE_GLOW
BORDER_COLORS = CYAN_GLOW
SLIDER_COLORS = CYAN_GLOW
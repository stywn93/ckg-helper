"""
ui_theme.py - design tokens and styled widget helpers for CKG Helper (CustomTkinter).

Everything visual lives here so app.py only describes structure:
  * C            - color tokens, each a (light, dark) tuple so CTk switches automatically
  * font()       - system font on macOS
  * icon()       - monochrome Lucide PNGs from ./icons, tinted per theme
  * button() / style_button() / entry() / option_menu() / checkbox() / textbox() / card()
  * NavButton    - sidebar item with active state and optional badge dot
  * ThemeSwitcher- System / Light / Dark segmented control (persist via save_appearance)
"""
import json
import sys
from pathlib import Path

import customtkinter as ctk
from PIL import Image

IS_MAC = sys.platform == "darwin"
IS_WIN = sys.platform == "win32"


# ---------------------------------------------------------------------------
# Colors. One accent (blue) for the single primary action on a page; the rest
# is neutral. Text colors were chosen for >= 4.5:1 contrast on their surface.
# ---------------------------------------------------------------------------
class C:
    BG            = ("#F2F2F4", "#1C1C1E")
    SIDEBAR       = ("#E7E7EA", "#242426")
    CARD          = ("#FFFFFF", "#2B2B2D")
    INPUT         = ("#FFFFFF", "#1E1E20")
    BORDER        = ("#DCDCE1", "#3A3A3D")
    BORDER_STRONG = ("#C4C6CD", "#56565A")

    TEXT          = ("#1D1D1F", "#F2F2F4")
    TEXT_MUTED    = ("#5C6068", "#A9ADB5")
    TEXT_DISABLED = ("#9EA1A8", "#707278")
    ON_ACCENT     = ("#FFFFFF", "#FFFFFF")

    ACCENT        = ("#0A64D8", "#2F7DE1")
    ACCENT_HOVER  = ("#0852B3", "#2569BF")
    ACCENT_TEXT   = ("#0A64D8", "#6AA9FF")

    NEUTRAL       = ("#E3E4E8", "#3A3A3D")
    NEUTRAL_HOVER = ("#D3D5DB", "#47474B")
    SELECTED      = ("#D6D8DE", "#3A3A3E")

    DANGER        = ("#D13438", "#D6454A")
    DANGER_HOVER  = ("#B52A2E", "#BC3A3F")

    SUCCESS       = ("#157F3B", "#4ADE80")
    WARNING       = ("#B45309", "#F5B73B")
    DANGER_TEXT   = ("#C62828", "#FF6B6B")

    ICON          = ("#4A4D55", "#D8DAE0")
    ICON_ON_FILL  = ("#FFFFFF", "#FFFFFF")

    SEG_BG        = ("#DADBE0", "#38383B")
    SEG_SELECTED  = ("#FFFFFF", "#58585D")


STATUS_COLORS = {"ok": C.SUCCESS, "warn": C.WARNING, "danger": C.DANGER_TEXT,
                 "muted": C.TEXT_MUTED, "accent": C.ACCENT_TEXT}


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------
def font(size=13, weight="normal"):
    family = ".AppleSystemUIFont" if IS_MAC else None   # None = CTk default
    return ctk.CTkFont(family=family, size=size, weight=weight)


def mono_font(size=12):
    family = "Menlo" if IS_MAC else ("Consolas" if IS_WIN else "DejaVu Sans Mono")
    return ctk.CTkFont(family=family, size=size)


# ---------------------------------------------------------------------------
# Appearance (System by default) + persistence
# ---------------------------------------------------------------------------
_MODES = ("System", "Light", "Dark")
_SETTINGS_NAME = "ui_settings.json"


def load_appearance(app_root, default="System"):
    try:
        data = json.loads((Path(app_root) / _SETTINGS_NAME).read_text(encoding="utf-8"))
        mode = data.get("appearance", default)
        return mode if mode in _MODES else default
    except Exception:
        return default


def save_appearance(app_root, mode):
    try:
        path = Path(app_root) / _SETTINGS_NAME
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        data["appearance"] = mode
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass   # a failed preference save must never break the app


def init_appearance(mode="System"):
    ctk.set_appearance_mode(mode)    # call BEFORE creating the window


def setup_window(root, on_preferences=None, page_shortcuts=None):
    """root background, macOS Settings menu (Cmd+,), Cmd+W, and Cmd/Ctrl+1..n page shortcuts."""
    root.configure(fg_color=C.BG)
    mod = "Command" if IS_MAC else "Control"
    if IS_MAC:
        if on_preferences:
            root.createcommand("tk::mac::ShowPreferences", on_preferences)
        root.bind("<Command-w>", lambda e: root.destroy())
    for i, fn in enumerate(page_shortcuts or [], start=1):
        root.bind(f"<{mod}-Key-{i}>", lambda e, f=fn: f())


# ---------------------------------------------------------------------------
# Icons: Lucide PNGs (transparent, any color) tinted to the current theme.
# Missing files return None so a packaging mistake never crashes the UI.
# ---------------------------------------------------------------------------
def _base_dir():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


ICON_DIR = _base_dir() / "icons"
_icon_cache = {}


def icon(name, size=18, color=None):
    color = color or C.ICON
    if isinstance(color, str):
        color = (color, color)
    key = (name, size, tuple(color))
    if key in _icon_cache:
        return _icon_cache[key]
    try:
        base = Image.open(ICON_DIR / f"{name}.png").convert("RGBA")
    except Exception:
        _icon_cache[key] = None
        return None
    alpha = base.split()[3]

    def tint(hex_color):
        layer = Image.new("RGBA", base.size, hex_color)
        layer.putalpha(alpha)
        return layer

    img = ctk.CTkImage(light_image=tint(color[0]), dark_image=tint(color[1]), size=(size, size))
    _icon_cache[key] = img
    return img


# ---------------------------------------------------------------------------
# Buttons
# ---------------------------------------------------------------------------
_BUTTON_STYLES = {
    "primary":   dict(fg=C.ACCENT,  hover=C.ACCENT_HOVER,  text=C.ON_ACCENT, icon=C.ICON_ON_FILL, bold=True),
    "secondary": dict(fg=C.NEUTRAL, hover=C.NEUTRAL_HOVER, text=C.TEXT,      icon=C.ICON,         bold=False),
    "danger":    dict(fg=C.DANGER,  hover=C.DANGER_HOVER,  text=C.ON_ACCENT, icon=C.ICON_ON_FILL, bold=True),
}


def style_button(btn, kind="secondary", icon_name=None, icon_size=16):
    """Re-skin an existing button (used for run/stop state changes)."""
    s = _BUTTON_STYLES[kind]
    opts = dict(fg_color=s["fg"], hover_color=s["hover"], text_color=s["text"])
    if icon_name:
        opts["image"] = icon(icon_name, icon_size, s["icon"])
    btn.configure(**opts)


def button(master, text, command=None, kind="secondary", icon_name=None,
           height=34, width=None, size=13):
    s = _BUTTON_STYLES[kind]
    f = font(size, "bold" if s["bold"] else "normal")
    img = icon(icon_name, 16, s["icon"]) if icon_name else None
    if width is None:                      # CTkButton clips text, so size to content
        width = max(72, f.measure(text) + 34 + (22 if img else 0))
    return ctk.CTkButton(
        master, text=text, command=command, image=img, compound="left",
        height=height, width=width, corner_radius=8, font=f,
        fg_color=s["fg"], hover_color=s["hover"], text_color=s["text"],
        text_color_disabled=C.TEXT_DISABLED,
    )


def primary_button(master, text, command=None, icon_name=None, **kw):
    return button(master, text, command, "primary", icon_name, **kw)


def secondary_button(master, text, command=None, icon_name=None, **kw):
    return button(master, text, command, "secondary", icon_name, **kw)


def danger_button(master, text, command=None, icon_name=None, **kw):
    return button(master, text, command, "danger", icon_name, **kw)


class NavButton(ctk.CTkButton):
    """Sidebar item: subtle highlight when active, optional badge dot."""
    def __init__(self, master, text, icon_name, command):
        super().__init__(
            master, text=text, image=icon(icon_name, 18), compound="left",
            anchor="w", height=36, corner_radius=8, font=font(13),
            fg_color="transparent", hover_color=C.NEUTRAL,
            text_color=C.TEXT, command=command,
        )
        self._dot = ctk.CTkFrame(master, width=8, height=8, corner_radius=4,
                                 fg_color=C.ACCENT, border_width=0)

    def set_active(self, active):
        self.configure(fg_color=C.SELECTED if active else "transparent")

    def set_badge(self, on):
        if on:
            self._dot.place(in_=self, relx=1.0, x=-14, rely=0.5, anchor="e")
            self._dot.lift()
        else:
            self._dot.place_forget()


class ThemeSwitcher(ctk.CTkSegmentedButton):
    """System / Light / Dark. save_cb(mode) persists the choice."""
    def __init__(self, master, current="System", save_cb=None):
        def _change(value):
            ctk.set_appearance_mode(value)
            if save_cb:
                save_cb(value)
        super().__init__(
            master, values=list(_MODES), command=_change, font=font(12),
            corner_radius=8, height=30,
            fg_color=C.SEG_BG, unselected_color=C.SEG_BG,
            unselected_hover_color=C.NEUTRAL_HOVER,
            selected_color=C.SEG_SELECTED, selected_hover_color=C.SEG_SELECTED,
            text_color=C.TEXT,
        )
        self.set(current)


# ---------------------------------------------------------------------------
# Inputs and containers
# ---------------------------------------------------------------------------
def entry(master, **kw):
    return ctk.CTkEntry(
        master, height=34, corner_radius=8, border_width=1, font=font(13),
        fg_color=C.INPUT, border_color=C.BORDER_STRONG, text_color=C.TEXT,
        placeholder_text_color=C.TEXT_DISABLED, **kw)


def option_menu(master, values, command=None, width=320):
    return ctk.CTkOptionMenu(
        master, values=values, command=command, width=width, height=34,
        corner_radius=8, font=font(13), dropdown_font=font(13),
        fg_color=C.NEUTRAL, button_color=C.NEUTRAL_HOVER,
        button_hover_color=C.BORDER_STRONG, text_color=C.TEXT,
        dropdown_fg_color=C.CARD, dropdown_text_color=C.TEXT,
        dropdown_hover_color=C.SELECTED)


def checkbox(master, text):
    return ctk.CTkCheckBox(
        master, text=text, font=font(13), text_color=C.TEXT, corner_radius=5,
        checkbox_width=20, checkbox_height=20, fg_color=C.ACCENT,
        hover_color=C.ACCENT_HOVER, border_color=C.BORDER_STRONG)


def textbox(master, mono=False, **kw):
    return ctk.CTkTextbox(
        master, corner_radius=8, border_width=1, border_color=C.BORDER,
        fg_color=C.INPUT, text_color=C.TEXT,
        scrollbar_button_color=C.BORDER_STRONG,
        scrollbar_button_hover_color=C.TEXT_MUTED,
        font=mono_font(12) if mono else font(12), **kw)


def card(master):
    return ctk.CTkFrame(master, fg_color=C.CARD, corner_radius=12,
                        border_width=1, border_color=C.BORDER)


def scroll_area(master):
    return ctk.CTkScrollableFrame(
        master, fg_color="transparent",
        scrollbar_button_color=C.BORDER_STRONG,
        scrollbar_button_hover_color=C.TEXT_MUTED)


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------
def title_label(master, text, size=24):
    return ctk.CTkLabel(master, text=text, font=font(size, "bold"),
                        text_color=C.TEXT, anchor="w")


def section_title(master, text):
    return ctk.CTkLabel(master, text=text, font=font(16, "bold"),
                        text_color=C.TEXT, anchor="w")


def field_label(master, text):
    return ctk.CTkLabel(master, text=text, font=font(13, "bold"),
                        text_color=C.TEXT, anchor="w")


def auto_wrap(label, container, padding=48, minimum=240):
    """Keep a label's wraplength in step with its container (no clipped text)."""
    state = {"w": None}

    def _on_configure(event):
        w = max(minimum, event.width - padding)
        if w != state["w"]:
            state["w"] = w
            label.configure(wraplength=w)

    container.bind("<Configure>", _on_configure, add="+")


def muted_label(master, text, wrap_in=None, padding=48, size=13):
    lbl = ctk.CTkLabel(master, text=text, font=font(size), text_color=C.TEXT_MUTED,
                       anchor="w", justify="left", wraplength=560)
    if wrap_in is not None:
        auto_wrap(lbl, wrap_in, padding)
    return lbl


def status_label(master, text="", kind="muted", icon_name=None):
    # CTkLabel puts no gap between image and text, so pad with spaces.
    return ctk.CTkLabel(
        master, text=("  " + text) if (icon_name and text) else text,
        font=font(13), anchor="w", justify="left",
        text_color=STATUS_COLORS[kind], compound="left",
        image=icon(icon_name, 16, STATUS_COLORS[kind]) if icon_name else None)


def set_status(label, text, kind="muted", icon_name=None):
    opts = dict(text=("  " + text) if icon_name else text, text_color=STATUS_COLORS[kind])
    if icon_name:
        opts["image"] = icon(icon_name, 16, STATUS_COLORS[kind])
    label.configure(**opts)

import ctypes
from pathlib import Path
from utils import log_message as log

HWND_BROADCAST = 0xFFFF
WM_FONTCHANGE = 0x001D


def _broadcast_font_change() -> None:
    ctypes.WinDLL("user32.dll").SendMessageW(HWND_BROADCAST, WM_FONTCHANGE, 0, 0)


def load(font_path: Path) -> bool:
    """Loads a custom font into the system font table for the current user session."""
    if not font_path.exists():
        log("Font file missing: {}", font_path)
        return False

    try:
        gdi32 = ctypes.WinDLL("gdi32.dll")
        if gdi32.AddFontResourceW(str(font_path)) > 0:
            _broadcast_font_change()
            log("Successfully injected session font: {}", font_path.name)
            return True
    except Exception as e:
        log("Failed to inject session font: {}", e)
    return False


def unload(font_path: Path) -> None:
    """Cleans up the loaded session font from system memory on exit."""
    try:
        gdi32 = ctypes.WinDLL("gdi32.dll")
        gdi32.RemoveFontResourceW(str(font_path))
        _broadcast_font_change()
        log("Successfully cleaned up session font: {}", font_path.name)
    except Exception as e:
        log("Failed to unload session font: {}", e)

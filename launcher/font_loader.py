import config
from utils import log_message as log
import ctypes


def load(font_path: config.Path) -> bool:
    """Loads a custom font into the system font table for the current user session."""
    if not font_path.exists():
        log("Font file missing: {}", font_path)
        return False

    try:
        gdi32 = ctypes.WinDLL("gdi32.dll")
        result = gdi32.AddFontResourceW(str(font_path))
        if result > 0:
            HWND_BROADCAST = 0xFFFF
            WM_FONTCHANGE = 0x001D
            ctypes.WinDLL("user32.dll").SendMessageW(
                HWND_BROADCAST, WM_FONTCHANGE, 0, 0
            )
            log("Successfully injected session font: {}", font_path.name)
            return True
    except Exception as e:
        log("Failed to inject session font: {}", e)
    return False


def unload(font_path: config.Path, regvapor_dir: config.Path):
    """Cleans up the loaded session font from system memory on exit."""
    try:
        gdi32 = ctypes.WinDLL("gdi32.dll")
        gdi32.RemoveFontResourceW(str(font_path))
        HWND_BROADCAST = 0xFFFF
        WM_FONTCHANGE = 0x001D
        ctypes.WinDLL("user32.dll").SendMessageW(HWND_BROADCAST, WM_FONTCHANGE, 0, 0)
        log("Successfully cleaned up session font: {}", font_path.name)
    except Exception as e:
        log("Failed to unload session font: {}", e)

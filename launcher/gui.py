import ctypes
from ctypes import wintypes

# Made with the help of Gemini

# Windows API Constants & Type Definitions for Raw UI Drawing
GWL_USERDATA = -21
WM_INITDIALOG = 0x0110
WM_COMMAND = 0x0111
CB_ADDSTRING = 0x0143
CB_SETCURSEL = 0x014E
CB_GETCURSEL = 0x0147
CB_GETLBTEXT = 0x0148
CBS_DROPDOWNLIST = 0x0003
WS_CHILD = 0x40000000
WS_VISIBLE = 0x10000000
WS_TABSTOP = 0x00010000

# Using ctypes to prevent Windowmanager issuess with games like Guilty The Sin
WndProcType = ctypes.WINFUNCTYPE(
    ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
)


class DLGTEMPLATE(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.DWORD),
        ("dwExtendedStyle", wintypes.DWORD),
        ("cdit", wintypes.WORD),
        ("x", wintypes.SHORT),
        ("y", wintypes.SHORT),
        ("cx", wintypes.SHORT),
        ("cy", wintypes.SHORT),
    ]


def select_game_id_gui(available_ids: list) -> str | None:
    user32 = ctypes.windll.user32  # noqa: F841
    gdi32 = ctypes.windll.gdi32  # noqa: F841
    chosen_id = [None]

    @WndProcType
    def dialog_proc(hwnd, msg, wparam, lparam):
        if msg == WM_INITDIALOG:
            user32.SetWindowTextW(hwnd, "RegVapor - Select Configuration")

            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            screen_width = user32.GetSystemMetrics(0)
            screen_height = user32.GetSystemMetrics(1)
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            user32.MoveWindow(
                hwnd,
                (screen_width - width) // 2,
                (screen_height - height) // 2,
                width,
                height,
                True,
            )

            h_font = gdi32.CreateFontW(
                15, 0, 0, 0, 400, False, False, False, 1, 0, 0, 0, 0, "Segoe UI"
            )

            label_text = "No local configuration profile found.\nSelect a configuration from the profile list:"
            h_label = user32.CreateWindowExW(
                0,
                "Static",
                label_text,
                WS_CHILD | WS_VISIBLE,
                15,
                12,
                250,
                30,
                hwnd,
                100,
                0,
                0,
            )
            user32.SendMessageW(h_label, 0x0030, h_font, 1)

            h_combo = user32.CreateWindowExW(
                0,
                "ComboBox",
                "",
                WS_CHILD | WS_VISIBLE | WS_TABSTOP | CBS_DROPDOWNLIST,
                15,
                48,
                250,
                200,
                hwnd,
                101,
                0,
                0,
            )
            user32.SendMessageW(h_combo, 0x0030, h_font, 1)

            for game_id in available_ids:
                user32.SendMessageW(h_combo, CB_ADDSTRING, 0, game_id)
            user32.SendMessageW(h_combo, CB_SETCURSEL, 0, 0)

            h_button = user32.CreateWindowExW(
                0,
                "Button",
                "Confirm & Save",
                WS_CHILD | WS_VISIBLE | WS_TABSTOP,
                90,
                85,
                100,
                26,
                hwnd,
                1,
                0,
                0,
            )
            user32.SendMessageW(h_button, 0x0030, h_font, 1)

            user32.SetFocus(h_combo)
            return 0

        elif msg == WM_COMMAND:
            loword_wparam = wparam & 0xFFFF
            if loword_wparam == 1:
                h_combo = user32.GetDlgItem(hwnd, 101)
                idx = user32.SendMessageW(h_combo, CB_GETCURSEL, 0, 0)
                if idx != -1:
                    length = user32.SendMessageW(h_combo, 0x0149, idx, 0)
                    buffer = ctypes.create_unicode_buffer(length + 1)
                    user32.SendMessageW(
                        h_combo, CB_GETLBTEXT, idx, ctypes.byref(buffer)
                    )
                    chosen_id[0] = buffer.value
                user32.EndDialog(hwnd, 1)
                return 1
            elif loword_wparam == 2:
                user32.EndDialog(hwnd, 0)
                return 1
        return 0

    dialog_template = DLGTEMPLATE(
        style=0x10C800C4, dwExtendedStyle=0, cdit=0, x=0, y=0, cx=210, cy=100
    )

    user32.DialogBoxIndirectParamW(0, ctypes.byref(dialog_template), 0, dialog_proc, 0)
    return chosen_id[0]


def show_error_message(message: str):
    user32 = ctypes.windll.user32
    user32.MessageBoxW(0, message, "RegVapor Launcher - Error", 0x10 | 0x0)


def show_info_message(message: str, title: str = "RegVapor Launcher - Info"):
    user32 = ctypes.windll.user32  # noqa: F841
    ans = ctypes.windll.user32.MessageBoxW(0, message, title, 0x04 | 0x40)
    return ans == 6

import os
import sys
import json
import time
import ctypes
from ctypes import wintypes
import winreg
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path

# ==============================================================================
# BASE CONFIGURATION
# ==============================================================================
__version__ = "0.6.0"
GITHUB_JSON_URL = "https://raw.githubusercontent.com/Saetron/RegVapor/refs/heads/main/game_registry.json"
GITHUB_EXE_URL = "https://github.com/Saetron/RegVapor/releases/latest/download/RegVapor.exe"

LOCAL_JSON_NAME = "RegVapor_game.json"
ID_FILE_NAME = "game_id.txt"
BACKUP_DIR_NAME = "registry"
LOGFILE = "RegVapor.log"
# ==============================================================================

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

# Using c_ssize_t to prevent Windowmanager issuess with games like Guilty The Sin
# select_game_id_gui and DLGTEMPLATE are created entirely with Gemini, as I have no clue about the Windows API. I just know it works and is stable enough for this purpose.
WndProcType = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

class DLGTEMPLATE(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.DWORD),
        ("dwExtendedStyle", wintypes.DWORD),
        ("cdit", wintypes.WORD),
        ("x", wintypes.SHORT),
        ("y", wintypes.SHORT),
        ("cx", wintypes.SHORT),
        ("cy", wintypes.SHORT)
    ]

def select_game_id_gui(available_ids: list) -> str | None:
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
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
            user32.MoveWindow(hwnd, (screen_width - width) // 2, (screen_height - height) // 2, width, height, True)

            h_font = gdi32.CreateFontW(15, 0, 0, 0, 400, False, False, False, 1, 0, 0, 0, 0, "Segoe UI")

            label_text = "No local configuration profile found.\nSelect a configuration from the profile list:"
            h_label = user32.CreateWindowExW(0, "Static", label_text, WS_CHILD | WS_VISIBLE, 15, 12, 250, 30, hwnd, 100, 0, 0)
            user32.SendMessageW(h_label, 0x0030, h_font, 1)

            h_combo = user32.CreateWindowExW(0, "ComboBox", "", WS_CHILD | WS_VISIBLE | WS_TABSTOP | CBS_DROPDOWNLIST, 15, 48, 250, 200, hwnd, 101, 0, 0)
            user32.SendMessageW(h_combo, 0x0030, h_font, 1)

            for game_id in available_ids:
                user32.SendMessageW(h_combo, CB_ADDSTRING, 0, game_id)
            user32.SendMessageW(h_combo, CB_SETCURSEL, 0, 0)

            h_button = user32.CreateWindowExW(0, "Button", "Confirm & Save", WS_CHILD | WS_VISIBLE | WS_TABSTOP, 90, 85, 100, 26, hwnd, 1, 0, 0)
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
                    user32.SendMessageW(h_combo, CB_GETLBTEXT, idx, ctypes.byref(buffer))
                    chosen_id[0] = buffer.value
                user32.EndDialog(hwnd, 1)
                return 1
            elif loword_wparam == 2:
                user32.EndDialog(hwnd, 0)
                return 1
        return 0

    dialog_template = DLGTEMPLATE(
        style=0x10C800C4,
        dwExtendedStyle=0,
        cdit=0,
        x=0, y=0, cx=210, cy=100
    )

    user32.DialogBoxIndirectParamW(0, ctypes.byref(dialog_template), 0, dialog_proc, 0)
    return chosen_id[0]



# ==============================================================================

# Log function, makes my life easier and doesnt clutter the code for every log entry
def log_message(message: str, *args, max_lines=100, base_dir):
    formatted_message = message.format(*args) if args else message
    logfile_path = base_dir / LOGFILE
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(logfile_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {formatted_message}\n")
    
    if os.path.exists(logfile_path):
        with open(logfile_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) > max_lines:
            with open(logfile_path, "w", encoding="utf-8") as f:
                f.writelines(lines[-max_lines:])

def read_saved_game_id(base_dir: Path) -> str | None:
    """Checks if a game_id.txt exists and returns its contents if valid."""
    id_file = base_dir / ID_FILE_NAME
    if id_file.exists():
        with open(id_file, "r", encoding="utf-8") as f:
            current_id = f.read().strip()
        if current_id and current_id != "ENTER_GAME_ID_HERE":
            return current_id
    return None

def fetch_and_cache_config(base_dir: Path, target_game_id: str | None) -> dict:
    """
    Attempts to fetch the database from GitHub. 
    - If target_game_id is known, caches ONLY that game's data to RegVapor_game.json.
    - If target_game_id is unknown (first run), returns the full database so the user can choose.
    - If offline, falls back to the local RegVapor_game.json.
    """
    local_json_path = base_dir / LOCAL_JSON_NAME
    
    # Trying to read the game_registry from GitHub first
    try:
        with urllib.request.urlopen(GITHUB_JSON_URL, timeout=5) as response:
            full_data = json.loads(response.read().decode())
            
            if target_game_id:
                if target_game_id in full_data:
                    # Filter to current game_id to save storage and allow offline fallback
                    filtered_data = {target_game_id: full_data[target_game_id]}
                    with open(local_json_path, "w", encoding="utf-8") as f:
                        json.dump(filtered_data, f, indent=4)
                    return filtered_data
                else:
                    # If ID doesnt exist in the fetched data, return full_data for GUI selection, avoids silent failure when remote data changes
                    return full_data
            else:
                return full_data
    except Exception as e:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with open(logfile_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] Network offline or GitHub unreachable ({e}).\n")
        
    # Offline fallback logic
    if local_json_path.exists():
        try:
            with open(local_json_path, "r", encoding="utf-8") as f:
                local_data = json.load(f)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            with open(logfile_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] Loaded cached fallback configuration from: {LOCAL_JSON_NAME}\n")
            return local_data
        except Exception as e:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            with open(logfile_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] Failed to read local fallback {LOCAL_JSON_NAME}: {e}\n")
            
    return {}

def check_for_updates(master_config: dict):
    """Checks for updates and notifies the user with a download link."""
    remote_version = master_config.get("__metadata__", {}).get("latest_launcher_version")
    if not remote_version:
        return

    # Simple semantic patch comparison
    def parse_ver(v_str):
        return [int(x) for x in v_str.split(".")]

    try:
        if parse_ver(remote_version) <= parse_ver(__version__):
            return
    except Exception:
        return

    # Notify user without auto-updating
    msg = (f"A new version of RegVapor is available (v{remote_version}).\n\n"
           f"Please download the update here:\n{GITHUB_EXE_URL.replace('/latest/download/', '/releases/latest')}\n\n"
           "Would you like to open the release page now?")
    
    # MB_YESNO | MB_ICONINFORMATION
    ans = ctypes.windll.user32.MessageBoxW(0, msg, "RegVapor Update Available", 0x04 | 0x40)
    
    if ans == 6: # IDYES
        os.startfile(GITHUB_EXE_URL.replace('/latest/download/', '/releases/latest'))

def load_session_font(font_path: Path) -> bool:
    """Loads a custom font into the system font table for the current user session."""
    if not font_path.exists():
        print(f"Font file missing: {font_path.name}")
        return False

    try:
        gdi32 = ctypes.WinDLL('gdi32.dll')
        result = gdi32.AddFontResourceW(str(font_path))
        if result > 0:
            HWND_BROADCAST = 0xFFFF
            WM_FONTCHANGE = 0x001D
            ctypes.WinDLL('user32.dll').SendMessageW(HWND_BROADCAST, WM_FONTCHANGE, 0, 0)
            print(f"Successfully injected session font: {font_path.name}")
            return True
    except Exception as e:
        print(f"Failed to inject session font: {e}")
    return False

def unload_session_font(font_path: Path):
    """Cleans up the loaded session font from system memory on exit."""
    try:
        gdi32 = ctypes.WinDLL('gdi32.dll')
        gdi32.RemoveFontResourceW(str(font_path))
        HWND_BROADCAST = 0xFFFF
        WM_FONTCHANGE = 0x001D
        ctypes.WinDLL('user32.dll').SendMessageW(HWND_BROADCAST, WM_FONTCHANGE, 0, 0)
        print(f"Successfully cleaned up session font: {font_path.name}")
    except Exception as e:
        print(f"Failed to unload session font: {e}")

def handle_file_backups(base_dir: Path, files_list: list) -> list:
    """Renames specific game files to .bak before launching. Returns a list of renamed pairs."""
    processed_backups = []
    for rel_path in files_list:
        target_file = (base_dir / rel_path).resolve()
        if target_file.exists() and target_file.is_file():
            bak_file = target_file.with_suffix(target_file.suffix + ".bak")
            try:
                if bak_file.exists():
                    bak_file.unlink()
                target_file.rename(bak_file)
                processed_backups.append((target_file, bak_file))
                print(f"Temporarily backed up: {rel_path} -> {bak_file.name}")
            except Exception as e:
                print(f"Failed to backup file {rel_path}: {e}")
    return processed_backups

def restore_file_backups(backups: list):
    """Restores the original filenames from their .bak counterparts on exit."""
    for original_file, bak_file in backups:
        if bak_file.exists():
            try:
                if original_file.exists():
                    original_file.unlink()
                bak_file.rename(original_file)
                print(f"Restored file layout: {original_file.name}")
            except Exception as e:
                print(f"Failed to restore file {bak_file.name}: {e}")

def delete_registry_key_tree(root, subkey):
    """Recursively purges a registry branch completely from Windows."""
    try:
        key = winreg.OpenKey(root, subkey, 0, winreg.KEY_ALL_ACCESS)
    except FileNotFoundError:
        return
    try:
        while True:
            child = winreg.EnumKey(key, 0)
            delete_registry_key_tree(key, child)
    except OSError:
        pass
    winreg.CloseKey(key)
    winreg.DeleteKey(root, subkey)

def set_registry_keys(game_dir: Path, backup_dir: Path, config: dict):
    """Injects saved local states or default layouts, matching active path states."""
    key_path = config["key_path"]
    registry_data = config["registry_data"]
    
    if not key_path:
        return

    key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)

    for value_name, (type_str, default_val) in registry_data.items():
        if type_str == "REG_BINARY":
            data_type = winreg.REG_BINARY
            fallback_bytes = bytes.fromhex(str(default_val).replace(" ", ""))
        elif type_str == "REG_DWORD":
            data_type = winreg.REG_DWORD
            fallback_bytes = int(str(default_val).strip())
        else:
            data_type = winreg.REG_SZ
            fallback_bytes = str(default_val)

        is_path_key = "{install_dir}" in str(default_val) or "{install_src}" in str(default_val) or str(default_val) == ".\\"

        backup_file = backup_dir / f"{value_name}.regdata"
        if backup_file.exists() and not is_path_key:
            try:
                if data_type == winreg.REG_BINARY:
                    prepared_value = backup_file.read_bytes()
                elif data_type == winreg.REG_DWORD:
                    prepared_value = int(backup_file.read_text(encoding="utf-8").strip())
                else:
                    prepared_value = backup_file.read_text(encoding="utf-8")
            except Exception:
                prepared_value = fallback_bytes
        else:
            if "{install_dir}" in str(default_val):
                prepared_value = str(default_val).replace("{install_dir}", str(game_dir))
            elif "{install_src}" in str(default_val):
                prepared_value = str(default_val).replace("{install_src}", str(game_dir.parent))
            else:
                prepared_value = fallback_bytes

        winreg.SetValueEx(key, value_name, 0, data_type, prepared_value)

    winreg.CloseKey(key)

def backup_and_clean_registry(key_path: str, backup_dir: Path):
    """Harvests user adjustments into files and deletes the Windows keys completely."""
    if not key_path:
        return

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
    except FileNotFoundError:
        return

    try:
        index = 0
        while True:
            value_name, value_data, data_type = winreg.EnumValue(key, index)
            backup_file = backup_dir / f"{value_name}.regdata"
            
            if data_type == winreg.REG_BINARY:
                backup_file.write_bytes(value_data)
            elif data_type == winreg.REG_DWORD:
                backup_file.write_text(str(value_data), encoding="utf-8")
            else:
                backup_file.write_text(str(value_data), encoding="utf-8")
                
            index += 1
    except OSError:
        pass
    finally:
        winreg.CloseKey(key)

    delete_registry_key_tree(winreg.HKEY_CURRENT_USER, key_path)

def main():
    base_dir = Path(sys.argv[0]).resolve().parent
    portable_profile = base_dir / "PortableProfile"
    #local_appdata = portable_profile / "AppData" / "Local"
    #roaming_appdata = portable_profile / "AppData" / "Roaming"
    backup_dir = portable_profile / BACKUP_DIR_NAME
    
    #os.makedirs(str(local_appdata), exist_ok=True)
    #os.makedirs(str(roaming_appdata), exist_ok=True)
    os.makedirs(str(backup_dir), exist_ok=True)
    
    #env = os.environ.copy()
    #env["USERPROFILE"] = str(portable_profile)
    #env["LOCALAPPDATA"] = str(local_appdata)
    #env["APPDATA"] = str(roaming_appdata)


    # 1. Read existing configuration profile id if already set
    game_id = read_saved_game_id(base_dir)

    # 2. Grab the relevant configuration dataset
    master_config = fetch_and_cache_config(base_dir, game_id)

    # 3. Securely check for and run application updater logic
    if master_config:
        check_for_updates(master_config)

    # 4. If missing or unconfigured profile id, launch GUI fallback 
    if not game_id or game_id == "ENTER_GAME_ID_HERE":
        if not master_config:
            ctypes.windll.user32.MessageBoxW(
                0,
                "Could not fetch configuration database (online or offline fallback), and no local configuration file exists.",
                "RegVapor Launcher - Error",
                0x10 | 0x0
            )
            return

        available_ids = sorted([k for k in master_config.keys() if k != "__metadata__"])
        game_id = select_game_id_gui(available_ids)

        if game_id:
            # Save the text identifier locally
            id_file = base_dir / ID_FILE_NAME
            with open(id_file, "w", encoding="utf-8") as f:
                f.write(game_id)
            
            # Now cache ONLY the chosen configuration details to disk
            if game_id in master_config:
                filtered_data = {game_id: master_config[game_id]}
                local_json_path = base_dir / LOCAL_JSON_NAME
                try:
                    with open(local_json_path, "w", encoding="utf-8") as f:
                        json.dump(filtered_data, f, indent=4)
                    master_config = filtered_data
                    print(f"Cached configuration for '{game_id}' locally to {LOCAL_JSON_NAME}.")
                except Exception as e:
                    print(f"Failed to write local backup cache: {e}")
            time.sleep(0.2)
        else:
            return

    print(f"RegVapor Launcher v{__version__} initializing for ID: {game_id}")
    
    if not master_config or game_id not in master_config:
        print(f"Error: Configurations for '{game_id}' not found.")
        return

    config = master_config[game_id]
    key_path = config.get("key_path", "")
    
    game_exe_setting = config["game_exe"]
    exe_candidates = [game_exe_setting] if isinstance(game_exe_setting, str) else game_exe_setting
    
    game_exe = None
    for candidate in exe_candidates:
        target_path = base_dir / candidate
        if target_path.exists():
            game_exe = target_path
            break

    if not game_exe:
        print(f"Executable missing. Looked for: {exe_candidates} inside {base_dir}")
        return

    font_loaded = False
    font_path = None
    font_filename = config.get("custom_font")
    if font_filename:
        font_path = base_dir / font_filename
        font_loaded = load_session_font(font_path)

    active_backups = []
    backup_files_list = config.get("backup_files", [])
    if backup_files_list and isinstance(backup_files_list, list):
        active_backups = handle_file_backups(base_dir, backup_files_list)

    try:
        set_registry_keys(base_dir, backup_dir, config)
    except Exception as e:
        print(f"Failed setting registry parameters: {e}")

    try:
        subprocess.run([str(game_exe)], cwd=str(base_dir))
    except Exception as e:
        print(f"Engine failed to run execution loops: {e}")
    finally:
        try:
            backup_and_clean_registry(key_path, backup_dir)
        except Exception as e:
            print(f"Scrub and backup failure: {e}")
        
        if active_backups:
            restore_file_backups(active_backups)
        
        if font_loaded and font_path:
            unload_session_font(font_path)

if __name__ == "__main__":
    main()
import os
import sys
import json
import ctypes
import winreg
import subprocess
import urllib.request
from pathlib import Path

# ==============================================================================
# BASE CONFIGURATION
# ==============================================================================
__version__ = "0.3.0"
GITHUB_JSON_URL = "https://raw.githubusercontent.com/Saetron/RegVapor/refs/heads/main/game_registry.json"
ID_FILE_NAME = "game_id.txt"
BACKUP_DIR_NAME = "registry"
# ==============================================================================

def select_game_id_gui(available_ids: list) -> str | None:
    """Invokes a native Windows selection dropdown using a lightweight PowerShell script wrapper."""
    choices_array = ",".join([f"'{uid}'" for uid in available_ids])
    
    ps_script = f"""
    Add-Type -AssemblyName System.Windows.Forms
    Add-Type -AssemblyName System.Drawing

    $form = New-Object System.Windows.Forms.Form
    $form.Text = "RegVapor - Select Configuration"
    $form.Size = New-Object System.Drawing.Size(420,180)
    $form.StartPosition = "CenterScreen"
    $form.FormBorderStyle = "FixedDialog"
    $form.MaximizeBox = $false
    $form.MinimizeBox = $false
    $form.TopMost = $true

    $label = New-Object System.Windows.Forms.Label
    $label.Location = New-Object System.Drawing.Point(20,15)
    $label.Size = New-Object System.Drawing.Size(360,35)
    $label.Text = "No local configuration profile found.`nSelect a configuration from the remote master index:"
    $label.Font = New-Object System.Drawing.Font("Segoe UI", 9)
    $form.Controls.Add($label)

    $comboBox = New-Object System.Windows.Forms.ComboBox
    $comboBox.Location = New-Object System.Drawing.Point(20,55)
    $comboBox.Size = New-Object System.Drawing.Size(360,25)
    $comboBox.DropDownStyle = [System.Windows.Forms.ComboBoxStyle]::DropDownList
    
    $choices = @({choices_array})
    foreach ($choice in $choices) {{ [void]$comboBox.Items.Add($choice) }}
    if ($comboBox.Items.Count -gt 0) {{ $comboBox.SelectedIndex = 0 }}
    $form.Controls.Add($comboBox)

    $button = New-Object System.Windows.Forms.Button
    $button.Location = New-Object System.Drawing.Point(150,95)
    $button.Size = New-Object System.Drawing.Size(120,30)
    $button.Text = "Confirm & Save"
    $button.DialogResult = [System.Windows.Forms.DialogResult]::OK
    $form.AcceptButton = $button
    $form.Controls.Add($button)

    $result = $form.ShowDialog()
    if ($result -eq [System.Windows.Forms.DialogResult]::OK) {{
        Write-Output $comboBox.SelectedItem
    }}
    """
    try:
        process = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        output = process.stdout.strip()
        return output if output in available_ids else None
    except Exception:
        return None

def get_game_id(base_dir: Path, master_config: dict) -> str | None:
    """Reads the game identifier string or prompts user to select one via native GUI if missing."""
    id_file = base_dir / ID_FILE_NAME
    
    if id_file.exists():
        with open(id_file, "r", encoding="utf-8") as f:
            current_id = f.read().strip()
        if current_id and current_id != "ENTER_GAME_ID_HERE":
            return current_id

    if not master_config:
        ctypes.windll.user32.MessageBoxW(
            0,
            "Could not fetch remote configuration database, and no local configuration file exists.",
            "RegVapor Launcher - Connection Error",
            0x10 | 0x0
        )
        return None

    available_ids = sorted(list(master_config.keys()))
    chosen_id = select_game_id_gui(available_ids)

    if chosen_id:
        with open(id_file, "w", encoding="utf-8") as f:
            f.write(chosen_id)
        return chosen_id
        
    return None

def fetch_remote_config() -> dict:
    """Fetches the unified database directly from the GitHub repository."""
    try:
        with urllib.request.urlopen(GITHUB_JSON_URL, timeout=5) as response:
            return json.loads(response.read().decode())
    except Exception:
        return {}

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
    
    key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)

    for value_name, (type_str, default_val) in registry_data.items():
        if type_str == "REG_BINARY":
            data_type = winreg.REG_BINARY
            fallback_bytes = bytes.fromhex(default_val.replace(" ", ""))
        elif type_str == "REG_DWORD":
            data_type = winreg.REG_DWORD
            fallback_bytes = int(default_val)
        else:
            data_type = winreg.REG_SZ
            fallback_bytes = str(default_val)

        # UPDATED: Checks if the string contains a token or matches the relative dot-slash path
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
            # UPDATED: Replaces strict matching with the flexible string replacement logic
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
    local_appdata = portable_profile / "AppData" / "Local"
    roaming_appdata = portable_profile / "AppData" / "Roaming"
    backup_dir = portable_profile / BACKUP_DIR_NAME
    
    os.makedirs(str(local_appdata), exist_ok=True)
    os.makedirs(str(roaming_appdata), exist_ok=True)
    os.makedirs(str(backup_dir), exist_ok=True)
    
    env = os.environ.copy()
    env["USERPROFILE"] = str(portable_profile)
    env["LOCALAPPDATA"] = str(local_appdata)
    env["APPDATA"] = str(roaming_appdata)

    master_config = fetch_remote_config()

    game_id = get_game_id(base_dir, master_config)
    if not game_id:
        return
        
    print(f"RegVapor Launcher v{__version__} initializing for ID: {game_id}")
    
    if not master_config or game_id not in master_config:
        print(f"Error: Configurations for '{game_id}' not found on remote storage target.")
        return

    config = master_config[game_id]
    key_path = config["key_path"]
    
    # --- MULTI-EXECUTABLE RESOLUTION LOGIC ---
    exe_setting = config["game_exe"]
    # Handle single string format transparently by wrapping it into an array list
    exe_candidates = [exe_setting] if isinstance(exe_setting, str) else exe_setting
    
    game_exe = None
    for exe_name in exe_candidates:
        test_path = base_dir / exe_name
        if test_path.exists():
            game_exe = test_path
            print(f"Target executable found: {exe_name}")
            break

    if not game_exe:
        print(f"Error: Executable file missing. Checked candidates: {', '.join(exe_candidates)}")
        return
    # ------------------------------------------

    # --- OPTIONAL FONT LAUNCHER INTEGRATION ---
    font_loaded = False
    font_path = None  
    font_filename = config.get("custom_font")
    
    if font_filename:
        font_path = base_dir / font_filename
        font_loaded = load_session_font(font_path)

    # Inject Values into Registry
    try:
        set_registry_keys(base_dir, backup_dir, config)
    except Exception as e:
        print(f"Failed setting registry parameters: {e}")

    # Launch Game
    try:
        subprocess.run([str(game_exe)], env=env, cwd=str(base_dir))
    except Exception as e:
        print(f"Engine failed to run execution loops: {e}")
    finally:
        # Scrub and backup registry changes
        try:
            backup_and_clean_registry(key_path, backup_dir)
        except Exception as e:
            print(f"Scrub and backup failure: {e}")
        
        # Unload font cleanly on exit if one was successfully injected
        if font_loaded and font_path:
            unload_session_font(font_path)

if __name__ == "__main__":
    main()
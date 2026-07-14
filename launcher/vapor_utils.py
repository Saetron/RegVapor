import sys
import config
import ctypes
import json
import subprocess
import urllib.request
from utils import log_message as log

def check_for_updates(master_config: dict):
    """Checks for updates and notifies the user with a download link."""
    remote_version = master_config.get("__metadata__", {}).get("latest_launcher_version")
    if not remote_version:
        log("Update check failed: No remote version found.")
        return

    def parse_ver(v_str):
        clean_v = ''.join(c for c in v_str if c.isdigit() or c == '.')
        return [int(x) for x in clean_v.split(".")]

    try:
        remote_parsed = parse_ver(remote_version)
        local_parsed = parse_ver(config.__version__)
        log("Checking updates: Remote v{}, Local v{}", remote_version, config.__version__)
        if remote_parsed <= local_parsed:
            return
    except Exception as e:
        log("Update check parsing error: {}", e)
        return

    msg = (f"A new version of RegVapor is available (v{remote_version}).\n\n"
           "Would you like to update now? (This will download the latest version and restart the launcher.)")
    
    ans = ctypes.windll.user32.MessageBoxW(0, msg, "RegVapor Update Available", 0x04 | 0x40)
    
    if ans == 6:
        target_exe = sys.argv[0]
        updater_exe = config.base_dir / "RegVapor_updater.exe"
        urllib.request.urlretrieve(config.GITHUB_UPDATER_URL, updater_exe)
        subprocess.Popen([str(updater_exe), target_exe, str(config.base_dir)], shell=False)
        sys.exit()

def read_saved_game_id() -> str | None:
    """Checks if a game_id.txt exists and returns its contents if valid."""
    if config.id_file.exists():
        with open(config.id_file, "r", encoding="utf-8") as f:
            current_id = f.read().strip()
        if current_id and current_id != "ENTER_GAME_ID_HERE":
            return current_id
    return None

def fetch_and_cache_config(target_game_id: str | None) -> dict:
    """
    Attempts to fetch the database from GitHub. 
    - If target_game_id is known, caches ONLY that game's data to RegVapor_game.json.
    - If target_game_id is unknown (first run), returns the full database so the user can choose.
    - If offline, falls back to the local RegVapor_game.json.
    """
   
    # Trying to read the game_registry from GitHub first
    try:
        with urllib.request.urlopen(config.GITHUB_JSON_URL, timeout=5) as response:
            full_data = json.loads(response.read().decode())
            
            if target_game_id:
                if target_game_id in full_data:
                    # Filter to current game_id to save storage and allow offline fallback
                    filtered_data = {target_game_id: full_data[target_game_id]}
                    with open(config.local_json_path, "w", encoding="utf-8") as f:
                        json.dump(filtered_data, f, indent=4)
                    return filtered_data
                else:
                    # If ID doesnt exist in the fetched data, return full_data for GUI selection, avoids silent failure when remote data changes
                    return full_data
            else:
                return full_data
    except Exception as e:
        log("Network offline or GitHub unreachable ({})", e)
        
    # Offline fallback logic
    if config.local_json_path.exists():
        try:
            with open(config.local_json_path, "r", encoding="utf-8") as f:
                local_data = json.load(f)
            log("Loaded cached fallback configuration from: {}", config.LOCAL_JSON_NAME)
            return local_data
        except Exception as e:
            log("Failed to read local fallback {}: {}", config.LOCAL_JSON_NAME, e)
            
    return {}
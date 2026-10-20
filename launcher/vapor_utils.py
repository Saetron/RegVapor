import json
import subprocess
import sys
import urllib.request
import config
import gui
from utils import log_message as log


def _parse_version(v_str: str) -> list[int]:
    clean_v = "".join(c for c in v_str if c.isdigit() or c == ".")
    return [int(x) for x in clean_v.split(".") if x]


def check_for_updates(master_config: dict) -> None:
    remote_version = master_config.get("__metadata__", {}).get(
        "latest_launcher_version"
    )
    if not remote_version:
        log("Update check failed: No remote version found.")
        return

    try:
        remote_parsed = _parse_version(remote_version)
        local_parsed = _parse_version(config.__version__)
        log(
            "Checking updates: Remote v{}, Local v{}",
            remote_version,
            config.__version__,
        )
        if remote_parsed <= local_parsed:
            return
    except Exception as e:
        log("Update check parsing error: {}", e)
        return

    msg = (
        f"A new version of RegVapor is available (v{remote_version}).\n\n"
        "Would you like to update now? (This will download the latest version and restart the launcher.)"
    )

    if gui.show_info_message(msg, title="RegVapor Launcher - Update Available"):
        target_exe = sys.argv[0]
        updater_exe = config.base_dir / "RegVapor_updater.exe"
        try:
            urllib.request.urlretrieve(config.GITHUB_UPDATER_URL, updater_exe)
            subprocess.Popen(
                [str(updater_exe), target_exe, str(config.base_dir)], shell=False
            )
            sys.exit()
        except Exception as e:
            log("Failed to download or start updater: {}", e)


def read_saved_game_id() -> str | None:
    """Checks if a game_id.txt exists and returns its contents if valid."""
    if config.id_file.exists():
        current_id = config.id_file.read_text(encoding="utf-8").strip()
        if current_id and current_id != "ENTER_GAME_ID_HERE":
            return current_id
    return None


def fetch_and_cache_config(target_game_id: str | None, master_config: dict) -> dict:
    """
    Resolves the game configuration database.
    - If master_config was fetched from GitHub and target_game_id is known, caches ONLY that game's data to RegVapor_game.json.
    - If master_config was fetched and target_game_id is unknown (first run), returns the full database so the user can choose.
    - If offline (master_config is empty), falls back to the local RegVapor_game.json.
    """
    if master_config:
        if target_game_id and target_game_id in master_config:
            filtered_data = {target_game_id: master_config[target_game_id]}
            try:
                with open(config.local_json_path, "w", encoding="utf-8") as f:
                    json.dump(filtered_data, f, indent=4)
            except Exception as e:
                log("Failed to write local backup cache: {}", e)
            return filtered_data
        return master_config

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


def get_master_config() -> dict:
    try:
        with urllib.request.urlopen(config.GITHUB_JSON_URL, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        log("Network offline or GitHub unreachable ({})", e)
        return {}

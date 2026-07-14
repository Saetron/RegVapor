from pathlib import Path
import sys

# ==============================================================================
# BASE CONFIGURATION
# ==============================================================================
__version__ = "0.6.1"
GITHUB_JSON_URL = "https://raw.githubusercontent.com/Saetron/RegVapor/refs/heads/main/game_registry.json"
GITHUB_EXE_URL = "https://github.com/Saetron/RegVapor/releases/latest/download/RegVapor.exe"
GITHUB_UPDATER_URL = "https://github.com/Saetron/RegVapor/releases/latest/download/RegVapor_updater.exe"

REGVAPOR_DIR_NAME = "RegVapor"
LOCAL_JSON_NAME = "RegVapor_game.json"
ID_FILE_NAME = "game_id.txt"
BACKUP_DIR_NAME = "registry"
LOGFILE = "RegVapor.log"
# ==============================================================================

# Generate paths based on RegVapor's location
base_dir = Path(sys.argv[0]).resolve().parent
regvapor_dir = base_dir / REGVAPOR_DIR_NAME
backup_dir = regvapor_dir / BACKUP_DIR_NAME
local_json_path = regvapor_dir / LOCAL_JSON_NAME
id_file = regvapor_dir / ID_FILE_NAME
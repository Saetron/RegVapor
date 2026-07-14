import sys
import config
import ctypes
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
        updater_exe = config.regvapor_dir / "RegVapor_updater.exe"
        urllib.request.urlretrieve(config.GITHUB_UPDATER_URL, updater_exe)
        subprocess.Popen([str(updater_exe), target_exe], shell=False)
        sys.exit()

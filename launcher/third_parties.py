import ctypes
import urllib.request
import json
from utils import log_message as log
import os

# ==============================================================================
# BASE CONFIGURATION
# ==============================================================================
LAV_API_URL = "https://api.github.com/repos/Nevcairiel/LAVFilters/releases/latest"
# ==============================================================================


def download_lav():
    try:
        with urllib.request.urlopen(LAV_API_URL, timeout=5) as response:
            full_data = json.loads(response.read().decode())
            return full_data
    except Exception as e:
        log("Network offline or GitHub unreachable ({})", e)
        return {}

    assets = full_data.get("assets", [])
    installer_asset = next((a for a in assets if "Installer.exe" in a["name"]), None)

    if installer_asset:
        download_url = installer_asset["browser_download_url"]
        filename = installer_asset["name"]

        urllib.request.urlretrieve(download_url, filename)
        log("Downloaded LAV installer: {}", filename)
        installer_path = os.path.abspath(filename)
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", installer_path, "/VERYSILENT /SUPPRESSMSGBOXES", None, 1
        )
        return filename
    else:
        log("No installer found in the latest LAV release.")
        return None

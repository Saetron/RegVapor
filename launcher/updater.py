import os
from pathlib import Path
import shutil
import subprocess
import sys
import textwrap
import time
import urllib.request
import config
from utils import log_message as log


def run_update() -> None:
    updater_name = "RegVapor_updater.exe"
    if len(sys.argv) < 2:
        log("Error in updater: Missing target executable argument.")
        return

    target_exe = Path(sys.argv[1])
    new_exe = config.base_dir / "RegVapor_new.exe"

    try:
        urllib.request.urlretrieve(config.GITHUB_EXE_URL, new_exe)
        log("Downloaded new version to {}", new_exe)
    except Exception as e:
        log("Updater failed to download new executable: {}", e)
        return

    time.sleep(2)
    try:
        if target_exe.exists():
            target_exe.unlink()
        shutil.move(str(new_exe), str(target_exe))
        os.startfile(str(target_exe))
    except Exception as e:
        log("Updater failed to replace the executable: {}", e)
        time.sleep(5)

    # Cleanup: delete Updater after execution
    updater_path = sys.argv[0]
    temp_dir = Path(os.environ.get("TEMP", str(config.base_dir)))
    batch_script = temp_dir / "cleanup_updater.bat"

    batch_content = textwrap.dedent(f"""\
        @echo off
        :loop
        :: Check if the process is still running
        tasklist /fi "IMAGENAME eq {updater_name}" | find "{updater_name}" >nul
        if not errorlevel 1 (
            timeout /t 1 /nobreak >nul
            goto :loop
        )
        :: Process is gone, now delete
        del "{updater_path}"
        del "%~f0"
    """)
    batch_script.write_text(batch_content, encoding="utf-8")

    log("Launching cleanup script to delete updater: {}", batch_script)
    subprocess.Popen([str(batch_script)], shell=True)


if __name__ == "__main__":
    log("RegVapor Updater Version {}", config.__version__)
    run_update()

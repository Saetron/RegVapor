import sys
import os
import time
import urllib.request
from pathlib import Path
import subprocess
import shutil
import config
from utils import log_message as log

def run_update():
    if len(sys.argv) < 2:
        log("Error in updater: Missing argument.")
        return
    target_exe = Path(sys.argv[1])
    new_exe = config.base_dir / "RegVapor_new.exe"
    urllib.request.urlretrieve(config.GITHUB_EXE_URL, new_exe)
    log("Downloaded new version to {}", new_exe)
    time.sleep(2)
    try:
        if target_exe.exists():
            target_exe.unlink()
        shutil.move(str(new_exe), str(target_exe))
        os.startfile(str(target_exe))
    except Exception as e:
        log("Updater failed to replace the executable: {}", e)
        time.sleep(5)

    # Cleanup, delete Updater after execution
    updater_path = sys.argv[0]
    batch_script = Path(os.environ["TEMP"]) / "cleanup_updater.bat"

    with open(batch_script, "w") as f:
        f.write(f"""
        @echo off
        :loop
        tasklist /fi "PID eq {os.getpid()}" | find "{os.getpid()}" >nul
        if not errorlevel 1 (
            timeout /t 1 /nobreak >nul
            goto :loop
        )
        del "{updater_path}"
        del "%~f0"
        """)

        log("Launching cleanup script to delete updater: {}", batch_script)
        subprocess.Popen([str(batch_script)], shell=True)
if __name__ == "__main__":
    log("RegVapor Updater Version {}", config.__version__)
    run_update()
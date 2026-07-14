from datetime import datetime
import os
from pathlib import Path
import config

def log_message(regvapor_dir: Path, message: str, *args, max_lines=100):
    formatted_message = message.format(*args) if args else message
    logfile_path = regvapor_dir / LOGFILE
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(logfile_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {formatted_message}\n")
    
    if os.path.exists(logfile_path):
        with open(logfile_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) > max_lines:
            with open(logfile_path, "w", encoding="utf-8") as f:
                f.writelines(lines[-max_lines:])
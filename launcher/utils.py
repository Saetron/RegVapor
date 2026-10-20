from datetime import datetime
import config


def log_message(message: str, *args, max_lines: int = 100) -> None:
    formatted_message = message.format(*args) if args else message
    logfile_path = config.regvapor_dir / config.LOGFILE
    logfile_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_line = f"[{timestamp}] {formatted_message}\n"

    lines: list[str] = []
    if logfile_path.exists():
        try:
            lines = logfile_path.read_text(encoding="utf-8").splitlines(keepends=True)
        except OSError:
            lines = []

    lines.append(new_line)
    logfile_path.write_text("".join(lines[-max_lines:]), encoding="utf-8")

import config
from utils import log_message as log

def backup(base_dir: config.Path, regvapor_dir: config.Path, files_list: list) -> list:
    """Renames specific game files to .bak before launching. Returns a list of renamed pairs."""
    processed_backups = []
    for rel_path in files_list:
        target_file = (base_dir / rel_path).resolve()
        if target_file.exists() and target_file.is_file():
            bak_file = target_file.with_suffix(target_file.suffix + ".bak")
            try:
                if bak_file.exists():
                    bak_file.unlink()
                target_file.rename(bak_file)
                processed_backups.append((target_file, bak_file))
                log("Temporarily backed up: {} -> {}", rel_path, bak_file.name)
            except Exception as e:
                log("Failed to backup file {}: {}", rel_path, e)
    return processed_backups

def restore(backups: list):
    """Restores the original filenames from their .bak counterparts on exit."""
    for original_file, bak_file in backups:
        if bak_file.exists():
            try:
                if original_file.exists():
                    original_file.unlink()
                bak_file.rename(original_file)
                log("Restored file layout: {}", original_file.name)
            except Exception as e:
                log("Failed to restore file {}: {}", bak_file.name, e)